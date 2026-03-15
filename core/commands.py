import sys
import subprocess
from datetime import datetime
from pathlib import Path

from core.storage import load, save, next_id
from core.ui import (
    BOLD,
    CYAN,
    DIM,
    GREEN,
    RED,
    banner,
    c,
    fmt_date,
    print_crumb,
    saved_banner,
)


def cmd_add(args) -> None:
    content = " ".join(args.content)
    if not content.strip():
        msg = c(RED, "Error: content cannot be empty.")
        print(banner(msg, len("Error: content cannot be empty.")))
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
    print(saved_banner(crumb["id"]))


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
        msg = c(DIM, f'No crumbs found for "{query}".')
        print(banner(msg, len(f'No crumbs found for "{query}".')))
        return

    header = f"{len(results)} crumb{'s' if len(results) != 1 else ''} found:"
    print(banner(c(BOLD, header), len(header)))
    for crumb in reversed(results):
        print_crumb(crumb, highlight=query)


def cmd_list(args) -> None:
    crumbs = load()

    if args.tag:
        tag = args.tag.lstrip("#")
        crumbs = [item for item in crumbs if tag in item.get("tags", [])]
        if not crumbs:
            msg = c(DIM, f"No crumbs tagged #{tag}.")
            print(banner(msg, len(f"No crumbs tagged #{tag}.")))
            return

    if not crumbs:
        msg = c(DIM, "No crumbs yet. Try: crumb add \"your command here\"")
        print(banner(msg, len("No crumbs yet. Try: crumb add \"your command here\"")))
        return

    limit = args.n or len(crumbs)
    shown = list(reversed(crumbs))[:limit]

    header = f"{len(crumbs)} crumb{'s' if len(crumbs) != 1 else ''} total:"
    print(banner(c(BOLD, header), len(header)))
    for crumb in shown:
        print_crumb(crumb)


def cmd_edit(args) -> None:
    crumbs = load()
    match = next((item for item in crumbs if item["id"] == args.id), None)
    if not match:
        msg = c(RED, f"No crumb with id {args.id}.")
        print(banner(msg, len(f"No crumb with id {args.id}.")))
        sys.exit(1)
    has_content = len(args.content) > 0
    if not (has_content or args.desc is not None or args.tag is not None):
        msg = c(RED, "Provide content, --desc, or --tag to update.")
        print(banner(msg, len("Provide content, --desc, or --tag to update.")))
        sys.exit(1)
    if has_content:
        match["content"] = " ".join(args.content)
    if args.desc is not None:
        match["description"] = args.desc
    if args.tag is not None:
        match["tags"] = [t.lstrip("#").strip() for t in args.tag if t.strip()]
    save(crumbs)
    msg = c(GREEN, f"Crumb {args.id} updated.")
    print(banner(msg, len(f"Crumb {args.id} updated.")))


def cmd_delete(args) -> None:
    crumbs = load()
    original_len = len(crumbs)
    crumbs = [item for item in crumbs if item["id"] != args.id]

    if len(crumbs) == original_len:
        msg = c(RED, f"No crumb with id {args.id}.")
        print(banner(msg, len(f"No crumb with id {args.id}.")))
        sys.exit(1)

    save(crumbs)
    msg = c(GREEN, f"Crumb {args.id} deleted.")
    print(banner(msg, len(f"Crumb {args.id} deleted.")))


def cmd_copy(args) -> None:
    crumbs = load()
    match = next((item for item in crumbs if item["id"] == args.id), None)
    if not match:
        msg = c(RED, f"No crumb with id {args.id}.")
        print(banner(msg, len(f"No crumb with id {args.id}.")))
        sys.exit(1)

    content = match["content"]

    copied = False
    for cmd in ["pbcopy", "xclip -selection clipboard", "clip"]:
        try:
            subprocess.run(cmd.split(), input=content.encode(), check=True, capture_output=True)
            copied = True
            break
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    if copied:
        preview = content[:60] + ("..." if len(content) > 60 else "")
        msg = c(GREEN, "Copied to clipboard: ") + c(DIM, preview)
        visible_len = len("Copied to clipboard: ") + len(preview)
        print(banner(msg, visible_len))
    else:
        print(content)


def cmd_tags(args) -> None:
    crumbs = load()
    tag_counts: dict[str, int] = {}
    for crumb in crumbs:
        for tag in crumb.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    if not tag_counts:
        msg = c(DIM, "No tags yet.")
        print(banner(msg, len("No tags yet.")))
        return

    print(banner(c(BOLD, "Tags:"), len("Tags:")))
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        bar = "·" * count
        print(f"  {c(CYAN, '#' + tag):<28} {c(DIM, bar)} {count}")
    print()


def cmd_export(args) -> None:
    crumbs = load()
    if not crumbs:
        msg = c(DIM, "Nothing to export.")
        print(banner(msg, len("Nothing to export.")))
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
        msg = c(GREEN, f"Exported to {args.out}")
        print(banner(msg, len(f"Exported to {args.out}")))
    else:
        print(output)


def cmd_clear(args) -> None:
    save([])
    msg = c(GREEN, "All crumbs cleared.")
    print(banner(msg, len("All crumbs cleared.")))
