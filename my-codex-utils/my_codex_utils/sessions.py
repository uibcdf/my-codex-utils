from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CODEX_DIR = Path.home() / ".codex"
SESSIONS_DIR = CODEX_DIR / "sessions"
SUMMARIES_DIR = CODEX_DIR / "session_summaries"


TEXTS: Dict[str, Dict[str, str]] = {
    "es": {
        "no_sessions_dir": "No se encontró ~/.codex/sessions; ¿Codex ha creado alguna sesión?",
        "not_in_repo": "No parece que estés dentro de un repositorio git.",
        "no_sessions_for_repo": "No se encontraron sesiones de Codex asociadas a este repositorio.",
        "header": "Sesiones de Codex para el repo:",
        "branch": "rama",
        "cwd": "cwd",
        "last_user_msg": "último mensaje del usuario",
        "summary": "resumen",
        "resume_cmd": "codex resume",
        "resuming": "Reanudando la última sesión:",
        "resume_none": "No hay sesiones para este repositorio; no se puede reanudar.",
    },
    "en": {
        "no_sessions_dir": "Could not find ~/.codex/sessions; has Codex created any session?",
        "not_in_repo": "It does not look like you are inside a git repository.",
        "no_sessions_for_repo": "No Codex sessions were found for this repository.",
        "header": "Codex sessions for repo:",
        "branch": "branch",
        "cwd": "cwd",
        "last_user_msg": "last user msg",
        "summary": "summary",
        "resume_cmd": "codex resume",
        "resuming": "Resuming last session:",
        "resume_none": "No sessions for this repository; cannot resume.",
    },
}


@dataclass
class CodexSession:
    session_id: str
    created: Optional[str]
    ended: Optional[str]
    cwd: Optional[str]
    repo_url: Optional[str]
    branch: Optional[str]
    last_user_msg: Optional[str]
    file: str
    lines: List[Dict[str, Any]]


def iso_to_local(dt_str: Optional[str]) -> str:
    if not dt_str:
        return "?"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return dt_str or "?"


def get_current_repo_info() -> Tuple[Optional[str], Optional[str]]:
    try:
        remote = (
            subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"],
                text=True,
            )
            .strip()
        )
    except Exception:
        remote = None

    try:
        repo_root = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                text=True,
            )
            .strip()
        )
    except Exception:
        repo_root = None

    return remote or None, repo_root or None


def _load_session_file(path: Path) -> Optional[CodexSession]:
    with path.open("r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f]

    meta = next((e for e in lines if e.get("type") == "session_meta"), None)
    if not meta:
        return None

    payload = meta.get("payload", {})
    session_id = payload.get("id")
    created = payload.get("timestamp")
    cwd = payload.get("cwd")
    gitinfo = payload.get("git", {})
    repo_url = gitinfo.get("repository_url")
    branch = gitinfo.get("branch")

    end_ts = lines[-1].get("timestamp", created)

    last_user_msg = None
    for entry in reversed(lines):
        if entry.get("type") == "event_msg":
            p = entry.get("payload", {})
            if p.get("type") == "user_message":
                last_user_msg = p.get("message")
                break

    if last_user_msg:
        last_user_msg = last_user_msg.replace("\n", " ")
        if len(last_user_msg) > 200:
            last_user_msg = last_user_msg[:197] + "..."

    return CodexSession(
        session_id=session_id,
        created=created,
        ended=end_ts,
        cwd=cwd,
        repo_url=repo_url,
        branch=branch,
        last_user_msg=last_user_msg,
        file=str(path),
        lines=lines,
    )


def build_session_context(lines: List[Dict[str, Any]], max_events: int = 40) -> str:
    events: List[str] = []

    for entry in reversed(lines):
        t = entry.get("type")
        payload = entry.get("payload", {})
        ts = entry.get("timestamp", "")

        if t == "event_msg" and payload.get("type") == "user_message":
            msg = payload.get("message", "")
            events.append(f"[USER @ {ts}] {msg}")
        elif t == "event_msg" and payload.get("type") == "tool_call":
            tool_name = payload.get("tool_name", "tool")
            events.append(f"[TOOL @ {ts}] tool call: {tool_name}")
        elif t == "event_msg" and payload.get("type") == "assistant_message":
            msg = payload.get("message", "")
            if msg:
                msg = msg.replace("\n", " ")
                if len(msg) > 200:
                    msg = msg[:197] + "..."
                events.append(f"[ASSISTANT @ {ts}] {msg}")

        if len(events) >= max_events:
            break

    events.reverse()
    if not events:
        return "No user/assistant events found in this session."
    return "\n".join(events)


def call_free_llm_summarizer(context_text: str, lang: str) -> str:
    cmd = os.environ.get("CODEX_SUMMARIZER_CMD")
    if not cmd:
        return ""

    if lang == "es":
        prompt = (
            "Eres un asistente que resume sesiones de trabajo con un modelo para programar.\n"
            "A partir del siguiente historial de eventos (mensajes del usuario, uso de herramientas, "
            "respuestas del asistente), escribe un resumen en ESPAÑOL de lo que se hizo en la sesión.\n"
            "Requisitos:\n"
            "- Un sólo párrafo de aproximadamente 5–6 líneas.\n"
            "- Tono técnico pero claro.\n"
            "- No repitas literalmente todos los mensajes, sintetiza las ideas.\n\n"
            "=== HISTORIAL ===\n"
            f"{context_text}\n"
            "=== FIN DEL HISTORIAL ===\n\n"
            "Ahora produce el resumen:\n"
        )
    else:
        prompt = (
            "You are an assistant summarizing coding-assistant sessions.\n"
            "From the following history of events (user messages, tool calls, assistant replies), "
            "write a summary in ENGLISH of what was done in the session.\n"
            "Requirements:\n"
            "- A single paragraph of about 5–6 lines.\n"
            "- Technical but clear tone.\n"
            "- Do not repeat every message verbatim; synthesize the key ideas.\n\n"
            "=== HISTORY ===\n"
            f"{context_text}\n"
            "=== END OF HISTORY ===\n\n"
            "Now produce the summary:\n"
        )

    try:
        import shlex

        args = shlex.split(cmd)
        proc = subprocess.run(
            args,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            return ""
        return proc.stdout.strip()
    except Exception:
        return ""


def get_or_create_summary(session: CodexSession, lang: str) -> str:
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = SUMMARIES_DIR / f"{session.session_id}.txt"

    if summary_path.exists():
        return summary_path.read_text(encoding="utf-8").strip()

    context = build_session_context(session.lines)
    summary = call_free_llm_summarizer(context, lang).strip()

    if summary:
        summary_path.write_text(summary, encoding="utf-8")
    return summary


def find_sessions_for_current_repo(lang: str) -> Tuple[Dict[str, str], List[CodexSession]]:
    lang = lang if lang in TEXTS else "en"
    T = TEXTS[lang]

    if not SESSIONS_DIR.exists():
        raise RuntimeError(T["no_sessions_dir"])

    remote_url, repo_root = get_current_repo_info()
    if not remote_url and not repo_root:
        raise RuntimeError(T["not_in_repo"])

    sessions: List[CodexSession] = []
    for root, _, files in os.walk(SESSIONS_DIR):
        for name in files:
            if not name.endswith(".jsonl"):
                continue
            path = Path(root) / name
            s = _load_session_file(path)
            if not s:
                continue

            match = False
            if remote_url and s.repo_url == remote_url:
                match = True
            elif repo_root and s.cwd and s.cwd.startswith(repo_root):
                match = True

            if match:
                sessions.append(s)

    if not sessions:
        raise RuntimeError(T["no_sessions_for_repo"])

    sessions.sort(key=lambda x: x.created or "", reverse=True)
    return T, sessions


def resume_last_session(lang: str = "es") -> None:
    T, sessions = find_sessions_for_current_repo(lang)
    last = sessions[0]
    sid = last.session_id
    created = iso_to_local(last.created)
    ended = iso_to_local(last.ended)

    print(f"{T['resuming']} {created} → {ended}")
    print(f"  {T['resume_cmd']} {sid}")
    print()

    try:
        subprocess.run(["codex", "resume", sid], check=False)
    except FileNotFoundError:
        print("No se encontró el comando 'codex' en el PATH.")


def print_sessions_list(
    lang: str = "es",
    num: Optional[int] = None,
    show_summaries: bool = True,
) -> None:
    T, sessions = find_sessions_for_current_repo(lang)
    lang = lang if lang in TEXTS else "en"

    if num is not None and num > 0:
        sessions = sessions[:num]

    remote_url, repo_root = get_current_repo_info()
    print(f"{T['header']} {remote_url or repo_root}")
    print()

    use_llm = bool(os.environ.get("CODEX_SUMMARIZER_CMD")) if show_summaries else False

    for i, s in enumerate(sessions, start=1):
        created = iso_to_local(s.created)
        ended = iso_to_local(s.ended)
        last_msg = s.last_user_msg or "(no user message)"
        branch = s.branch or "?"
        cwd = s.cwd or "?"

        print(f"[{i}] {created} → {ended}  ({T['branch']}: {branch})")
        print(f"    {T['resume_cmd']} {s.session_id}")
        print(f"    {T['cwd']}: {cwd}")
        print(f"    {T['last_user_msg']}: {last_msg}")

        if use_llm:
            summary = get_or_create_summary(s, lang).strip()
            if summary:
                print(f"    {T['summary']}:")
                for line in summary.splitlines():
                    print(f"      {line}")
        print()
