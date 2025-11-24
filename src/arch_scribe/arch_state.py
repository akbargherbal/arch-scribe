#!/usr/bin/env python3
import argparse
import sys

# Import from the new locations to maintain backward compatibility
# and serve as the CLI entry point
from .core.constants import (
    STATE_FILE,
    BACKUP_FILE,
    SESSION_FILE,
    IGNORE_DIRS,
    IGNORE_EXTS,
    SIGNIFICANT_SIZE_KB,
    Colors,
    DEFAULT_STATE,
)
from .core.state_manager import StateManager


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("init").add_argument("name")
    sub.add_parser("status")
    sub.add_parser("list")
    sub.add_parser("graph")
    sub.add_parser("validate")
    sub.add_parser("coverage")

    sub.add_parser("session-start")
    sub.add_parser("session-end")

    show = sub.add_parser("show")
    show.add_argument("name")
    show.add_argument("--summary", action="store_true")

    sub.add_parser("add").add_argument("name")

    upd = sub.add_parser("update")
    upd.add_argument("name")
    upd.add_argument("--desc")

    map_cmd = sub.add_parser("map")
    map_cmd.add_argument("name")
    map_cmd.add_argument("files", nargs="+")

    ins = sub.add_parser("insight")
    ins.add_argument("name")
    ins.add_argument("text")

    dep = sub.add_parser("dep")
    dep.add_argument("name")
    dep.add_argument("target")
    dep.add_argument("reason")

    args = parser.parse_args()
    mgr = StateManager()

    if args.cmd == "init":
        mgr.init_project(args.name)
    elif args.cmd == "status":
        mgr.print_status()
    elif args.cmd == "list":
        mgr.list_systems()
    elif args.cmd == "graph":
        mgr.export_graph()
    elif args.cmd == "validate":
        errors = mgr.validate_schema()
        if errors:
            print(f"\n{Colors.FAIL}❌ Validation Errors:{Colors.ENDC}")
            for e in errors:
                print(f"  • {e}")
        else:
            print(
                f"\n{Colors.GREEN}✅ Validation passed. Ready for Phase 2.{Colors.ENDC}"
            )
    elif args.cmd == "coverage":
        mgr.print_coverage_detail()
    elif args.cmd == "session-start":
        mgr.start_session()
    elif args.cmd == "session-end":
        mgr.end_session()
    elif args.cmd == "show":
        mgr.show_system(args.name, args.summary)
    elif args.cmd == "add":
        mgr.add_system(args.name)
    elif args.cmd == "update":
        mgr.update_system(args.name, args.desc)
    elif args.cmd == "map":
        mgr.map_files(args.name, args.files)
    elif args.cmd == "insight":
        mgr.add_insight(args.name, args.text, force=False)
    elif args.cmd == "dep":
        mgr.add_dependency(args.name, args.target, args.reason)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
