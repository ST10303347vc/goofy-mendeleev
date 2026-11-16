def clean_day_points(day):
    """Return the points earned for the given one-based day of a quit streak."""
    week, offset = divmod(day - 1, 7)
    return (1 << week) + offset


def _points_through(streak):
    weeks, remaining = divmod(max(0, streak), 7)
    next_week_base = 1 << weeks
    # Each complete week adds offsets 0 through 6 and doubles its base.
    return (
        7 * (next_week_base - 1)
        + 21 * weeks
        + remaining * next_week_base
        + remaining * (remaining - 1) // 2
    )


def newly_earned_points(previous_streak, new_streak):
    """Count newly completed days without recalculating points already paid."""
    return _points_through(new_streak) - _points_through(previous_streak)
