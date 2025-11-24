from __future__ import annotations

import argparse

from .sessions import resume_last_session


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resume the most recent Codex session associated with the current git repository.",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="es",
        help="Language for informational messages (e.g. es, en). Default: es.",
    )
    args = parser.parse_args()
    resume_last_session(lang=args.lang)
