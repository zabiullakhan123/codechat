"""Command line entry point.

  python -m codechat.cli index <path-or-github-url>
  python -m codechat.cli chat
  python -m codechat.cli ask "How does authentication work?"
"""
import argparse
import sys

from rich.console import Console

from .ingest import resolve_repo, chunk_repo
from .index import Index

console = Console()


def cmd_index(args):
    root = resolve_repo(args.source)
    chunks = chunk_repo(root)
    if not chunks:
        console.print("[red]No supported files found.[/red]")
        sys.exit(1)
    files = len({c.path for c in chunks})
    console.print(f"Embedding {len(chunks)} chunks from {files} files ...")
    Index.build(chunks).save()
    console.print("[green]Index saved to .codechat_index/[/green]")


def _print_sources(results):
    console.print("\n[dim]Sources:[/dim]")
    for c, s in results[:5]:
        console.print(f"[dim]  {c.path}:{c.start_line}-{c.end_line}  ({s:.2f})[/dim]")


def cmd_ask(args):
    from .chat import ChatSession
    session = ChatSession(Index.load())
    _, results = session.ask(args.question, stream_to=lambda t: print(t, end="", flush=True))
    print()
    _print_sources(results)


def cmd_chat(args):
    from .chat import ChatSession
    session = ChatSession(Index.load())
    console.print("[bold]Chat with your codebase[/bold] (type 'exit' to quit)\n")
    while True:
        try:
            q = console.input("[cyan]you> [/cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"exit", "quit"}:
            break
        if not q:
            continue
        console.print("[magenta]claude>[/magenta] ", end="")
        _, results = session.ask(q, stream_to=lambda t: print(t, end="", flush=True))
        print()
        _print_sources(results)
        print()


def main():
    p = argparse.ArgumentParser(prog="codechat")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("index", help="Index a local folder or GitHub URL")
    s.add_argument("source")
    s.set_defaults(func=cmd_index)
    s = sub.add_parser("ask", help="Ask one question")
    s.add_argument("question")
    s.set_defaults(func=cmd_ask)
    s = sub.add_parser("chat", help="Interactive chat")
    s.set_defaults(func=cmd_chat)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
