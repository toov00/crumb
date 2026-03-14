#!/usr/bin/env python3

import argparse
import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(os.environ.get("CRUMB_DIR", Path.home() / ".config" / "crumb"))
DATA_FILE = DATA_DIR / "crumbs.json"

def load() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text())

def save(crumbs: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(crumbs, indent=2))

def next_id(crumbs: list[dict]) -> int:
    return max((c["id"] for c in crumbs), default=0) + 1

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
RED    = "\033[31m"

def supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def c(code: str, text: str) -> str:
    return f"{code}{text}{RESET}" if supports_color() else text

def fmt_tags(tags: list[str]) -> str:
    if not tags:
        return ""
    return "  " + "  ".join(c(CYAN, f"#{t}") for t in tags)

def fmt_date(iso: str) -> str:
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%d %b %Y")

def print_crumb(crumb: dict, highlight: str = "") -> None:
    id_str   = c(DIM, f"[{crumb['id']}]")
    date_str = c(DIM, fmt_date(crumb["created_at"]))
    tags_str = fmt_tags(crumb.get("tags", []))

    content = crumb["content"]
    if highlight:
        pattern = re.compile(re.escape(highlight), re.IGNORECASE)
        content = pattern.sub(lambda m: c(YELLOW + BOLD, m.group()), content)

    desc = crumb.get("description", "")
    desc_line = f"\n   {c(DIM, desc)}" if desc else ""

    print(f" {id_str} {c(BOLD, content)}{desc_line}")
    print(f"   {date_str}{tags_str}\n")

def cmd_add(args) -> None:
    content = " ".join(args.content)
    if not content.strip():
        print(c(RED, "Error: content cannot be empty."))
        sys.exit(1)

    tags = [t.lstrip("#").strip() for t in (args.tag or []) if t.strip()]
    crumbs = load()
    crumb = {
        "id": next_id(crumbs),
        "content": content,
        "description": args.desc or "",
        "tags": tags,
        "created_at": datetime.now().isoformat(),
    }
    crumbs.append(crumb)
    save(crumbs)
    print(c(GREEN, f"Crumb saved! ") + c(DIM, f"(id: {crumb['id']})"))

def cmd_search(args) -> None:
    query = " ".join(args.query).lower()
    crumbs = load()

    results = []
    for crumb in crumbs:
        haystack = " ".join([
            crumb["content"],
            crumb.get("description", ""),
            " ".join(crumb.get("tags", [])),
        ]).lower()
        if query in haystack:
            results.append(crumb)

    if not results:
        print(c(DIM, f'No crumbs found for "{query}".'))
        return

    print(c(BOLD, f"\n  {len(results)} crumb{'s' if len(results) != 1 else ''} found:\n"))
    for crumb in reversed(results):
        print_crumb(crumb, highlight=query)

def cmd_list(args) -> None:
    crumbs = load()

    if args.tag:
        tag = args.tag.lstrip("#")
        crumbs = [c for c in crumbs if tag in c.get("tags", [])]
        if not crumbs:
            print(c(DIM, f"No crumbs tagged #{tag}."))
            return

    if not crumbs:
        print(c(DIM, "No crumbs yet. Try: crumb add \"your command here\""))
        return

    limit = args.n or len(crumbs)
    shown = list(reversed(crumbs))[:limit]

    print(c(BOLD, f"\n  {len(crumbs)} crumb{'s' if len(crumbs) != 1 else ''} total:\n"))
    for crumb in shown:
        print_crumb(crumb)

def cmd_delete(args) -> None:
    crumbs = load()
    original_len = len(crumbs)
    crumbs = [c for c in crumbs if c["id"] != args.id]

    if len(crumbs) == original_len:
        print(c(RED, f"No crumb with id {args.id}."))
        sys.exit(1)

    save(crumbs)
    print(c(GREEN, f"Crumb {args.id} deleted."))

def cmd_copy(args) -> None:
    crumbs = load()
    match = next((c for c in crumbs if c["id"] == args.id), None)
    if not match:
        print(c(RED, f"No crumb with id {args.id}."))
        sys.exit(1)

    content = match["content"]

    import subprocess
    copied = False
    for cmd in ["pbcopy", "xclip -selection clipboard", "clip"]:
        try:
            subprocess.run(cmd.split(), input=content.encode(), check=True, capture_output=True)
            copied = True
            break
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    if copied:
        print(c(GREEN, "Copied to clipboard: ") + c(DIM, content[:60] + ("..." if len(content) > 60 else "")))
    else:
        print(content)

def cmd_tags(args) -> None:
    crumbs = load()
    tag_counts: dict[str, int] = {}
    for crumb in crumbs:
        for tag in crumb.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    if not tag_counts:
        print(c(DIM, "No tags yet."))
        return

    print(c(BOLD, "\n  Tags:\n"))
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        bar = "·" * count
        print(f"  {c(CYAN, '#' + tag):<28} {c(DIM, bar)} {count}")
    print()

def cmd_export(args) -> None:
    crumbs = load()
    if not crumbs:
        print(c(DIM, "Nothing to export."))
        return

    lines = ["# crumb export\n"]
    for crumb in crumbs:
        lines.append(f"## [{crumb['id']}] {fmt_date(crumb['created_at'])}")
        if crumb.get("description"):
            lines.append(f"_{crumb['description']}_")
        lines.append(f"\n```\n{crumb['content']}\n```\n")
        if crumb.get("tags"):
            lines.append("Tags: " + ", ".join(f"#{t}" for t in crumb["tags"]) + "\n")
        lines.append("\n")

    output = "\n".join(lines)
    if args.out:
        Path(args.out).write_text(output)
        print(c(GREEN, f"Exported to {args.out}"))
    else:
        print(output)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crumb",
        description="crumb: leave a trail of useful commands and snippets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  crumb add "docker ps -a" --tag docker
  crumb add "ffmpeg -i in.mp4 -vn out.mp3" --tag ffmpeg,audio --desc "strip audio"
  crumb search docker
  crumb list --tag ffmpeg
  crumb copy 3
  crumb delete 3
  crumb tags
  crumb export --out crumbs.md
        """,
    )
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    p_add = sub.add_parser("add", help="save a new crumb")
    p_add.add_argument("content", nargs="+", help="the command or snippet to save")
    p_add.add_argument("--tag", "-t", nargs="+", metavar="TAG", help="one or more tags")
    p_add.add_argument("--desc", "-d", metavar="TEXT", help="short description")
    p_add.set_defaults(func=cmd_add)

    p_search = sub.add_parser("search", aliases=["s"], help="search crumbs")
    p_search.add_argument("query", nargs="+", help="search term")
    p_search.set_defaults(func=cmd_search)

    p_list = sub.add_parser("list", aliases=["ls"], help="list all crumbs")
    p_list.add_argument("--tag", "-t", metavar="TAG", help="filter by tag")
    p_list.add_argument("-n", type=int, metavar="N", help="show last N crumbs")
    p_list.set_defaults(func=cmd_list)

    p_del = sub.add_parser("delete", aliases=["rm"], help="delete a crumb by id")
    p_del.add_argument("id", type=int, help="crumb id")
    p_del.set_defaults(func=cmd_delete)

    p_copy = sub.add_parser("copy", aliases=["cp"], help="copy crumb content to clipboard")
    p_copy.add_argument("id", type=int, help="crumb id")
    p_copy.set_defaults(func=cmd_copy)

    p_tags = sub.add_parser("tags", help="list all tags with counts")
    p_tags.set_defaults(func=cmd_tags)

    p_exp = sub.add_parser("export", help="export crumbs to markdown")
    p_exp.add_argument("--out", "-o", metavar="FILE", help="output file (default: stdout)")
    p_exp.set_defaults(func=cmd_export)

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
