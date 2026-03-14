import argparse

from core.commands import (
    cmd_add,
    cmd_clear,
    cmd_copy,
    cmd_delete,
    cmd_export,
    cmd_list,
    cmd_search,
    cmd_tags,
)


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
  crumb clear
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

    p_clear = sub.add_parser("clear", help="remove all crumbs")
    p_clear.set_defaults(func=cmd_clear)

    p_exp = sub.add_parser("export", help="export crumbs to markdown")
    p_exp.add_argument("--out", "-o", metavar="FILE", help="output file (default: stdout)")
    p_exp.set_defaults(func=cmd_export)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
