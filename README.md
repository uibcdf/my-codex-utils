# my-codex-utils

Utilities to inspect and resume **OpenAI Codex CLI** sessions stored under `~/.codex`.

- `codex-list-sessions`: list sessions associated with the current git repository.
- `codex-resume-last`: resume the most recent session for the current git repository.

## Optional: natural-language summaries

If you set `CODEX_SUMMARIZER_CMD`, the tool will pipe a prompt to that command’s stdin and print its stdout as the summary (cached under `~/.codex/session_summaries/`). Example options:

- Ollama (local, free): install Ollama (`curl -fsSL https://ollama.com/install.sh | sh` or `conda install -c conda-forge ollama`), pull a model (`ollama pull mistral`), then:
  ```bash
  export CODEX_SUMMARIZER_CMD="ollama run mistral"
  codex-list-sessions --lang es   # or --lang en
  ```
- GPT4All (local via pip):
  ```bash
  pip install gpt4all
  export CODEX_SUMMARIZER_CMD="python -m gpt4all.cli run --model mistral-7b-openorca.Q4_0.gguf"
  ```
- Any paid/chat endpoint via `curl`:
  ```bash
  export CODEX_SUMMARIZER_CMD="curl -s https://api.tu-llm.com/chat -H 'Content-Type: application/json' -H 'Authorization: Bearer <TOKEN>' -d @-"
  ```
  Adjust URL/body as required; the prompt arrives on stdin.

Summaries are cached per session ID; delete `~/.codex/session_summaries/<id>.txt` to regenerate.
- Tip: instala el LLM (Ollama, GPT4All, etc.) de forma centralizada en tu usuario/sistema y sólo apunta `CODEX_SUMMARIZER_CMD` desde cualquier entorno conda; así evitas descargar modelos pesados en cada entorno.

See `dev/guide/README.md` for developer-oriented details.
