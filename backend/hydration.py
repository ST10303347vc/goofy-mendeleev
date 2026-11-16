BOTTLE_ML = 1500
TAP_ML = BOTTLE_ML // 10
TIERS = ("Minimum", "Better", "Best")


def read_water(conn, day):
    row = conn.execute("SELECT count, partial_ml FROM water_log WHERE date = ?", (day,)).fetchone()
    count = (row["count"] or 0) if row else 0
    partial = row["partial_ml"] if row else 0
    next_tier = None
    if count < len(TIERS):
        next_tier = {"name": TIERS[count], "total_ml": (count + 1) * BOTTLE_ML}
    return {
        "date": day,
        "count": count,
        "partial_ml": partial,
        "total_ml": count * BOTTLE_ML + partial,
        "bottle_ml": BOTTLE_ML,
        "step_ml": TAP_ML,
        "tier": TIERS[min(count, len(TIERS)) - 1] if count else None,
        "next_tier": next_tier,
    }


def log_water(conn, day, amount_ml, *, stop_at_best=False):
    current = read_water(conn, day)
    if stop_at_best and current["next_tier"] is None:
        return dict(current, points_awarded=0)

    count, partial = divmod(current["total_ml"] + amount_ml, BOTTLE_ML)
    conn.execute(
        "INSERT INTO water_log (date, count, partial_ml) VALUES (?, ?, ?) "
        "ON CONFLICT(date) DO UPDATE SET count = excluded.count, partial_ml = excluded.partial_ml",
        (day, count, partial),
    )
    points = count - current["count"]
    if points:
        row = conn.execute("SELECT value FROM settings WHERE key = 'task_points'").fetchone()
        balance = int(row["value"]) if row else 0
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('task_points', ?)", (str(balance + points),))
    return dict(read_water(conn, day), points_awarded=points)
