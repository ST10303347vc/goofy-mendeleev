"""Dated training plan, separate from general tasks and workout carry-over."""
import datetime
import json
from dataclasses import asdict, dataclass


PLAN_VERSION = 5
MOVEMENT_PROGRESSION_VERSION = 4
MOVEMENT_DAYS_PER_LEVEL = 5


@dataclass(frozen=True)
class Block:
    slot: str
    title: str
    kind: str
    steps: tuple[str, ...] = ()
    muscle_groups: tuple[str, ...] = ()
    optional: bool = False


MORNING = Block("morning-water", "Morning: Water with salt", "reminder")
CREATINE = Block("creatine", "Creatine", "reminder")
BOXING_FITNESS = Block("boxing", "Boxing · Full fitness", "session", (
    "Complete your full boxing fitness session.",
))
BOXING_TECHNIQUE = Block("boxing", "Boxing · Technique", "session", (
    "Technique work with lighter fitness.",
))
BOXING_SPARRING = Block("boxing", "Boxing · Sparring", "session", (
    "Sparring with lighter fitness.",
))
LIFTING_WARMUP = "Warm up with easy movement and lighter sets before the first lifts."
LIFTING_PROGRESSION = (
    "On weighted exercises, finish each set with about two reps left. Rest about two minutes between sets on the bigger lifts.",
    "When you reach the top of the rep range on every weighted set with good form, add the smallest weight increase next time.",
)
STRENGTH_A = Block("strength-a", "Muscle gain A · Squat and hinge", "session", (
    LIFTING_WARMUP,
    "Start with two work sets per exercise if you’re new to lifting or still tired from Monday’s fitness.",
    "Goblet squat: 3 sets of 8–12",
    "Dumbbell Romanian deadlift: 3 sets of 8–12",
    "Dumbbell bench press: 3 sets of 8–12",
    "Chest-supported dumbbell row: 3 sets of 8–12",
    "Standing calf raise: 2 sets of 12–20",
    "Dumbbell lateral raise: 2 sets of 12–15",
    "Dumbbell biceps curl: 2 sets of 10–15",
    *LIFTING_PROGRESSION,
), ("quads", "glutes", "hamstrings", "calves", "chest", "back", "shoulders", "biceps"))
STRENGTH_B = Block("strength-b", "Muscle gain B · Leg press and single-leg work", "session", (
    LIFTING_WARMUP,
    "Start with two work sets per exercise if you’re new to lifting or still tired from Friday’s sparring.",
    "Leg press: 3 sets of 8–12",
    "Dumbbell split squat: 2 sets of 8–12 per side",
    "Seated leg curl: 3 sets of 10–15",
    "Incline dumbbell press: 3 sets of 8–12",
    "Lat pulldown: 3 sets of 8–12",
    "Cable triceps pressdown: 2 sets of 10–15",
    "Standing calf raise: 3 sets of 12–20",
    "Plank: 2 holds of 20–40 seconds",
    *LIFTING_PROGRESSION,
), ("quads", "glutes", "chest", "back", "hamstrings", "triceps", "calves", "core"))
LEGS = Block("legs-extra", "Muscle gain · Short leg session", "session", (
    LIFTING_WARMUP,
    "Leg extension: 2 sets of 12–15",
    "Seated leg curl: 2 sets of 12–15",
    "Standing calf raise: 2 sets of 12–20",
    "Leave about three reps in reserve. Start with one set each if you’re adding this day for the first time.",
    "If your legs are heavy or Friday sparring is a priority, take an easy walk or rest instead. Log this session only if you lift.",
), ("quads", "hamstrings", "calves"), optional=True)
RECOVERY = Block("recovery", "Recovery day", "recovery", (
    "Rest, walk easily, or spend a few minutes on comfortable mobility.",
), optional=True)
SESSIONS = (BOXING_FITNESS, STRENGTH_A, BOXING_TECHNIQUE, LEGS, BOXING_SPARRING, STRENGTH_B, RECOVERY)

MOVEMENT_TARGETS = (
    "Choose one: 5 easy bodyweight squats, 5 easy push-ups, or a 15-second plank.",
    "Choose one: 6–8 easy bodyweight squats, 6–8 easy push-ups, or a 20-second plank.",
    "Choose one: 8–10 easy bodyweight squats, 8–10 easy push-ups, or a 25–30 second plank.",
)


def movement_for(conn, day, *, boxing_day):
    # Keep the same target all day, including after today's check-off.
    completed_days = conn.execute(
        "SELECT COUNT(*) FROM training_completions WHERE slot = ? AND plan_version >= ? AND day < ?",
        ("movement", MOVEMENT_PROGRESSION_VERSION, day.isoformat()),
    ).fetchone()[0]
    level_index = min(completed_days // MOVEMENT_DAYS_PER_LEVEL, len(MOVEMENT_TARGETS) - 1)
    level = level_index + 1
    target = MOVEMENT_TARGETS[level_index]
    if boxing_day:
        target = "Choose one for your warm-up: 1 minute of easy rope, 5 easy bodyweight squats, or a 15-second plank."
    progress = "Keep this level as long as it feels easy."
    if level < len(MOVEMENT_TARGETS):
        threshold = level * MOVEMENT_DAYS_PER_LEVEL
        progress = f"Level {level + 1} starts after {threshold} days checked off on this routine."
    return Block("movement", f"Light daily movement · Level {level}", "movement", (
        target,
        "An easier version counts. Skip this if you’ve already trained or need more recovery.",
        progress,
    ), optional=True)


def blocks_for(conn, day):
    session = SESSIONS[day.weekday()]
    if session is RECOVERY:
        return MORNING, session, CREATINE
    movement = movement_for(conn, day, boxing_day=session.slot == "boxing")
    return MORNING, movement, session, CREATINE


def init_training(conn, today):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS training_completions (
            day TEXT NOT NULL,
            slot TEXT NOT NULL,
            title TEXT NOT NULL,
            kind TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            plan_version INTEGER NOT NULL,
            planned_details TEXT NOT NULL,
            PRIMARY KEY (day, slot)
        )
    """)
    legacy = conn.execute(
        "SELECT id FROM tasks WHERE title = ? AND parent_id IS NULL ORDER BY id LIMIT 1",
        (f"Daily Protocol {today.isoformat()}",),
    ).fetchone()
    if legacy is None:
        return
    items = conn.execute(
        "SELECT title, completed, last_completed_at FROM tasks WHERE parent_id = ? ORDER BY id",
        (legacy["id"],),
    ).fetchall()
    creatine = [item for item in items if (item["title"] or "").strip().casefold() == "drink power"]
    exercise = [item for item in items if item not in creatine]
    for block in blocks_for(conn, today):
        if block.slot == "creatine":
            completed = next((item for item in creatine if item["completed"]), None)
        elif block.slot == "movement" and exercise and all(item["completed"] for item in exercise):
            completed = exercise[-1]
        else:
            completed = None
        if completed is not None:
            record_completion(conn, today, block, completed["last_completed_at"] or today.isoformat(), legacy=True)


def record_completion(conn, day, block, completed_at, *, legacy=False):
    details = {"source": "legacy"} if legacy else {"steps": block.steps, "muscle_groups": block.muscle_groups}
    version = 1 if legacy else PLAN_VERSION
    result = conn.execute(
        """INSERT OR IGNORE INTO training_completions
           (day, slot, title, kind, completed_at, plan_version, planned_details) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (day.isoformat(), block.slot, block.title, block.kind, completed_at, version, json.dumps(details)),
    )
    return result.rowcount == 1


def training_payload(conn, day):
    completed_slots = {
        row["slot"] for row in conn.execute("SELECT slot FROM training_completions WHERE day = ?", (day.isoformat(),))
    }
    return {
        "day": day.isoformat(),
        "today": [dict(asdict(block), completed=block.slot in completed_slots) for block in blocks_for(conn, day)],
        "tomorrow": asdict(SESSIONS[(day + datetime.timedelta(days=1)).weekday()]),
    }
