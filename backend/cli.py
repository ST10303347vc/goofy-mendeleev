"""Local task commands for the same tracker used by the Mac app."""
import argparse
import datetime
import json
import sqlite3
import sys


def main():
    parser = argparse.ArgumentParser(prog="goofy", description=__doc__)
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
    groups = parser.add_subparsers(dest="group", required=True)
    actions = groups.add_parser("tasks").add_subparsers(dest="action", required=True)
    add = actions.add_parser("add", help="Create a task.")
    add.add_argument("title")
    add.add_argument("--notes", default="")
    add.add_argument("--repeat", choices=("daily", "weekly"))
    add.add_argument("--priority", action="store_true")
    listing = actions.add_parser("list", help="List open tasks and their IDs.")
    listing.add_argument("--all", action="store_true", help="Include completed tasks.")
    done = actions.add_parser("done", help="Complete a task by ID.")
    done.add_argument("id", type=int)
    args = parser.parse_args()
    if args.action == "add" and not args.title.strip():
        parser.error("Provide a task title.")

    try:
        from .main import database, daily_database, insert_task, list_tasks, refresh_daily_state, update_task_fields

        if args.action == "list":
            with daily_database() as (conn, _):
                result = [task for task in list_tasks(conn) if args.all or not task["completed"]]
        else:
            with database(write=True) as conn:
                now = datetime.datetime.now()
                refresh_daily_state(conn, now)
                if args.action == "add":
                    result = insert_task(conn, {"title": args.title.strip(), "description": args.notes,
                                                "repeat_interval": args.repeat, "is_priority": args.priority})
                else:
                    result = update_task_fields(conn, args.id, {"completed": True, "progress": 100}, now)
                    if result is None:
                        parser.exit(1, f"Task #{args.id} was not found.\n")
                    for child in result["sub_tasks"]:
                        update_task_fields(conn, child["id"], {"completed": True, "progress": 100}, now)
                    result = update_task_fields(conn, args.id, {}, now)
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        elif args.action == "list":
            for task in result:
                show_task(task)
        else:
            print(f"{'Added' if args.action == 'add' else 'Completed'} #{result['id']} {result['title']}")
        return 0
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"Goofy Mendeleev: {error}", file=sys.stderr)
        return 1


def show_task(task, indent=""):
    markers = ["done" if task["completed"] else "open"]
    if task["repeat_interval"]:
        markers.append(task["repeat_interval"])
    if task["is_priority"]:
        markers.append("priority")
    print(f"{indent}#{task['id']} [{', '.join(markers)}] {task['title']}")
    for child in task["sub_tasks"]:
        show_task(child, indent + "  ")


if __name__ == "__main__":
    raise SystemExit(main())
