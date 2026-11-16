import datetime
import os
import sqlite3
from contextlib import contextmanager

from flask import Flask, jsonify, request, send_from_directory

if __package__:
    from .hydration import BOTTLE_ML as WATER_BOTTLE_ML, TAP_ML as WATER_STEP_ML, log_water, read_water
    from .quit import clean_day_points, newly_earned_points
    from .storage import ROOT, database_path
    from .training import blocks_for, init_training, record_completion, training_payload
else:
    from hydration import BOTTLE_ML as WATER_BOTTLE_ML, TAP_ML as WATER_STEP_ML, log_water, read_water
    from quit import clean_day_points, newly_earned_points
    from storage import ROOT, database_path
    from training import blocks_for, init_training, record_completion, training_payload

DB_PATH = database_path()

app = Flask(__name__, static_folder=ROOT / "frontend")
app.config["TRUSTED_HOSTS"] = ["127.0.0.1", "localhost", "[::1]"]


@app.before_request
def validate_api_origin():
    if request.path.startswith("/api/"):
        origin = request.headers.get("Origin")
        if origin is not None and origin != request.host_url.rstrip("/"):
            return jsonify({"error": "Open the app directly to use its local API."}), 403
        if request.headers.get("Sec-Fetch-Site") == "cross-site":
            return jsonify({"error": "Open the app directly to use its local API."}), 403


@app.after_request
def disable_api_cache(response):
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def database(*, write=False):
    conn = get_db()
    try:
        with conn:
            conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield conn
    finally:
        conn.close()


def init_db():
    legacy = ROOT / "tracker.db"
    if not os.environ.get("GOOFY_DB_PATH") and not DB_PATH.exists() and legacy.is_file():
        raise ValueError(
            f"Legacy database found at {legacy}. Run python -m backend.server "
            f'--import-legacy "{legacy}" to copy it into {DB_PATH.parent}.'
        )
    DB_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    schema = '''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS daily_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            completed BOOLEAN DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS todo_workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_name TEXT,
            date_added TEXT,
            completed BOOLEAN DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            streak INTEGER DEFAULT 0,
            last_completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS habit_check_ins (
            habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            PRIMARY KEY (habit_id, date)
        );
        CREATE TABLE IF NOT EXISTS daily_reflections (
            date TEXT PRIMARY KEY,
            note TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            parent_id INTEGER,
            completed BOOLEAN DEFAULT 0,
            progress REAL DEFAULT 0.0,
            repeat_interval TEXT,
            last_completed_at TEXT,
            is_priority BOOLEAN DEFAULT 0,
            FOREIGN KEY(parent_id) REFERENCES tasks(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS water_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            count INTEGER DEFAULT 0,
            partial_ml INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS shopping_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            level INTEGER,
            points_required INTEGER,
            progress INTEGER DEFAULT 0,
            completed BOOLEAN DEFAULT 0
        );
    '''
    with database(write=True) as conn:
        for statement in schema.strip().rstrip(";").split(";"):
            conn.execute(statement)
        if "kind" not in {row["name"] for row in conn.execute("PRAGMA table_info(habits)")}:
            conn.execute("ALTER TABLE habits ADD COLUMN kind TEXT NOT NULL DEFAULT 'quit' CHECK (kind IN ('build', 'quit'))")
        init_training(conn, datetime.date.today())
        if "partial_ml" not in {row["name"] for row in conn.execute("PRAGMA table_info(water_log)")}:
            conn.execute("ALTER TABLE water_log ADD COLUMN partial_ml INTEGER NOT NULL DEFAULT 0")


init_db()

def reset_daily_workouts(conn, now):
    """Roll over workout totals and user-created weekday workouts."""
    today = now.date()
    row = conn.execute("SELECT value FROM settings WHERE key = 'daily_workout_date'").fetchone()
    last_day = datetime.date.fromisoformat(row["value"]) if row else None
    if last_day == today:
        return

    if last_day and last_day < today:
        if last_day.isocalendar()[:2] != today.isocalendar()[:2]:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('weekly_workouts', '0')")

        weekdays = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
        workouts = conn.execute("SELECT id, title FROM tasks WHERE parent_id IS NULL").fetchall()
        # Preserve the original carry-over for custom workouts only.
        for offset in range(min((today - last_day).days, 7)):
            prior = last_day + datetime.timedelta(days=offset)
            weekday = weekdays[prior.weekday()]
            for workout in workouts:
                title = (workout["title"] or "").lower()
                if weekday not in title or ("workout" not in title and "gym" not in title):
                    continue
                conn.execute(
                    """INSERT INTO todo_workouts (exercise_name, date_added, completed)
                       SELECT title, ?, 0 FROM tasks WHERE parent_id = ? AND completed = 0""",
                    (prior.isoformat(), workout["id"]),
                )
                conn.execute(
                    """UPDATE tasks SET completed = 0, progress = 0.0, last_completed_at = NULL
                       WHERE id = ? OR parent_id = ?""",
                    (workout["id"], workout["id"]),
                )

    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('daily_workout_date', ?)", (today.isoformat(),))


def list_todo_workouts(conn):
    return [dict(row) for row in conn.execute(
        """SELECT * FROM todo_workouts WHERE completed = 0
           AND lower(trim(exercise_name)) NOT IN ('drink power', 'creatine', 'morning: water with salt')"""
    )]


@app.route("/api/todo_workouts", methods=["GET"])
def read_todo_workouts():
    with daily_database() as (conn, _):
        return jsonify(list_todo_workouts(conn))

@app.route("/api/todo_workouts/<int:todo_id>/complete", methods=["PUT"])
def complete_todo_workout(todo_id):
    with database(write=True) as conn:
        conn.execute("UPDATE todo_workouts SET completed = 1 WHERE id = ?", (todo_id,))
        return jsonify({"success": True})


def read_stats(conn):
    totals = {
        row["key"]: int(row["value"])
        for row in conn.execute(
            "SELECT key, value FROM settings WHERE key IN ('weekly_workouts', 'yearly_workouts', 'task_points')"
        )
    }
    return {
        "weekly_workouts": totals.get("weekly_workouts", 0),
        "yearly_workouts": totals.get("yearly_workouts", 0),
        "task_points": totals.get("task_points", 0),
        "total_water_days": conn.execute("SELECT COUNT(*) FROM water_log WHERE count >= 1").fetchone()[0],
    }

@app.route("/api/stats", methods=["GET"])
def get_stats():
    with daily_database() as (conn, _):
        return jsonify(read_stats(conn))

def increment_workout_counts(conn):
    counts = {}
    for key in ("weekly_workouts", "yearly_workouts"):
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        counts[key] = (int(row["value"]) if row else 0) + 1
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(counts[key])))
    return counts


@app.route("/api/stats/increment_workout", methods=["POST"])
def increment_workout():
    with database(write=True) as conn:
        refresh_daily_state(conn, datetime.datetime.now())
        return jsonify(increment_workout_counts(conn))


@app.route("/api/training/<day>/<slot>/complete", methods=["PUT"])
def complete_training(day, slot):
    with database(write=True) as conn:
        now = datetime.datetime.now()
        today = now.date()
        if day != today.isoformat():
            return jsonify({"error": "This plan has rolled over. Reopen today’s plan."}), 409
        block = next((item for item in blocks_for(conn, today) if item.slot == slot), None)
        if block is None:
            return jsonify({"error": "This item is not in today’s plan."}), 404
        refresh_daily_state(conn, now)
        if record_completion(conn, today, block, now.isoformat()):
            if block.kind == "session":
                increment_workout_counts(conn)
            if block.kind != "recovery":
                row = conn.execute("SELECT value FROM settings WHERE key = 'task_points'").fetchone()
                points = (int(row["value"]) if row else 0) + 1
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('task_points', ?)", (str(points),))
        return jsonify({"training": training_payload(conn, today), "stats": read_stats(conn)})


@app.route("/api/water/drink", methods=["POST"])
def drink_water():
    with database(write=True) as conn:
        return jsonify(log_water(conn, datetime.date.today().isoformat(), WATER_BOTTLE_ML))


@app.route("/api/water/tap", methods=["POST"])
def tap_water():
    with database(write=True) as conn:
        return jsonify(log_water(conn, datetime.date.today().isoformat(), WATER_STEP_ML, stop_at_best=True))

@app.route("/api/water/today", methods=["GET"])
def water_today():
    with database() as conn:
        return jsonify(read_water(conn, datetime.date.today().isoformat()))

def reset_repeating_tasks(conn, now):
    tasks = conn.execute("SELECT id, repeat_interval, last_completed_at FROM tasks WHERE completed = 1 AND repeat_interval IS NOT NULL AND last_completed_at IS NOT NULL").fetchall()
    for task in tasks:
        try:
            last = datetime.datetime.fromisoformat(task['last_completed_at'])
        except Exception:
            continue
            
        reset = False
        if task['repeat_interval'] == 'daily':
            if last.date() < now.date(): 
                reset = True
        elif task['repeat_interval'] == 'weekly':
            if last.date() < now.date() and last.isocalendar()[:2] != now.isocalendar()[:2]:
                reset = True
            
        if reset:
            conn.execute("UPDATE tasks SET completed = 0, progress = 0.0, last_completed_at = NULL WHERE id = ?", (task['id'],))
            conn.execute("UPDATE tasks SET completed = 0, progress = 0.0 WHERE parent_id = ?", (task['id'],))


def list_tasks(conn):
    tasks = {row["id"]: dict(row, sub_tasks=[]) for row in conn.execute("SELECT * FROM tasks")}
    roots = []
    for task in tasks.values():
        if task["parent_id"] is None:
            roots.append(task)
        else:
            parent = tasks.get(task["parent_id"])
            if parent:
                parent["sub_tasks"].append(task)
    return roots


@app.route("/api/tasks", methods=["GET"])
def read_tasks():
    with daily_database() as (conn, _):
        return jsonify(list_tasks(conn))

def insert_task(conn, data):
    result = conn.execute(
        "INSERT INTO tasks (title, description, parent_id, repeat_interval, is_priority) VALUES (?, ?, ?, ?, ?)",
        (data.get("title"), data.get("description"), data.get("parent_id"),
         data.get("repeat_interval"), bool(data.get("is_priority"))),
    )
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (result.lastrowid,)).fetchone()
    return dict(task, sub_tasks=[])


@app.route("/api/tasks", methods=["POST"])
def create_task():
    with database(write=True) as conn:
        return jsonify(insert_task(conn, request.json))


def adjust_task_points(conn, task_id, is_subtask, completing):
    """Award or reverse task points. Single source of truth for scoring logic.
    
    Args:
        completing: True if task is being completed, False if being uncompleted.
    """
    row = conn.execute("SELECT value FROM settings WHERE key = 'task_points'").fetchone()
    val = int(row['value']) if row else 0
    
    if is_subtask:
        delta = 1
    else:
        sub_count = conn.execute("SELECT COUNT(*) as cnt FROM tasks WHERE parent_id = ?", (task_id,)).fetchone()['cnt']
        # Parent with no sub-tasks acts as its own sub-task (+2 total)
        delta = 2 if sub_count == 0 else 1
    
    if completing:
        val += delta
    else:
        val = max(0, val - delta)
    
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('task_points', ?)", (str(val),))

def update_task_fields(conn, task_id, data, now):
    old_task = conn.execute("SELECT completed, parent_id FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if old_task is None:
        return None

    fields, values = [], []
    for key in ("title", "description", "completed", "progress", "repeat_interval", "is_priority"):
        if key not in data:
            continue
        value = data[key]
        if key == "completed":
            value = int(bool(value))
            if value != old_task["completed"]:
                fields.extend(("completed = ?", "last_completed_at = ?"))
                values.extend((value, now.isoformat() if value else None))
                adjust_task_points(conn, task_id, old_task["parent_id"] is not None, completing=bool(value))
        else:
            fields.append(f"{key} = ?")
            values.append(value)
    if fields:
        conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", (*values, task_id))
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    children = conn.execute("SELECT * FROM tasks WHERE parent_id = ?", (task_id,))
    return dict(task, sub_tasks=[dict(child) for child in children])


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    with database(write=True) as conn:
        now = datetime.datetime.now()
        refresh_daily_state(conn, now)
        task = update_task_fields(conn, task_id, request.json, now)
        if task is None:
            return jsonify({"error": "Task not found"}), 404
        return jsonify(task)


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    with database(write=True) as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return jsonify({"success": True})

def auto_complete_habits(conn, today):
    """Credit completed calendar days since the last quit-streak boundary."""
    today_str = today.isoformat()
    habits = conn.execute("SELECT id, streak, last_completed_at FROM habits WHERE kind = 'quit'").fetchall()
    points_to_add = 0
    for habit in habits:
        last_completed = habit['last_completed_at']
        if last_completed and last_completed < today_str:
            last_date = datetime.date.fromisoformat(last_completed)
            days_diff = (today - last_date).days
            previous_streak = habit['streak'] or 0
            streak = previous_streak + days_diff
            points_to_add += newly_earned_points(previous_streak, streak)
            conn.execute("UPDATE habits SET streak = ?, last_completed_at = ? WHERE id = ?", (streak, today_str, habit['id']))
    if points_to_add > 0:
        row_points = conn.execute("SELECT value FROM settings WHERE key = 'task_points'").fetchone()
        val_points = int(row_points['value']) if row_points else 0
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('task_points', ?)", (str(val_points + points_to_add),))


def daily_refresh_needed(conn, now):
    row = conn.execute("SELECT value FROM settings WHERE key = 'daily_refresh_date'").fetchone()
    return row is None or row["value"] != now.date().isoformat()


def refresh_daily_state(conn, now):
    if not daily_refresh_needed(conn, now):
        return
    reset_daily_workouts(conn, now)
    reset_repeating_tasks(conn, now)
    auto_complete_habits(conn, now.date())
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('daily_refresh_date', ?)", (now.date().isoformat(),))


@contextmanager
def daily_database():
    with database() as conn:
        now = datetime.datetime.now()
        if not daily_refresh_needed(conn, now):
            yield conn, now
            return
    with database(write=True) as conn:
        now = datetime.datetime.now()
        refresh_daily_state(conn, now)
        yield conn, now


def habit_payload(conn, row, today):
    habit = dict(row)
    if habit["kind"] == "build":
        entries = conn.execute(
            "SELECT date FROM habit_check_ins WHERE habit_id = ? AND date <= ? ORDER BY date DESC",
            (habit["id"], today.isoformat()),
        )
        latest = next(entries, None)
        checked = bool(latest and latest["date"] == today.isoformat())
        expected = today if checked else today - datetime.timedelta(days=1)
        streak = 0
        while latest and latest["date"] == expected.isoformat():
            streak += 1
            expected -= datetime.timedelta(days=1)
            latest = next(entries, None)
        habit.update(streak=streak, checked_today=checked)
    else:
        boundary = habit["last_completed_at"]
        habit["lapsed_today"] = bool(boundary and boundary > today.isoformat())
        # Text preserves exact point values beyond JavaScript's integer range.
        habit["next_clean_day_points"] = str(clean_day_points(max(0, habit["streak"] or 0) + 1))
    return habit


def list_habits(conn, today):
    return [habit_payload(conn, row, today) for row in conn.execute("SELECT * FROM habits")]


@app.route("/api/habits", methods=["GET"])
def get_habits():
    with daily_database() as (conn, now):
        return jsonify(list_habits(conn, now.date()))


@app.route("/api/habits", methods=["POST"])
def create_habit():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Enter a habit name and choose Build or Quit."}), 400
    title, kind = data.get("title"), data.get("kind", "quit")
    if not isinstance(title, str) or not title.strip() or kind not in ("build", "quit"):
        return jsonify({"error": "Enter a habit name and choose Build or Quit."}), 400
    with database(write=True) as conn:
        today = datetime.date.today()
        result = conn.execute("INSERT INTO habits (title, streak, last_completed_at, kind) VALUES (?, 0, ?, ?)",
                              (title.strip(), today.isoformat() if kind == "quit" else None, kind))
        row = conn.execute("SELECT * FROM habits WHERE id = ?", (result.lastrowid,)).fetchone()
        return jsonify(habit_payload(conn, row, today))


@app.route("/api/habits/<int:habit_id>/check-in", methods=["PUT"])
def check_in_habit(habit_id):
    data = request.get_json(silent=True)
    checked = data.get("checked") if isinstance(data, dict) else None
    if type(checked) is not bool:
        return jsonify({"error": "Check-in state must be true or false."}), 400
    with database(write=True) as conn:
        row = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        if row is None or row["kind"] != "build":
            return jsonify({"error": "Build habit not found."}), 404
        today = datetime.date.today()
        params = (habit_id, today.isoformat())
        if checked:
            conn.execute("INSERT OR IGNORE INTO habit_check_ins (habit_id, date) VALUES (?, ?)", params)
        else:
            conn.execute("DELETE FROM habit_check_ins WHERE habit_id = ? AND date = ?", params)
        return jsonify(habit_payload(conn, row, today))


@app.route("/api/reflection", methods=["GET", "PUT"])
def reflection():
    today = datetime.date.today().isoformat()
    if request.method == "PUT":
        data = request.get_json(silent=True)
        note = data.get("note") if isinstance(data, dict) else None
        if not isinstance(note, str) or len(note) > 2000:
            return jsonify({"error": "Keep the reflection to 2,000 characters."}), 400
        with database(write=True) as conn:
            conn.execute("INSERT INTO daily_reflections VALUES (?, ?) ON CONFLICT(date) DO UPDATE SET note = excluded.note",
                         (today, note.strip()))
            return jsonify({"date": today, "note": note.strip()})
    with database() as conn:
        row = conn.execute("SELECT note FROM daily_reflections WHERE date = ?", (today,)).fetchone()
        return jsonify({"date": today, "note": row["note"] if row else ""})


@app.route("/api/habits/<int:habit_id>", methods=["DELETE"])
def delete_habit(habit_id):
    with database(write=True) as conn:
        conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        return jsonify({"success": True})

@app.route("/api/habits/<int:habit_id>/fumble", methods=["POST", "PUT"])
def fumble_habit(habit_id):
    with database(write=True) as conn:
        now = datetime.datetime.now()
        refresh_daily_state(conn, now)
        habit = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        if not habit or habit["kind"] != "quit":
            return jsonify({"error": "Quit habit not found"}), 404

        # Skip the lapse day. The first new clean day can only end after tomorrow.
        resume_str = (now.date() + datetime.timedelta(days=1)).isoformat()

        conn.execute("UPDATE habits SET streak = 0, last_completed_at = ? WHERE id = ?", (resume_str, habit_id))
        updated_habit = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        return jsonify(habit_payload(conn, updated_habit, now.date()))


@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    with daily_database() as (conn, now):
        return jsonify({
            "tasks": list_tasks(conn),
            "todo_workouts": list_todo_workouts(conn),
            "training": training_payload(conn, now.date()),
            "stats": read_stats(conn),
            "water": read_water(conn, now.date().isoformat()),
            "habits": list_habits(conn, now.date()),
            "shopping_items": list_shopping_items(conn),
        })

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)


def list_shopping_items(conn):
    return [dict(row) for row in conn.execute("SELECT * FROM shopping_items")]


@app.route("/api/shopping", methods=["GET"])
def get_shopping_items():
    with database() as conn:
        return jsonify(list_shopping_items(conn))

@app.route("/api/shopping", methods=["POST"])
def create_shopping_item():
    data = request.json
    name = data.get('name', '')
    level = int(data.get('level', 1))
    points_required = level * 2
    with database(write=True) as conn:
        conn.execute("INSERT INTO shopping_items (name, level, points_required, progress) VALUES (?, ?, ?, 0)",
                     (name, level, points_required))
        return jsonify({"success": True})

@app.route("/api/shopping/<int:item_id>", methods=["DELETE"])
def delete_shopping_item(item_id):
    with database(write=True) as conn:
        conn.execute("DELETE FROM shopping_items WHERE id = ?", (item_id,))
        return jsonify({"success": True})

@app.route("/api/shopping/<int:item_id>/complete", methods=["POST"])
def complete_shopping_item(item_id):
    with database(write=True) as conn:
        item = conn.execute("SELECT points_required, completed FROM shopping_items WHERE id = ?", (item_id,)).fetchone()
        if item and not item['completed']:
            points_cost = item['points_required']
            row_points = conn.execute("SELECT value FROM settings WHERE key = 'task_points'").fetchone()
            val_points = int(row_points['value']) if row_points else 0
            
            if val_points < points_cost:
                return jsonify({"error": "Not enough points", "required": points_cost, "available": val_points}), 400
            
            # Spend points to purchase item
            new_points = val_points - points_cost
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('task_points', ?)", (str(new_points),))
            
            conn.execute("UPDATE shopping_items SET completed = 1 WHERE id = ?", (item_id,))
        
        return jsonify({"success": True})

@app.route("/api/shopping/<int:item_id>/restore", methods=["POST"])
def restore_shopping_item(item_id):
    with database(write=True) as conn:
        item = conn.execute("SELECT points_required, completed FROM shopping_items WHERE id = ?", (item_id,)).fetchone()
        if item and item['completed']:
            points_cost = item['points_required']
            row_points = conn.execute("SELECT value FROM settings WHERE key = 'task_points'").fetchone()
            val_points = int(row_points['value']) if row_points else 0
            
            # Refund points when restoring
            new_points = val_points + points_cost
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('task_points', ?)", (str(new_points),))
            
            conn.execute("UPDATE shopping_items SET completed = 0 WHERE id = ?", (item_id,))
        return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)

