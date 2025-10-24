# CONTEXTO DO PROJETO LATEXAPI

## Visão Geral

A LatexAPI é um serviço HTTP escrito em **Python 3.11** utilizando **FastAPI**. O objetivo é receber documentos LaTeX (ou variáveis que permitam gerar LaTeX) e devolver o PDF ou log de compilação. O foco atual é atender fluxos automatizados vindos do **n8n**, mas a API é genérica e pode servir qualquer cliente.

### Estrutura principal
- `app/main.py`: define o endpoint `/compile` e valida as requisições.
- `app/services/compiler.py`: executa a compilação LaTeX com `latexmk/pdflatex`, lida com assets (imagens, anexos) e retorna o resultado.
- `deploy/stack.yml`: stack Docker Swarm com Traefik (reverse proxy) e Portainer opcional.
- `Dockerfile`: constrói a imagem com TeX Live 2024 e os pacotes necessários.

### Fluxo de compilação
1. O cliente envia JSON para `/compile` contendo:
   - `source`: string LaTeX completa.
   - `assets`: lista opcional de arquivos em Base64 que serão gravados e disponibilizados ao LaTeX (`filename` + `content_base64`).  
   - `return_log`: opcional; se `true`, a resposta inclui o log detalhado.
   - `template_name`: opcional; atualmente apenas ecoado, mas reservado para evoluções.
2. A API grava o LaTeX e os assets em diretórios temporários isolados.
3. Executa `latexmk -pdf` (fallback `pdflatex`) com timeout configurável.
4. Retorna um JSON com `pdf_base64`, `elapsed_ms`, `log` (se solicitado).

## TeX Live 2024 + Pacotes

O `Dockerfile` fixa o TeX Live **2024** usando o instalador oficial (`install-tl`) e um conjunto enxuto de pacotes:
- `latexmk`: automatiza os ciclos LaTeX.
- `babel-portuges`: idioma português (o Dockerfile cria alias `portuguese.ldf`).
- `geometry`, `booktabs`, `siunitx`: layout, tabelas e unidades; suportam a maioria dos modelos.
- `pgf`, `xcolor`: gráficos/TikZ e cores.
- `beamer`: apresentações.

O TeX Live 2024 inclui nativamente os módulos AMS (`amsmath`, `amssymb`, etc.), `mathtools`, fontes (`lmodern`) e outros pacotes comuns, por isso não precisamos instalá-los separadamente.

Após instalar os pacotes, o Dockerfile:
- Copia `portuges.ldf` para `portuguese.ldf` em `texmf-local` (garantindo `\usepackage[portuguese]{babel}`).
- Executa `mktexlsr` e `fmtutil-sys --all` para registrar formatos e caches.

## Uso via n8n

### Requisição simples
Endpoints importantes:
- `https://latexapi.entryprep.com`: endpoint principal da API (FastAPI). É aqui que clientes como n8n enviam `POST /compile`.
- `https://traefiklatexapi.entryprep.com`: dashboard do Traefik, protegido por basic auth, mostrando roteadores, middlewares e certificados.
- `https://portainerlatexapi.entryprep.com`: interface opcional do Portainer (usuário `admin` + secret). Permite gerenciar containers/stacks no Swarm.

1. Nó `HTTP Request` (POST para `https://latexapi.entryprep.com/compile`).
2. Headers:
   - `Content-Type: application/json`
3. Body JSON (modo Table/JSON):

```json
{
  "source": "{{ $json.body.latex }}",
  "return_log": true
}
```

### Convertendo o PDF
Após a chamada:
```javascript
// nó Code (Function)
return [{
  binary: {
    pdf: {
      data: $json.pdf_base64,
      mimeType: "application/pdf",
      fileName: "documento.pdf"
    }
  }
}];
```
Ligue a um nó `Write Binary File` ou `Email` para baixar/enviar o PDF.

### Incluindo imagens (assets)
- Pegue a imagem no n8n (HTTP Request binário, Read Binary File etc.).
- Converta para Base64 (se já não estiver).
- Envie no payload:
```json
{
  "source": "\\documentclass{article}\\begin{document}\\includegraphics{images/logo.png}\\end{document}",
  "assets": [
    {
      "filename": "images/logo.png",
      "content_base64": "{{ $json.logoBase64 }}"
    }
  ]
}
```
Use o mesmo caminho em `\includegraphics{...}`.

### Templates no n8n (Mustache/Handlebars/Jinja-like)
- Armazene o `.tex` com placeholders (`{{ aluno.nome }}`, loops, etc.).
- Nó `Code` com `require('mustache')`:
```javascript
const Mustache = require('mustache');
const template = items[0].json.template; // string LaTeX
const context = items[0].json.context;   // dados
const rendered = Mustache.render(template, context);
return [{ json: { source: rendered } }];
```
- O resultado vai para o HTTP Request da LatexAPI.

#### Exemplos:
```tex
\section{Aluno}
{{ aluno.nome }}

{{#disciplinas}}
- {{nome}}: {{nota}}
{{/disciplinas}}
```
Contexto:
```json
{
  "aluno": { "nome": "Ana" },
  "disciplinas": [
    {"nome": "Matemática", "nota": 17},
    {"nome": "Física", "nota": 18}
  ]
}
```

### Templates server-side (futuro)
- `template_name` pode mapear para templates em disco (ex.: `templates/relatorio.tex`).
- Evolução planejada: carregar dados (`context`) e renderizar dentro do serviço usando Jinja2 ou Mustache (Python). Atualmente, apenas registramos o nome.

## Próximos Passos / Roadmap

1. **Autenticação**:
   - Adicionar API Key ou JWT (FastAPI Dependencies).
   - Integrar com Traefik middlewares para rate limiting.

2. **Escala e Resiliência**:
   - Separar workers em fila (Redis + RQ/Celery) para compilações longas.
   - Monitorar tempos de compilação e logs (Prometheus + Grafana; Traefik metrics).
   - Habilitar storage externo (S3/MinIO) se os PDFs precisarem ser armazenados.

3. **Segurança**:
   - Sanitizar entrada LaTeX (bloquear comandos perigosos, shell escape).
   - Rodar cada compilação em sandbox (pod isolado, firejail) para clientes não confiáveis.
   - Revisar assets (limitar tamanho, tipos de arquivo).

4. **Ferramentas extras**:
   - Jinja2/Template engine dentro da API (quando `template_name/context` for implementado).
   - Geração de logs estruturados (JSON) e tracing (OpenTelemetry).
   - Endpoint de status/healthcheck (FastAPI router).

5. **Automação**:
   - Pipeline CI/CD (GitHub Actions) para build e push da imagem.
   - Integração com registries (GHCR) para evitar rebuilds longos.

## Resumo de Comandos Importantes

### Build/Deploy
```bash
docker build --pull --no-cache -t latexapi:latest .
export TRAEFIK_ACME_EMAIL="paulo.lucio.ist@gmail.com"
export LATEXAPI_IMAGE="latexapi:latest"
docker stack deploy -c deploy/stack.yml latexapi
```

### Check TeX Live
```bash
docker exec -it $(docker ps --filter name=latexapi_latexapi -q | head -n 1) \
  kpsewhich portuguese.ldf
```

### Teste rápido
```bash
curl https://latexapi.entryprep.com/compile \
     -H "Content-Type: application/json" \
     -d '{"source":"\\documentclass{article}\\begin{document}Olá\\end{document}","return_log":true}'
```

## Observações Gerais
- A imagem é enxuta mas suficiente para relatórios, gráficos TikZ, beamer e recursos científicos comuns.
- Qualquer pacote extra deve ser adicionado ao bloco `tlmgr install` ou instalado sob demanda.
- Guardar templates em repositório dedicado facilita versionamento e colaboração.
- Ao evoluir para filas/Workers, preserve o contrato da API (`/compile` → `pdf_base64`) e apenas mude a camada interna (queue → worker).

Com este contexto, qualquer nova sessão ou colaborador consegue entender rapidamente o estado atual e dar continuidade ao projeto.
