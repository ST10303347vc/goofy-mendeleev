import argparse
import sqlite3
import sys
from threading import Thread

from werkzeug.serving import make_server

from .storage import import_legacy_database


def main():
    parser = argparse.ArgumentParser(description="Run Goofy Mendeleev locally.")
    parser.add_argument("--port", type=int, default=8000, help="Use 0 to select an available port.")
    parser.add_argument("--managed", action="store_true", help="Exit when the parent closes stdin.")
    parser.add_argument("--import-legacy", metavar="PATH", help="Copy a legacy SQLite database and exit.")
    args = parser.parse_args()

    try:
        if args.import_legacy:
            destination = import_legacy_database(args.import_legacy)
            print(f"Imported database to {destination}", file=sys.stderr)
            return 0

        from .main import app
        server = make_server("127.0.0.1", args.port, app, threaded=True)
        if args.managed:
            def stop_when_parent_exits():
                while sys.stdin.buffer.read(8192):
                    pass
                server.shutdown()

            Thread(target=stop_when_parent_exits, daemon=True).start()

        print(f"READY {server.server_port}", flush=True)
        try:
            server.serve_forever()
        finally:
            server.server_close()
        return 0
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"Goofy Mendeleev: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
