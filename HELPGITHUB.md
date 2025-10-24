# HELPGITHUB – Guia Rápido de Comandos Git

## Comandos essenciais
- `git status` – mostra o estado do repositório (arquivos modificados, staged, untracked).
- `git add <arquivo>` – adiciona arquivo específico ao staging.
- `git add .` – adiciona todas as mudanças.
- `git commit -m "mensagem"` – cria commit com a mensagem informada.
- `git push origin main` – envia commits locais para o repositório remoto (branch `main`).
- `git pull` – traz alterações do remoto e atualiza a branch local.
- `git log --oneline` – histórico resumido.
- `git diff` – compara alterações não commitadas.
- `git checkout -b nova-branch` – cria e troca para uma nova branch.
- `git checkout branch-existente` – troca de branch.
- `git remote -v` – lista remotes configurados.

## Fluxo típico para este projeto
1. **Atualizar repositório local**
   ```bash
   git pull
   ```
2. **Atualizar servidor a partir do GitHub**
   ```bash
   ssh root@servidor
   cd ~/LaTexAPI
   git pull
   ```
   (Depois refaça `docker build`/`docker stack deploy` conforme abaixo.)
2. **Após modificar arquivos**
   ```bash
   git status
   git add <arquivos ou .>
   git commit -m "Descrição clara das mudanças"
   ```
3. **Enviar ao GitHub**
   ```bash
   git push origin main
   ```
4. **Redeploy da LatexAPI**
   ```bash
   docker build --pull --no-cache -t latexapi:latest .
   export TRAEFIK_ACME_EMAIL="paulo.lucio.ist@gmail.com"
   export LATEXAPI_IMAGE="latexapi:latest"
   docker stack deploy -c deploy/stack.yml latexapi
   ```
5. **Testes rápidos**
   ```bash
   docker exec -it $(docker ps --filter name=latexapi_latexapi -q | head -n 1) kpsewhich portuguese.ldf
   curl https://latexapi.entryprep.com/compile \
        -H "Content-Type: application/json" \
        -d '{"source":"\\documentclass{article}\\begin{document}Olá\\end{document}"}'
   ```

## Dicas
- Sempre verifique `git status` antes de commitar.
- Commits devem ter mensagens claras (ex.: “Add CONTEXTO.md com documentação”).
- Se o `git commit` abrir o editor (`vi`), feche com `Esc :wq`.
- Se esquecer de adicionar algo, use `git commit --amend` (antes de push) para ajustar o último commit.
