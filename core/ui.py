import sys
import re
from datetime import datetime

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"


def supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def c(code: str, text: str) -> str:
    return f"{code}{text}{RESET}" if supports_color() else text


def banner(msg: str, visible_len: int) -> str:
    inner = "  🍞  " + msg + "  🍞  "
    inner_len = 10 + visible_len
    w = inner_len + 4
    top = "╭" + "─" * w + "╮"
    bot = "╰" + "─" * w + "╯"
    mid = "│" + " " + inner + " " * (w - inner_len - 2) + "│"
    return f"\n  {top}\n  {mid}\n  {bot}\n"


def saved_banner(crumb_id: int) -> str:
    msg = c(GREEN, "Crumb saved! ") + c(DIM, f"(id: {crumb_id})")
    visible_len = len("Crumb saved! ") + len(f"(id: {crumb_id})")
    return banner(msg, visible_len)


def fmt_tags(tags: list[str]) -> str:
    if not tags:
        return ""
    return "  " + "  ".join(c(CYAN, f"#{t}") for t in tags)


def fmt_date(iso: str) -> str:
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%d %b %Y")


def print_crumb(crumb: dict, highlight: str = "") -> None:
    id_str = c(DIM, f"[{crumb['id']}]")
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
