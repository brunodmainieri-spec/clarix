# Clarix — contexto do repositório

## Objetivo
- Evoluir um protótipo de visualização do uso de disco com assistente Iris; não tratá-lo como produto pronto para produção.
- Responder em português e basear sugestões de limpeza apenas nos dados de uma análise real.

## Arquitetura
- `frontend/` é o aplicativo React/Vite com visualização em Three.js; `src/api/chat.js` e `src/api/scan.js` chamam o backend, por padrão em `127.0.0.1:8000` ou via `VITE_API_URL`.
- `backend/api.py` expõe FastAPI: `/health`, `/scan`, `/scan/entries` e `/chat`.
- `backend/tools/scan_disk.py` lê o sistema de arquivos e persiste a última análise em `backend/data/last_scan.json` quando solicitado pelo endpoint.
- `backend/agent.py` cria a Iris com LangChain/OpenAI; `tools/ui_focus.py` envia ações de foco para o mapa.
- `frontend/src/clarix/` é um segundo projeto Vite/template com manifest próprio; consulte `HOW_TO_USE.md` e não misture seus scripts com os de `frontend/`.
- Consulte os arquivos em `.agents/skills/` quando a tarefa envolver o fluxo correspondente.

## Comandos declarados no projeto
- Em `frontend/`, `npm run dev`, `npm run lint` e `npm run build` são scripts de `package.json`; instale dependências somente com autorização.
- Em `frontend/src/clarix/`, `npm run dev` e `npm run build` são scripts do manifest separado.
- O backend declara Python >=3.12 e dependências em `backend/pyproject.toml`/`uv.lock`; não há script de testes declarado.
- Os comandos acima foram conferidos nos arquivos, não executados; não presuma que o ambiente está pronto.

## Limites e segurança
- Uma varredura pode inspecionar caminhos pessoais e salvar metadados locais: peça confirmação do escopo antes de executá-la; não exponha nomes/caminhos privados nos logs ou respostas.
- Não apague, mova nem modifique arquivos do usuário como parte de uma sugestão de limpeza.
- Não exponha `.env`, `OPENAI_API_KEY` ou respostas brutas de APIs; não execute o chat sem consentimento para consumo de API.
- Preserve o contrato entre frontend e backend e os limites de CORS ao alterar endpoints.

## Verificação
- Confira alterações em ambos os lados do contrato HTTP; após autorização para dependências/execução, rode os scripts pertinentes e teste o fluxo de scan e chat com dados de teste, sem varrer diretórios privados.
- Sem dependências/credenciais ou execução autorizada, limite-se a revisões estáticas e registre explicitamente o que não foi testado.
