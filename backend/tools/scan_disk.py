"""Disk scan — pure runner + LangChain tool for the agent."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from langchain.tools import tool


def _mtime_iso(stat_result: os.stat_result) -> str:
    return datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc).isoformat()

# Skip noisy / inaccessible system dirs
_SKIP_NAMES = {
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".DS_Store",
    "Library",  # huge on macOS home; opt-in via explicit path
}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LAST_SCAN_PATH = DATA_DIR / "last_scan.json"


def _dir_size_bytes(path: Path, max_depth: int, depth: int = 0) -> int:
    total = 0
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.name in _SKIP_NAMES:
                    continue
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_dir(follow_symlinks=False) and depth < max_depth:
                        total += _dir_size_bytes(Path(entry.path), max_depth, depth + 1)
                except (PermissionError, FileNotFoundError, OSError):
                    continue
    except (PermissionError, FileNotFoundError, OSError):
        return 0
    return total


def _scan_node(path: Path, max_depth: int, max_children: int, depth: int = 0) -> dict:
    node: dict = {
        "name": path.name or str(path),
        "path": str(path),
        "type": "directory" if path.is_dir() else "file",
    }

    try:
        node["mtime"] = _mtime_iso(path.stat())
    except OSError:
        node["mtime"] = None

    if path.is_file():
        try:
            node["size_bytes"] = path.stat().st_size
        except OSError:
            node["size_bytes"] = 0
        node["size_gb"] = round(node["size_bytes"] / (1024**3), 3)
        return node

    children: list[dict] = []
    if depth < max_depth:
        try:
            entries = sorted(path.iterdir(), key=lambda p: p.name.lower())
        except (PermissionError, FileNotFoundError, OSError):
            entries = []

        for entry in entries:
            if entry.name in _SKIP_NAMES:
                continue
            try:
                if entry.is_symlink():
                    continue
                if entry.is_file() or entry.is_dir():
                    children.append(_scan_node(entry, max_depth, max_children, depth + 1))
            except (PermissionError, FileNotFoundError, OSError):
                continue

        children.sort(key=lambda c: c.get("size_bytes", 0), reverse=True)
        children = children[:max_children]

    node["children"] = children
    node["size_bytes"] = sum(c.get("size_bytes", 0) for c in children)
    if depth >= max_depth:
        node["size_bytes"] = _dir_size_bytes(path, max_depth=2)

    node["size_gb"] = round(node["size_bytes"] / (1024**3), 3)
    return node


def list_directory_entries(path: str, max_children: int = 200) -> dict:
    """List immediate children of a directory (for the files table)."""
    root = Path(path).expanduser()
    if not root.exists():
        return {"error": f"Path does not exist: {root}"}
    if not root.is_dir():
        return {"error": f"Not a directory: {root}"}

    # Table listing: allow many rows; still cap for safety
    limit = max(1, min(int(max_children), 500))
    # Lighter skips than full scan — user expects to see most of the folder
    skip = {".DS_Store", "__pycache__", ".git", ".svn", ".hg"}
    entries: list[dict] = []

    try:
        scanned = list(os.scandir(root))
    except (PermissionError, FileNotFoundError, OSError) as exc:
        return {"error": str(exc)}

    for entry in scanned:
        if entry.name in skip:
            continue
        try:
            if entry.is_symlink():
                continue
            is_dir = entry.is_dir(follow_symlinks=False)
            is_file = entry.is_file(follow_symlinks=False)
            if not (is_dir or is_file):
                continue
            st = entry.stat(follow_symlinks=False)
            size = (
                _dir_size_bytes(Path(entry.path), max_depth=1)
                if is_dir
                else st.st_size
            )
            entries.append(
                {
                    "name": entry.name,
                    "path": entry.path,
                    "type": "directory" if is_dir else "file",
                    "size_bytes": size,
                    "size_gb": round(size / (1024**3), 3),
                    "mtime": _mtime_iso(st),
                }
            )
        except (PermissionError, FileNotFoundError, OSError):
            continue

    entries.sort(key=lambda e: e.get("size_bytes", 0), reverse=True)
    total = len(entries)
    return {
        "path": str(root),
        "total": total,
        "entries": entries[:limit],
        "truncated": total > limit,
    }


def run_scan_disk(
    path: str = "",
    max_depth: int = 2,
    max_children: int = 12,
    *,
    persist: bool = False,
) -> dict:
    """Run a disk scan and optionally persist the tree as JSON."""
    root = Path(path).expanduser() if path.strip() else Path.home()
    if not root.exists():
        return {"error": f"Path does not exist: {root}"}
    if not root.is_dir():
        return {"error": f"Not a directory: {root}"}

    depth = max(1, min(int(max_depth), 4))
    limit = max(3, min(int(max_children), 30))
    tree = _scan_node(root, max_depth=depth, max_children=limit)
    tree["root"] = str(root)
    tree["capacity_hint_gb"] = None

    if persist:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        LAST_SCAN_PATH.write_text(
            json.dumps(tree, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tree["saved_to"] = str(LAST_SCAN_PATH)

    return tree


@tool
def get_last_scan() -> str:
    """Read the most recent disk analysis already saved by the Clarix app.

    Use this whenever you need real sizes, folders, or file hierarchy data.
    You cannot run a new scan yourself — only the app's Start scan button
    creates/updates this file. If no analysis exists yet, tell the user to
    click Start scan first.
    """
    if not LAST_SCAN_PATH.exists():
        return json.dumps(
            {
                "error": "no_scan",
                "message": (
                    "Nenhuma análise salva. O usuário precisa clicar em "
                    "Start scan no app antes de você ter dados."
                ),
            },
            ensure_ascii=False,
        )
    try:
        return LAST_SCAN_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        return json.dumps(
            {"error": "read_failed", "message": str(exc)},
            ensure_ascii=False,
        )
