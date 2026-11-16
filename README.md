# Goofy Mendeleev

Goofy Mendeleev is a personal tracker for tasks, workouts, habits, hydration, and progress through the year. The Mac app uses the original Quiet Tracker dashboard from `748462e`.

Open **Goofy Mendeleev** from Spotlight or from your home Applications folder. Use the green window control to enter macOS full screen. The date opens Habits, the clock opens Archive, and tapping the water column advances its fill. The app works offline after setup.

Choose **Theme → Light** (warm white and indigo) or **Theme → Dark** (warm charcoal and soft indigo) in the Mac menu bar. Your choice is saved and applies to the dashboard, Archive, dialogs, and locked clock. The standalone browser dashboard also has a theme picker. Use the **×** or **Esc** to close Archive or a dialog.

Choose **View → Lock Display** or press **⇧⌘L** to open the locked clock. The elapsed year fills the background, and Your Progress sits below the clock. Click the locked clock or press **⇧⌘L** again to authenticate with macOS. The app remembers the locked state if you quit while locked.

Click the date for **Build** habit check-ins or **Quit** habit lapses. Click **Year Progress** for a daily reflection. **View → Performance** samples system CPU and shows whether the dashboard server is running, with a shortcut to Activity Monitor.

Each water tap logs 150 mL. Ten taps fill a 1.5 L bottle. The column shows the personal tiers at one, two, and three bottles, and saves partial progress across launches.

**Today's Plan** keeps boxing fitness on Monday, technique on Wednesday, and sparring on Friday. Tuesday and Saturday are full-body muscle-gain sessions with legs first. Thursday adds a short optional leg session; walk or rest instead if your legs feel heavy before sparring. Sunday is recovery. At full volume, the plan gives you 10 quad, 8 hamstring, and 7 calf work sets per week. Start at the lower volume in the session notes and build up as recovery allows. Log your weights and reps and add weight once all sets reach the top of the rep range with good form and about two reps left. Morning salt water and creatine count as reminders.

**Light daily movement** is optional. Easy bodyweight squats are one option if you want more frequent leg practice. Keep them easy; the lifting sessions supply the muscle-building work. Level 2 starts after five logged days on this routine and level 3 after ten, with the new level appearing on the next movement day. Boxing days offer the starter effort at every level.

A Quit habit credits finished clean calendar days. The first three weeks pay 1–7, 2–8, and 4–10 points per day. The starting value doubles each week and rises by one each day within the week. Logging a lapse earns zero for that day and starts a new streak tomorrow.

Use `./goofy tasks add "Take a lunch walk"`, `./goofy tasks list`, or `./goofy tasks done 7` from this checkout. The CLI uses the app’s database while the window is open, locked, or closed. Add `--repeat daily`, `--repeat weekly`, `--priority`, or `--notes "…"` to a new task. To capture a task through the local Codex chat, just ask it to add the task to Goofy Mendeleev.

To rebuild and install from this checkout, run `./install-mac.sh`. The build uses Python 3.10 or later, Node.js with npm, and the Xcode Command Line Tools. The installed app uses that Python interpreter and includes its packages, CSS, scripts, icons, and fonts. Use `GOOFY_PYTHON=/path/to/python3 ./install-mac.sh` to select Python. `./install-mac.sh --build-only` creates a local candidate under `.build/restored`.

`./run.sh` starts the same dashboard at `http://127.0.0.1:8000` for browser use. Both launchers use `~/Library/Application Support/Goofy Mendeleev/tracker.db`. Use **Goofy Mendeleev → Open Data Folder** to locate it. Quit the tracker before making a copy of the database.

If you find a previous `tracker.db`, run `./run.sh --import-legacy "/path/to/tracker.db"` before first opening a fresh database. The import verifies a copy and refuses to replace an existing database. `GOOFY_DB_PATH` selects a separate database for testing.

[Design proposals and Apple references](docs/IMPROVEMENTS.md) · [Mac handoff](docs/MAC-HANDOFF.md)
