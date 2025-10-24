# LatexAPI – Blueprint Inicial

Este documento resume as ideias discutidas para evoluir a **LatexAPI** para um serviço profissional de conversão e compilação de documentos (LaTeX + outros formatos) com foco em escalabilidade e integração com plataformas como n8n.

## Visão Geral
- **Objetivo**: disponibilizar uma API robusta que converta entradas (LaTeX, HTML, Markdown, Excel, etc.) em PDF/Base64, isolada do n8n e pronta para consumo por múltiplos clientes.
- **Motivação**:
  - Desacoplar compilação de LaTeX do ritmo de release do n8n.
  - Permitir escala independente, hardening, monitorização e autenticação específicas.
  - Servir tanto n8n como outros serviços, mobile ou web.

## Funcionalidades Desejadas
1. **Entrada flexível**:
   - Texto LaTeX (string/base64).
  - HTML/Markdown (convertidos via Pandoc ou equivalente antes da compilação LaTeX).
  - Excel/Word/PPT → PDF (headless LibreOffice ou serviços dedicados).
  - Suporte avançado a gráficos (TikZ, PGFPlots, Graphviz se necessário).
2. **Saída**:
   - PDF (binário ou Base64).
   - Metadados (logs de compilação, tempo gasto, warnings).
3. **Automação & Filas**:
   - Job queue com Redis/Bull (para escalar compilações pesadas).
   - Suporte a reprocessamento/falhas.
4. **Segurança**:
   - Autenticação (API keys, JWT, etc.).
   - Rate limiting / quotas.
   - Sanitização de entrada (prevenir comandos perigosos em LaTeX).
   - Sandbox (containers isolados ou AppArmor/Firejail) opcional.
5. **Observabilidade**:
   - Logging estruturado (request id, input type, outcome).
   - Métricas: tempo de compilação, fila, erros.
   - Alertas (ex.: backlog acima do normal, taxa de falhas).

## Arquitetura (proposta)
- **API Gateway / HTTP Service** (ex.: FastAPI, Express, NestJS):
  - Recebe requests, valida input, autentica.
  - Cria job na fila (Bull/Redis) ou executa diretamente (modo síncrono opcional).
- **Worker(s)**:
  - Containers com TeX Live, Pandoc, LibreOffice (modo headless).
  - Recebem jobs da fila, executam conversão e compilação.
  - Guardam output em storage temporário ou devolvem direto.
- **Storage** (opcional):
  - Resultado pode ser devolvido inline (Base64) ou armazenado (S3, MinIO) para download posterior.
- **Banco de Dados**:
  - Postgres para metadata, rastrear requests e logs persistentes.
  - Redis obrigatório para orquestração de filas (Bull/Celery) e caching.

- **Infra**:
  - Docker Compose/Swarm/Kubernetes.
  - CI/CD: GitHub Actions (build + testes de compilação).
  - Ambiente de staging e produção.

## Integração com n8n
- n8n chama a API via HTTP Request (envia LaTeX/HTML/Excel).
- Recebe PDF/links e prossegue com automação (e-mail, Supabase, etc.).
- Pode manter fallback local (compilação direta) só para casos offline.

## Roadmap Inicial (sugestão)
1. **Definir requisitos detalhados**: formatos suportados, payloads, limites.
2. **Protótipo**:
   - Definir Dockerfile base com TeX Live + Pandoc + LibreOffice.
   - Criar um endpoint `/compile` que recebe LaTeX e devolve PDF Base64.
3. **Adicionar Queue**:
   - Introduzir Redis + Bull, workers separados.
   - Gerir tempos limite, reintentos, prioridade.
4. **Expandir conversões**:
   - Mapear entradas HTML/Markdown → LaTeX → PDF.
   - Integração com conversores de Excel/Word (LibreOffice).
5. **Segurança & Observabilidade**:
   - Autenticação (API keys).
   - Rate limiting (ex.: NGINX, express-rate-limit).
   - Logging (pino, winston), métricas (Prometheus).
6. **Documentação**:
   - Especificação OpenAPI.
   - Exemplo de consumo (cURL, n8n, Node/Python).
   - Guia de deploy (prod/staging).

## Itens a Decidir Futuramente
- Linguagem/framework preferido para a API (Node, Python, Go...).
- Política de updates TeX Live / conversores.
- Estratégia de arquivos temporários (cleanup, quotas).
- Auth (API key simples vs OAuth/JWT).
- Pricing/quota (se exposto a terceiros).
- Gestão de recurso pesado (Xelatex, lualatex, fonts extras).

## Notas Finais
- A LatexAPI ficará como componente central reusable.
- n8n passa a consumir a API em modo fila ou regular.
- Manter o repositório Latex-N8N como referência de fluxo interno, mas o novo projeto foca-se na API.

Este blueprint pode ser usado como base para a sessão de kick-off do projeto. Ajuste conforme decisões futuras.
- **Tecnologia sugerida**
  - **Linguagem**: Python (FastAPI + Celery/RQ) pela robustez, tipagem opcional e excelente ecossistema.
  - Conversões: Pandoc (HTML/Markdown → LaTeX/PDF), LibreOffice headless para formatos Office.

- **Performance e Exigência**
  - Dimensionar workers para carga elevada (profiling de compilações pesadas).
  - Ajustar limites de CPU/memória; considerar isolamento via contêineres por job.
  - Cachear compilações repetidas (opcional) via hash de entrada.
