# Goofy Mendeleev Mac handoff

12 November 2026 · Owner Ushe · Work item Goofy Mendeleev Mac setup, this chat.

Repository `ST10303347vc/goofy-mendeleev` · Local `master` · Baseline `748462e7f2c870bd5835677126aba12ef1200b21`.

| Checkpoint | Exit criterion | Evidence and next action |
| --- | --- | --- |
| 1. Find the original | Identify the dashboard with the original interactions. | The original GitHub checkout contains the dashboard, the water fill, and the date and clock actions. A check of the original project context and remote refs found no later copy with the year detail reveal. A separate recovered SwiftUI prototype is set aside under `.build/superseded-prototype`. |
| 2. Restore and optimize | Preserve the original dashboard and make launch and refresh cheaper. | Compared dashboard body and stylesheet rules with the baseline. Only asset loading changed in the presentation files. Local assets include the original font families. The original clock stays live while visible. The app pauses the clock when hidden, loads dashboard data in one request, and avoids repeat SQLite writes during the same day. |
| 3. Prove the build | Check original behavior and isolation using disposable data. | Browser smoke verified all three original progress bars, date and clock reveals, ten-tap water fill, persistence on relaunch, local fonts, one initial API request, and no external requests. The signed Apple silicon build also displayed the original dashboard in the installed Mac app. The standard full-screen control worked. Quitting ended the local server. |
| 4. Hand off | Provide the installed app and design proposals. | Installed `~/Applications/Goofy Mendeleev.app`. Verified with an isolated database and left the default tracker database untouched. [Design proposals and Apple sources](IMPROVEMENTS.md) are ready for review. |

The scope is local source, build, install, and proof. The data check found no previous tracker database to import. GitHub, production, and provider state were outside this work.

## Light locked display

12 November 2026 · Owner Ushe · Work item approved in this chat · Local `master` at `748462e7f2c870bd5835677126aba12ef1200b21` with the existing Mac setup changes.

| Checkpoint | Exit criterion | Evidence and next action |
| --- | --- | --- |
| 1. Scope | Preserve the original interactions and choose a reversible entry to the locked display. | The current clock opens Archive. Use a Mac menu command to lock, and the locked clock or menu to request authentication. Next: build the native view and fix the bar contrast. |
| 2. Build | Show the clock and two progress bars in a light native view. Start and stop the local dashboard with the lock state and remember that state across launches. | The Apple silicon candidate built and signed. The locked view reads the saved points directly from SQLite and the dashboard now uses one dark Year Progress label over a light track and fill. Next: test with an isolated bundle ID and database. |
| 3. Prove and install | Check label contrast, lock and unlock, and relaunch with an isolated database. Install the signed build in the existing local Applications location. | The isolated app went full screen and read a 63.7% saved value. macOS authentication returned to the original dashboard with a new server. Relaunch restored the lock without spawning Python. The Year Progress label measured 15.2:1 over the track and 9.6:1 over the fill. The browser smoke check also covered the existing date, clock, and water interactions. Installed and verified the signature of version 1.1 in `~/Applications/Goofy Mendeleev.app`. Quit and reopen any earlier running copy to use the update. |

## Dark display and local task capture

12 November 2026 · Owner Ushe · Approved in this chat · Local `master`, baseline `748462e7f2c870bd5835677126aba12ef1200b21` with existing Mac changes.

| Checkpoint | Exit criterion | Evidence and next action |
| --- | --- | --- |
| 1. Scope | Identify the current install and old app bundles. Define one reviewable iteration. | The installed app is 1.1; the older WebKit and Focus Race bundles were identified by bundle ID and path. Build the dark display, local CLI, on-demand CPU check, and small improvements inside the existing dashboard interactions. |
| 2. Build | Add native full-screen year fill and verify shared data paths for the app and CLI. | The signed candidate built. Browser verification passed for habit check-in and undo, reflection persistence, contrast, and the original water and dashboard actions. CLI verification passed for create, list, and repeated completion without double points. Confirm the open Mac dashboard sees CLI updates. |
| 3. Proof and handoff | Verify the changes against disposable data, install locally, and move the old bundles to Trash. | Verified the dark full-screen layout, live CLI task appearance, and CPU report with the dashboard server off in the isolated app. Installed and reopened signed version 1.2 in the existing locked state. The installed CLI passed with a disposable database. Moved superseded app bundles to Trash. Next: get feedback on the dark display and daily reflection. |

## Remove Guidance

12 November 2026 · Owner Ushe · Approved in this chat · Local `master` at `748462e7f2c870bd5835677126aba12ef1200b21` with Mac 1.2 changes.

| Checkpoint | Exit criterion | Evidence and next action |
| --- | --- | --- |
| Scope | Remove the in-app AI flow while preserving task capture. | Located the Guidance modal, provider route, and provider-only dependencies. Keep the plus button and CLI. |
| Build and proof | No Guidance surface or provider route. Manual task creation and CLI still work. | The browser check verified that Guidance is gone and the plus button saves a task directly. The signed candidate's CLI added and listed a task with a disposable database. The provider packages are absent from the bundle. Next: install and reopen the local app. |
| Handoff | Install the verified build and reopen it on the Mac. | Installed and reopened signed version 1.2.1 in the existing Applications location. Task capture can continue through the plus button or local CLI. |

## Personal training, hydration, and quit plan

12 November 2026 · Owner Ushe · Approved in this chat · Local `master` at `748462e7f2c870bd5835677126aba12ef1200b21` with Mac 1.2.1 changes.

| Checkpoint | Exit criterion | Evidence and next action |
| --- | --- | --- |
| 1. Scope | Agree on day-specific training, hydration tiers, and the quit formula before editing. | Use the existing Today and Habits surfaces. Delegate hydration, workout plan implementation, and quit scoring, then integrate and verify against disposable databases. The athlete view is a design proposal. |
| 2. Integrate | Keep existing records, show the requested routine and tiers, and avoid counting reminders as workouts. | Implemented the three slices. A verified SQLite backup is in the tracker’s Backups folder. Rehearsal on a copy retained the existing task rows, water history, points, and today's prior creatine checkmark. Salt water was left unchecked. |
| 3. Proof | Verify dates, point accrual and lapse reset, hydration persistence, and the installed Mac bundle. | Verified the seven-day schedule, duplicate workout completion, rollover and lapse scoring, concurrent water taps, and partial fill across reload. The combined browser check passed. Built and signed the Mac candidate. |
| 4. Handoff | Configure the two personal quit habits in the user’s local data and explain the training plan and athlete recommendation. | Installed and verified signed Mac version 1.3, configured both quit entries from today, and reopened the app in its locked state. The live dashboard payload includes both new reminders and the 1.5 L bottle. Existing points were kept. The [Athlete view proposal](IMPROVEMENTS.md#athlete-view-proposal) covers anatomy assets, exercise tagging, and the later 3D viewer. |

## Muscle-gain schedule and Athlete view recommendation

12 November 2026 · Owner Ushe · Work item approved in this chat · Local `master`, baseline `748462e7f2c870bd5835677126aba12ef1200b21` with the existing Mac 1.3 working changes.

| Checkpoint | Exit criterion | Evidence and next action |
| --- | --- | --- |
| Scope | Identify the current schedule, completion behavior, and body-map options. | `backend/training.py` serves Today’s Plan. There is one required strength day. Completions retain a dated plan snapshot. Next, add two lifting sessions and document the suggested artwork. |
| Local source | Offer two full-body muscle-gain sessions around three boxing days, with instructions for progression. | Added strength A on Tuesday and strength B on Saturday, made Thursday cardio optional, and documented a two-view body map. The new lifting sessions have their own slots and a versioned completion snapshot. Next, check the dashboard and completion API across a full week. |
| Proof and handoff | Verify the weekly schedule, saved history, and completion in disposable data. | Flask dashboard checks passed for all seven days and their next-day previews. Each new lifting completion counted once when retried. A version 1 record survived initialization, and the creatine reminder did not increment workout totals. The edits are in `backend/training.py`, `README.md`, and the existing project notes. Next, review the new routine in the source checkout. The installed Mac bundle is still 1.3. The Athlete view remains a proposal. |

## Boxing session details

12 November 2026 · Owner Ushe · Follow-up in this chat · Local `master` at `748462e7f2c870bd5835677126aba12ef1200b21` with the muscle-gain working changes.

| Checkpoint | Exit criterion | Evidence and next action |
| --- | --- | --- |
| Scope | Match the boxing days to Ushe’s routine and account for the heavier sessions in the lifting notes. | The three days share a generic Boxing block. Split the plan text while keeping its existing completion slot. |
| Local source | Show full fitness on Monday, technique on Wednesday, and sparring on Friday, with lighter fitness on the last two days. | Updated `backend/training.py` and `README.md`. Tuesday and Saturday include an option to lift with two work sets if tired. The plan keeps the same boxing slot and stores new titles in version 3 completion snapshots. Next, check the dashboard and completion API. |
| Proof and handoff | Verify daily labels, next-day previews, and old and new boxing completions against disposable data. | The Flask dashboard and completion API passed for a full week. An existing Monday completion retained its snapshot and checkmark. Wednesday and Friday saved their own titles, and retries counted once. The Thursday and lifting notes appeared on their assigned days. The source checkout is ready to preview. The installed Mac bundle is still 1.3. |

## Daily movement progression

12 November 2026 · Owner Ushe · Follow-up in this chat · Local `master` at `748462e7f2c870bd5835677126aba12ef1200b21` with the existing boxing and muscle-gain edits.

| Checkpoint | Exit criterion | Evidence and next action |
| --- | --- | --- |
| Scope | Let actual movement check-offs set the pace. Keep the routine optional around boxing and lifting. | The app already stores one completion per day and slot. Use that history to advance after five and ten check-offs on the new routine. |
| Local source | Show the right level in Today’s Plan and keep the day’s target stable after check-off. | Updated `backend/training.py`, `backend/main.py`, and `README.md`. The level uses prior dated check-offs from plan version 4 onward. The existing completion slot preserves earlier checkmarks. Next, exercise the thresholds through the dashboard and completion API. |
| Proof and handoff | Verify both thresholds, skipped days, prior history, and boxing and Sunday behavior in disposable data. | Dashboard and completion API checks passed through both unlocks, skipped days, same-day retries, a migrated Daily Protocol entry, and earlier history. Boxing kept the starter target and Sunday showed recovery. The new levels are available in the source checkout. The installed Mac bundle is still 1.3. |

## Mac 1.4 training update

12 November 2026 · Owner Ushe · Mac update requested in this chat · Local `master` at `748462e7f2c870bd5835677126aba12ef1200b21` with the existing training changes.

| Checkpoint | Exit criterion | Evidence and next action |
| --- | --- | --- |
| Scope | Identify the installed version, build path, and release path. | Installed app is 1.3. GitHub reports zero Actions workflows for this repository. The existing build-only mode writes to the checkout. Next, give the candidate a distinct version and build it there. |
| Candidate | Produce a signed Apple silicon app with the training changes. | Built `.build/restored/Goofy Mendeleev.app` from the local working changes. The bundle identifies as 1.4, build 6, and passed strict signature verification. The bundled training module matches the working source. |
| Proof and handoff | Exercise the packaged workout code with a disposable database and identify the path to the installed update. | The packaged CLI and dashboard passed. The schedule and five- and ten-day unlocks passed on disposable data. A browser preview from the bundle returned HTTP 200 and showed the starter movement and next-day sparring. The installed bundle still reports 1.3. Next, obtain Ushe’s explicit exception for this one native update under the standing release instruction. |

## Warm white and indigo on Mac 1.4

13 November 2026 · Owner Ushe · Theme and one-time Mac install approved in this chat · Local `master` at `748462e7f2c870bd5835677126aba12ef1200b21` with the existing 1.4 training changes.

| Checkpoint | Exit criterion | Evidence and next action |
| --- | --- | --- |
| Scope | Identify the palette and confirm the installed version. | Version 1.3 is installed. Apply warm white, charcoal, and indigo to the existing dashboard. Verify the year label on its track and fill, plus the existing gestures, in a signed 1.4 candidate. |
| Candidate | Show the approved colors in the bundled dashboard and pass gesture checks with disposable data. | Rebuilt the signed candidate after changing the indigo bar’s small labels to white. The browser measured 13.4:1 on the year track, 11.3:1 on its fill, and 7.4:1 on indigo. The clock, date, year reflection, water tap, and movement check-off passed. Changes are in `frontend/styles.css` and `scripts/tailwind.config.cjs`. |
| Install and handoff | Install 1.4 once and verify that the Mac launches it with the new theme and training plan. | Verified a backup of `tracker.db` in `Backups/before-1.4.Y3iIZn`. Installed and launched the signed 1.4 bundle in `~/Applications`. The running app served the new palette, Friday sparring, Light Daily Movement Level 1, and Saturday’s lifting preview. The live database passed SQLite’s quick check. The previous signed app is available in `.build/before-1.4.K7BrTo`. The one-time authorization was used for this Mac install. |

## Athlete body map preview

13 November 2026 · Owner Ushe · Goofy Mendeleev Athlete view follow-up in this chat · Local `master` at `748462e7f2c870bd5835677126aba12ef1200b21` with existing 1.4 working changes.

| Checkpoint | Exit criterion | Evidence and next action |
| --- | --- | --- |
| Scope and asset | Confirm the source for a standalone front and back preview of Tuesday’s lifting plan. | Anatomy Atlas supplies a named Z-Anatomy GLB at revision `1c4185438dec1e6a396c325c6e07655d05a79c0a`. No local Blender app was found. Render the converted mesh directly and preserve its attribution. |
| Preview | Both views show the primary and supporting groups for each selected exercise in Tuesday’s plan. | Rendered front and back stills and aligned region masks from the pinned model with Three.js. Embedded the stills in `.build/athlete-preview/index.html` and added the six exercise selections and artwork credit. |
| Handoff | Verify exercise selection, front and back alignment, and opening the preview as a local file. | Chrome opened the file offline. All six keyboard selections, labels, and highlight changes passed. Both silhouettes kept their alignment, and the desktop and narrow layouts were inspected. The first curl check assumed almost no rear highlight; review confirmed the outer edges of the biceps were visible, and the front highlight covered more than eight times the rear area. The work is local preview only. Next action is Ushe’s review of the artwork and interaction. |
| Phone preview | Give Ushe access to the same six exercise views from this conversation. | Added the conversation preview using the existing artwork and a touch-friendly exercise selector. All six selections and both images worked in Chrome at 320 pixels. Next action is Ushe’s review on the phone. |

## Shared appearance, close controls, and leg priority

13 November 2026 · Owner Ushe · Goofy Mendeleev follow-up in this chat · Local `master`, baseline `748462e7f2c870bd5835677126aba12ef1200b21` with the existing 1.4 working changes.

| Checkpoint | Exit criterion | Evidence and next action |
| --- | --- | --- |
| Scope | Confirm the installed appearance and the current clock and workout paths. | Installed 1.4 uses warm white and indigo in WebKit and a hard-coded dark palette in the native locked display. Archive has its own close handler and the task button sits above the shared modal backdrop. Tuesday and Saturday are full-body lifting days; Thursday is optional cardio. Next: share the appearance setting, fix dialog layering and dismissal, and add recoverable leg volume around boxing. |
| Local source | A saved Mac Theme menu updates both displays; dialog close buttons and Escape work; the training plan prioritizes legs while preserving dated history. | Added native Theme preferences and themed web surfaces, one dialog state and shared close behavior, and training version 5 with two leg-first lifting days plus an optional Thursday session. Existing workout slots and the movement progression baseline are retained. Next: build and test with disposable data. |
| Candidate and proof | Verify both palettes, controls, weekly schedule and data isolation; build a signed local candidate. | Packaged Chrome checks passed for both themes, contrast, all six close buttons, Escape, backdrop dismissal, and focus return. These checks exposed a transparent modal style and Habits tabs overlapping the close control; both were corrected. An isolated AppKit build exercised the Theme menu in live WebKit and the native locked clock and checked the saved setting. The packaged API passed seven days of training, next-day previews, repeat completion, and unchanged old snapshots. |
| Handoff | Verify the candidate and identify the install boundary. | The local `.build/restored/Goofy Mendeleev.app` is signed 1.5 (build 7). The installed copy is still 1.4 and the live tracker data was untouched. The earlier one-time approval covered 1.4. Next: obtain explicit authorization for this specific local install. |

## GitHub publication and Windows review

16 November 2026 · Owner Ushe · GitHub push and Windows review requested in this chat · Local `master`, baseline `748462e7f2c870bd5835677126aba12ef1200b21`.

| Checkpoint | Exit criterion | Evidence and next action |
| --- | --- | --- |
| Source review | Identify the changes to publish and confirm the target branch. | The existing source and handoff changes are ready for one commit to `ST10303347vc/goofy-mendeleev` on `master`. Local build outputs and tracker databases are ignored. |
| Windows review | Identify the available launch path and its verification scope. | The browser dashboard has Python and Node entry points and a Windows data path. The bundled app uses AppKit, WebKit, and LocalAuthentication on macOS. This was a source review. A Windows runtime check is pending. |
| GitHub verification | Read back the published commit from `origin/master`. | Record the verified SHA in the handoff for this chat. |
