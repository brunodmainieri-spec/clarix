"""UI control tools — Iris can drive the Clarix space map."""

from __future__ import annotations

import json
import threading
from pathlib import Path

from langchain.tools import tool

from tools.scan_disk import LAST_SCAN_PATH

_lock = threading.Lock()
_pending_ui_actions: list[dict] = []


def clear_ui_actions() -> None:
    with _lock:
        _pending_ui_actions.clear()


def drain_ui_actions() -> list[dict]:
    with _lock:
        actions = list(_pending_ui_actions)
        _pending_ui_actions.clear()
        return actions


def _push_ui_action(action: dict) -> None:
    with _lock:
        _pending_ui_actions.append(action)


def _load_last_scan() -> dict | None:
    if not LAST_SCAN_PATH.exists():
        return None
    try:
        return json.loads(LAST_SCAN_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _walk(node: dict):
    yield node
    for child in node.get("children") or []:
        yield from _walk(child)


def _norm(path: str) -> str:
    try:
        return str(Path(path).expanduser().resolve())
    except OSError:
        return str(Path(path).expanduser())


def _find_node(tree: dict, *, path: str = "", name: str = "") -> dict | None:
    path = (path or "").strip()
    name = (name or "").strip()

    if path:
        target = _norm(path)
        for node in _walk(tree):
            node_path = node.get("path")
            if not node_path:
                continue
            if _norm(node_path) == target or node_path == path:
                return node
        # Path may be under scanned root but not expanded in the tree
        root = tree.get("root") or tree.get("path")
        if root and (
            target == _norm(root)
            or target.startswith(_norm(root) + "/")
            or path.startswith(str(root))
        ):
            p = Path(path).expanduser()
            return {
                "name": p.name or str(p),
                "path": str(p),
                "type": "directory" if p.is_dir() else "file",
                "size_bytes": 0,
                "size_gb": 0,
            }

    if name:
        name_l = name.lower()
        matches = [
            n
            for n in _walk(tree)
            if str(n.get("name", "")).lower() == name_l
        ]
        if not matches:
            matches = [
                n
                for n in _walk(tree)
                if name_l in str(n.get("name", "")).lower()
            ]
        if matches:
            # Prefer largest by size_bytes
            matches.sort(key=lambda n: n.get("size_bytes", 0), reverse=True)
            return matches[0]

    return None


@tool
def focus_folder(path: str = "", name: str = "") -> str:
    """Focus the Clarix sunburst / space map on a folder or file.

    Call this when you want the UI to highlight a path while you discuss it
    (e.g. after finding a large folder with get_last_scan). Prefer the
    absolute path from the last scan JSON. If you only know the folder name
    (Downloads, Movies), pass name=.

    Args:
        path: Absolute filesystem path to focus (preferred).
        name: Folder/file name to fuzzy-match in the last scan (fallback).
    """
    tree = _load_last_scan()
    if tree is None:
        return json.dumps(
            {
                "ok": False,
                "error": "no_scan",
                "message": (
                    "Nenhuma análise salva. Peça ao usuário para clicar em "
                    "Start scan."
                ),
            },
            ensure_ascii=False,
        )

    if not path.strip() and not name.strip():
        return json.dumps(
            {
                "ok": False,
                "error": "missing_target",
                "message": "Informe path ou name para focar no mapa.",
            },
            ensure_ascii=False,
        )

    node = _find_node(tree, path=path, name=name)
    if node is None:
        return json.dumps(
            {
                "ok": False,
                "error": "not_found",
                "message": (
                    f"Não encontrei '{path or name}' na última análise. "
                    "Use um path/nome que apareça em get_last_scan."
                ),
            },
            ensure_ascii=False,
        )

    action = {
        "type": "select_path",
        "path": node.get("path"),
        "name": node.get("name"),
        "size_gb": node.get("size_gb"),
        "node_type": node.get("type"),
    }
    _push_ui_action(action)

    return json.dumps(
        {
            "ok": True,
            "message": (
                f"Mapa focado em {node.get('name')} "
                f"({node.get('size_gb', '?')} GB)."
            ),
            "focused": action,
        },
        ensure_ascii=False,
    )
