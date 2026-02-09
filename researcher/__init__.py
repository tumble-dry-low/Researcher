"""Researcher — Multi-agent research orchestration system."""
import os
from pathlib import Path

from .core import KnowledgeBase

DEFAULT_DB_DIR = Path.home() / ".researcher"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "kb.db"


def get_db_path():
    """Resolve DB path: KB_DB env var > local knowledge-base/kb.db > ~/.researcher/kb.db"""
    # Explicit env var
    if env := os.environ.get("KB_DB"):
        p = Path(env)
        p.parent.mkdir(parents=True, exist_ok=True)
        return str(p)

    # Local project DB (if knowledge-base/ exists in cwd)
    local = Path("knowledge-base/kb.db")
    if local.parent.exists():
        return str(local)

    # Global default
    DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
    return str(DEFAULT_DB_PATH)


__all__ = ["KnowledgeBase", "get_db_path"]
