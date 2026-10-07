"""FastAPI app — bridge between Clarix frontend and the ReAct agent."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent import create_clarix_agent
from tools.scan_disk import LAST_SCAN_PATH, list_directory_entries, run_scan_disk
from tools.ui_focus import clear_ui_actions, drain_ui_actions

app = FastAPI(title="Clarix API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# One agent + checkpointer for the process (short-term memory by thread_id)
_agent = create_clarix_agent()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    thread_id: str | None = None


class UiAction(BaseModel):
    type: str
    path: str | None = None
    name: str | None = None
    size_gb: float | None = None
    node_type: str | None = None


class ChatResponse(BaseModel):
    thread_id: str
    reply: str
    ui_actions: list[UiAction] = Field(default_factory=list)


class ScanRequest(BaseModel):
    path: str = ""
    max_depth: int = 2
    max_children: int = 12


def _message_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def _last_ai_reply(messages: list) -> str:
    for msg in reversed(messages):
        role = getattr(msg, "type", None) or msg.__class__.__name__
        if role in {"ai", "AIMessage"}:
            text = _message_text(getattr(msg, "content", "")).strip()
            if text:
                return text
    return ""


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/scan")
def scan(body: ScanRequest | None = None):
    """Run disk scan via the scan tool logic, persist JSON, return the tree."""
    req = body or ScanRequest()
    try:
        tree = run_scan_disk(
            path=req.path,
            max_depth=req.max_depth,
            max_children=req.max_children,
            persist=True,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if "error" in tree:
        raise HTTPException(status_code=400, detail=tree["error"])

    return {
        "ok": True,
        "saved_to": str(LAST_SCAN_PATH),
        "disk_tree": tree,
    }


@app.get("/scan/entries")
def scan_entries(path: str, max_children: int = 200):
    """List files/folders inside a path for the files table."""
    if not path or not path.strip():
        raise HTTPException(status_code=400, detail="path is required")
    try:
        result = list_directory_entries(path, max_children=max_children)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"ok": True, **result}


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    thread_id = body.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    clear_ui_actions()
    try:
        result = _agent.invoke(
            {"messages": [{"role": "user", "content": body.message}]},
            config=config,
        )
    except Exception as exc:  # noqa: BLE001 — surface to client for demos
        clear_ui_actions()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    reply = _last_ai_reply(result.get("messages", []))
    if not reply:
        reply = "Não consegui gerar uma resposta agora. Tente de novo."

    ui_actions = drain_ui_actions()
    return ChatResponse(
        thread_id=thread_id,
        reply=reply,
        ui_actions=ui_actions,
    )
