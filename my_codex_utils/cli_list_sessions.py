from __future__ import annotations

import argparse

from .sessions import print_sessions_list


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List Codex sessions associated with the current git repository.",
    )
    parser.add_argument(
        "-n",
        "--num",
        type=int,
        default=None,
        help="Maximum number of sessions to show (most recent first).",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="es",
        help="Language for output and summaries (e.g. es, en). Default: es.",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Do not call the external summarizer; omit natural-language summaries.",
    )
    args = parser.parse_args()

    show_summaries = not args.no_summary
    print_sessions_list(
        lang=args.lang,
        num=args.num,
        show_summaries=show_summaries,
    )
