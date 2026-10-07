"""Clarix ReAct agent — LangChain create_agent + disk tools + short-term memory."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from tools.scan_disk import get_last_scan
from tools.ui_focus import focus_folder

# Project root .env (../.env relative to backend/)
_ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ROOT_ENV)

# Latest cheap OpenAI model (Luna). reasoning_effort=none required for tools
# on /v1/chat/completions.
MODEL_NAME = os.getenv("CLARIX_MODEL", "gpt-5.6-luna")

SYSTEM_PROMPT = """\
Você é a Iris, agente de limpeza e performance do app Clarix (estilo CleanMyMac).

Seu papel:
- Ajudar o usuário a entender o uso de disco, encontrar pastas/arquivos grandes
  e sugerir otimizações (cache, downloads, lixo, duplicatas conceituais).
- Responder em português do Brasil, de forma clara e objetiva.
- Quando tiver dados de análise, resuma os maiores vilões e pergunte o
  próximo passo (ex.: analisar Downloads, Movies, etc.).

Dados de disco:
- Você NÃO consegue escanear o computador. Quem gera a análise é o botão
  Start scan do app (frontend).
- Sua única fonte de dados reais é a ferramenta get_last_scan, que lê a
  última análise já salva.
- Só consegue acessar análises já feitas. Se get_last_scan disser que não
  há scan, peça ao usuário para clicar em Start scan e tentar de novo.
- Não invente tamanhos nem invente pastas que não aparecem no JSON.

Controle do mapa (sunburst):
- Use focus_folder para destacar no app a pasta/arquivo sobre o qual você
  está falando. Isso cria o efeito de você controlando a interface.
- Prefira o path absoluto do JSON. Se só souber o nome (ex.: Movies),
  passe name=.
- Sempre que apontar um vilão concreto de espaço, chame focus_folder nele
  antes ou junto da explicação.

Formato das respostas:
- Texto limpo e natural, pronto para um chat de app.
- NÃO use Markdown: sem **, *, #, listas com -, backticks, links ou código.
- Evite emojis e símbolos decorativos.
- Prefira frases curtas e parágrafos simples.

Regras:
- Não invente números: se precisar de dados, chame get_last_scan.
- Não apague nada sozinha — só analise e recomende.
"""


def create_clarix_agent(*, checkpointer: InMemorySaver | None = None):
    """Build the ReAct agent that will later power the FastAPI backend."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY não encontrada. Defina no .env na raiz do projeto."
        )

    model = ChatOpenAI(
        model=MODEL_NAME,
        reasoning_effort="none",
    )

    return create_agent(
        model=model,
        tools=[get_last_scan, focus_folder],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer or InMemorySaver(),
    )
