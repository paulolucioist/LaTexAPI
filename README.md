# LatexAPI (MVP)

API enxuta para receber fonte LaTeX e devolver PDF em Base64. O objetivo é servir de base estável para evoluir futuramente para filas e workloads maiores sem reescrever o núcleo.

## Visão rápida
- **Stack**: Python 3.10+, FastAPI, Uvicorn.
- **Compilação**: executa `latexmk` (`pdflatex` como fallback). Falha caso nenhuma ferramenta esteja instalada.
- **Endpoint**: `POST /compile` recebendo LaTeX puro e devolvendo PDF Base64 com tempo de execução e log opcional.

## Configuração
1. Instale dependências:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```
2. Garanta que `latexmk` ou `pdflatex` esteja disponível no PATH (ex.: TeX Live) e que os pacotes necessários para o seu LaTeX estejam instalados (imagem base inclui `texlive-lang-portuguese` e `texlive-lang-other`).
3. Execute localmente:
   ```bash
   uvicorn app.main:app --reload
   ```

## Exemplo de uso
```bash
curl -X POST http://localhost:8000/compile \
  -H "Content-Type: application/json" \
  -d '{
        "source": "\\\\documentclass{article}\\\\begin{document}Hello LatexAPI\\\\end{document}",
        "return_log": true,
        "assets": [
          {
            "filename": "images/logo.png",
            "content_base64": "<BASE64_DA_IMAGEM>"
          }
        ]
      }'
```
Resposta típica:
   ```json
   {
     "pdf_base64": "<...>",
     "elapsed_ms": 732,
     "log": "..."
   }
   ```

## Deploy em Debian 12 (Hetzner)
1. Provisionar servidor com Docker e plugin Compose:
   ```bash
   sudo apt-get update
   sudo apt-get install -y ca-certificates curl gnupg
   sudo install -m 0755 -d /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
   echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
     $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt-get update
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   sudo usermod -aG docker $USER
   ```
   (faça logoff/logon após adicionar o usuário ao grupo `docker`).
2. Clone o projeto e construa a imagem:
   ```bash
   git clone https://seu-repo.git latexapi
   cd latexapi
   docker compose build
   ```
3. Execute:
   ```bash
   docker compose up -d
   ```
4. A API ficará disponível em `http://<IP_DO_SERVIDOR>:8000`. Para ajustar portas, edite `docker-compose.yml`.

### Considerações operacionais
- O Dockerfile instala um conjunto mínimo de pacotes LaTeX (`texlive-latex-extra`, `latexmk`). Adicione pacotes específicos no Dockerfile se seus templates exigirem.
- Utilize volumes externos se quiser persistir logs ou armazenar artefatos. Por padrão, tudo fica no container.
- Configure firewall/NGINX na Hetzner para expor a API com TLS e rate limiting.

## Deploy com Docker Swarm + Traefik
1. Inicialize o Swarm no manager:
   ```bash
   docker swarm init
   ```
2. Defina variáveis de ambiente necessárias (exemplo com bash):
   ```bash
   export TRAEFIK_ACME_EMAIL="paulo.lucio.ist@gmail.com"
   export LATEXAPI_IMAGE="registry/latexapi:latest"
   ```
3. Gere o hash htpasswd e crie o secret (executar no manager):
   ```bash
   htpasswd -nb admin 'senha-segura' | docker secret create traefik_dashboard_users -
   ```
4. (Opcional) Defina senha do usuário admin do Portainer via secret:
   ```bash
   htpasswd -nB admin 'senha-portainer' | cut -d: -f2 | \
     docker secret create portainer_admin_password -
   ```
3. Envie a stack:
   ```bash
   docker stack deploy -c deploy/stack.yml latexapi
   ```
4. Traefik cuidará do HTTPS (LetsEncrypt) e roteamento. A API será acessível em `https://latexapi.entryprep.com`.

### Portainer (opcional)
- O stack inclui Portainer CE como interface gráfica. Caso não queira, remova o serviço `portainer` do `deploy/stack.yml`.
- Acesse via `https://portainerlatexapi.entryprep.com` (traefik aplicará TLS). Configure usuários adicionais dentro do Portainer.
- Para pular a tela inicial de criação de usuário, gere o secret `portainer_admin_password` conforme o passo anterior; o login será `admin` com a senha escolhida.

### Dados ainda necessários
- **LATEXAPI_IMAGE**: referência da imagem publicada no registro (ex.: `ghcr.io/seu-usuario/latexapi:0.1.0`).
- **DNS**: crie registros A/AAAA para `latexapi.entryprep.com`, `traefiklatexapi.entryprep.com` e `portainerlatexapi.entryprep.com` apontando para o IP do nó manager.
- **Secrets opcionais**: tokens/API keys que a API venha a exigir futuramente devem ser injetados via variáveis ou secrets específicos.

## Assets e Templates
- Use o campo `assets` para enviar imagens ou outros anexos necessários à compilação (`filename` + conteúdo em Base64). O serviço grava cada arquivo em um diretório temporário e impede path traversal.
- Recursos podem ser referenciados no LaTeX normalmente (`\includegraphics{images/logo.png}`), bastando alinhar o caminho com o nome enviado.
- O campo opcional `template_name` permite indicar ao serviço qual template pré-configurado deve ser aplicado antes da compilação. A implementação padrão apenas ecoa o valor, mas você pode acoplar um motor de templates (Jinja2, Mustache) ou montar o documento final selecionando arquivos estáticos no servidor.
- Boas práticas para templates:
  - Mantenha um repositório versionado de modelos (`templates/base_invoice.tex`, etc.).
  - Padronize variáveis de contexto e valide dados antes de renderizar.
  - Faça caching dos modelos carregados para evitar IO repetitivo.

## Evolução planejada
- Introduzir fila (Redis + RQ/Celery) mantendo o contrato do endpoint.
- Persistência opcional (Postgres) para auditoria, billing e histórico.
- Conversões adicionais (HTML/Markdown, Office) usando conversores dedicados.
