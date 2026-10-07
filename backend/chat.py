#!/usr/bin/env python3
"""Terminal REPL to test the Clarix ReAct agent before FastAPI."""

from __future__ import annotations

import sys
import uuid

from agent import MODEL_NAME, create_clarix_agent


def _print_last_ai(messages) -> None:
    for msg in reversed(messages):
        role = getattr(msg, "type", None) or msg.__class__.__name__
        if role in {"ai", "AIMessage"}:
            content = msg.content
            if isinstance(content, list):
                text = "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                )
            else:
                text = str(content)
            print(f"\nIris: {text}\n")
            return
    print("\n(Iris não retornou texto)\n")


def main() -> int:
    print(f"Clarix agent  ·  modelo: {MODEL_NAME}")
    print("Digite sua mensagem. Comandos: /sair  /novo (nova memória)\n")

    agent = create_clarix_agent()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        try:
            user = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo.")
            return 0

        if not user:
            continue
        if user.lower() in {"/sair", "/exit", "sair", "exit", "quit"}:
            print("Até logo.")
            return 0
        if user.lower() in {"/novo", "/new"}:
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            print("(nova conversa — memória resetada)\n")
            continue

        result = agent.invoke(
            {"messages": [{"role": "user", "content": user}]},
            config=config,
        )
        _print_last_ai(result.get("messages", []))

    return 0


if __name__ == "__main__":
    sys.exit(main())
