#!/usr/bin/env python3
"""Add weekly workout tasks to goofy-mendeleev via the live Flask API."""
import json
import urllib.request

BASE = "http://localhost:8000"

WORKOUTS = [
    {
        "title": "Monday Workout",
        "repeat_interval": "weekly",
        "sub_tasks": [
            "Bulgarian Split Squats 5x5/leg",
            "Romanian Deadlift 4x8-10",
            "Single-Leg Calf Raises 4x15/leg",
            "Weighted Pull-Ups 3x5",
        ],
    },
    {
        "title": "Tuesday workout",
        "repeat_interval": "weekly",
        "sub_tasks": [
            "Barbell Bench Press 5x5",
            "Bent-Over Barbell Row 4x8",
            "Walking Lunges 3x20 steps",
            "Face Pulls 3x15-20",
        ],
    },
    {
        "title": "Wednesday workout",
        "repeat_interval": "weekly",
        "sub_tasks": [
            "Isometric Split Squat Holds 4x30-45s/leg",
            "Standing OHP 4x8",
            "Hanging Leg Raises 4x12",
            "Mobility Flow 20min",
        ],
    },
    {
        "title": "Thursday GYM",
        "repeat_interval": "weekly",
        "sub_tasks": [
            "Goblet Squats (heels elevated) 4x12-15",
            "Single-Leg RDL 3x10/leg",
            "ATG Split Squat 3x10/leg",
            "Jump Squats 3x10",
        ],
    },
    {
        "title": "Friday Workout",
        "repeat_interval": "weekly",
        "sub_tasks": [
            "Incline DB Bench 4x10",
            "Arm Farm Superset (BB/DB Curls 4x12)",
            "Overhead Tricep Extensions 4x12",
            "Plyometric Lunges 4x20sec",
        ],
    },
]


def post(path, payload):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


created = []
for w in WORKOUTS:
    parent = post("/api/tasks", {
        "title": w["title"],
        "description": "",
        "parent_id": None,
        "repeat_interval": w["repeat_interval"],
    })
    pid = parent["id"]
    subs = []
    for st in w["sub_tasks"]:
        sub = post("/api/tasks", {
            "title": st,
            "description": "",
            "parent_id": pid,
            "repeat_interval": None,
        })
        subs.append(sub["id"])
    created.append((w["title"], pid, len(subs)))

print("CREATED:")
for t, pid, n in created:
    print(f"  id={pid:>3}  {t}  ({n} exercises)")

print("\nVERIFY /api/tasks:")
with urllib.request.urlopen(BASE + "/api/tasks", timeout=15) as r:
    tasks = json.loads(r.read().decode())
print(f"  top-level tasks: {len(tasks)}")
for t in tasks:
    flag = "WEEKLY" if t.get("repeat_interval") == "weekly" else "      "
    print(f"  [{flag}] #{t['id']} {t['title']} -> {len(t['sub_tasks'])} subs")
