# Installation

## Requirements

- Python 3.7+
- SQLite (built-in)
- Optional: `sqlite-vec` for vector search (falls back to FTS5 gracefully)

## Install

```bash
git clone <repo-url> && cd Researcher
pip install -e .
```

This installs the `kb` command globally.

```bash
kb help    # verify
```

## Use in Any Project

```bash
cd /path/to/your/project
kb init
```

This creates:
- `knowledge-base/kb.db` — local SQLite research database
- `.copilot-instructions.md` — agent instructions for copilot-cli sessions

Any new copilot-cli session in that project will automatically discover the research agent.

## DB Resolution

The `kb` command finds its database in this order:

1. **`KB_DB` env var** — explicit path: `KB_DB=/data/research.db kb stats`
2. **Local `knowledge-base/kb.db`** — if a `knowledge-base/` directory exists in the current working directory
3. **Global `~/.researcher/kb.db`** — default fallback

## Verify

```bash
kb stats                        # show DB contents
kb search "any topic"           # search existing research
kb add "Test" "content"         # create an entity
kb help                         # full command reference
```

## Uninstall

```bash
pip uninstall researcher-kb
```

Research data stays in `knowledge-base/kb.db` (per-project) or `~/.researcher/kb.db` (global).
