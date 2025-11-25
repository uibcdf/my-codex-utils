# Developer guide – my-codex-utils

This package provides small utilities to inspect and resume **OpenAI Codex CLI**
sessions stored under `~/.codex`.

## What the tool does

- Reads Codex JSONL session files under `~/.codex/sessions/**.jsonl`.
- Groups sessions by git repository using:
  - `remote.origin.url` (preferred), and
  - the `cwd` recorded for the session.
- For the current git repository, it can:
  - List all matching sessions (most recent first).
  - Show creation and last-activity timestamps.
  - Show the `codex resume <session_id>` command.
  - Show the last user message for context.
  - Optionally call a local/remote LLM (via `CODEX_SUMMARIZER_CMD`) to generate a
    ~5–6 line natural-language summary per session.
  - Resume the most recent session for the current repo via `codex-resume-last`.

## Code structure

- `my_codex_utils/__init__.py`
- `my_codex_utils/sessions.py`
- `my_codex_utils/cli_list_sessions.py`
- `my_codex_utils/cli_resume_last.py`
- `tests/`
