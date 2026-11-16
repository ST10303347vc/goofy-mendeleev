# Goofy Mendeleev design notes

The baseline is the original Quiet Tracker dashboard in `748462e`. It puts progress on the surface and opens details from the elements already on screen. Tapping the date opens Habits, tapping the clock opens Archive, and tapping the water column increases the fill. The checked-in year bars show the year and your progress. The earlier year detail screen was not found in the available source.

## Proposals for review

| Priority | Idea | How it could work |
| --- | --- | --- |
| 1 | Dedicated desktop | Use the existing macOS full-screen window on its own Space. Keep the dashboard ready when you switch back. Start by trying that setup with the restored design. |
| 2 | Year display | Let a click on either progress bar open a quiet view of the two existing measures with room to read them at a glance. Keep it useful while left open. A click on the progress or Escape could return to the dashboard in one action. |
| 3 | Reveal the gestures when needed | Keep the existing surfaces as the visible controls. Consider a pointer hint or a short tooltip on hover. Offer keyboard access and accessible names for the same actions, with commands in the macOS menu bar for people who use it. |
| 4 | Motion and idle behavior | Give water immediate fill feedback. Keep the year display still between meaningful changes. If you add transitions, use a short fade or a restrained move and honor Reduce Motion. |
| 5 | Details behind the existing surfaces | Keep workouts, daily and one-time tasks, Build habits, and Quit habits within the details they relate to. Review each reveal and what it should contain before changing it. |

The first design decision is what the year detail view should show when left open. The two existing bars would be enough for a first version. Days remaining or the pace needed to finish could be secondary information if you want them.

## Implemented in 1.2

- The locked view uses a charcoal field for the elapsed year, a black remainder, a large centered clock, and a thick rounded personal progress bar. **View → Lock Display** and **⇧⌘L** enter it. Clicking the locked clock asks macOS to authenticate. The locked view runs without WebKit or the Python server. [Apple Color guidance](https://developer.apple.com/design/human-interface-guidelines/color) · [Apple Local Authentication](https://developer.apple.com/documentation/localauthentication/lapolicy/deviceownerauthentication)
- **View → Performance** samples system CPU and shows whether the dashboard server is running. It includes a shortcut to Activity Monitor.
- The local task CLI can add, list, and complete tasks from the same Mac. The app reads the same SQLite database and the open dashboard refreshes after CLI edits.
- The date still opens Habits, now with Build check-ins and Quit lapses. Year Progress opens a private daily reflection. Keyboard focus and progress label contrast are clearer, and web transitions honor Reduce Motion. [Apple Motion guidance](https://developer.apple.com/design/human-interface-guidelines/motion)

The next addition I’d prioritize is a short weekly review that summarizes the work you already log and asks what to carry into next week. After that, named goals such as workouts per week or reading days could make progress more specific. A simple sleep or energy check-in is optional if it helps you understand your patterns.

## Apple references

- Apple’s macOS guidance covers full-screen windows, comfortable viewing density, menus, keyboard shortcuts, and transitions between active and inactive use. Apple’s Spaces guide explains the dedicated full-screen desktop. [Designing for macOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-macos/) · [Work in multiple spaces on Mac](https://support.apple.com/guide/mac-help/work-in-multiple-spaces-mh14112/mac)
- Apple recommends familiar gestures, quick feedback, and another way to perform important actions. A click on a visible surface can stay primary while the keyboard and assistive technology reach the same action. [Gestures](https://developer.apple.com/design/human-interface-guidelines/gestures) · [Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)
- Apple recommends purposeful motion and reducing repetitive animation when Reduce Motion is enabled. That fits short feedback for water and a calm year display. [Motion](https://developer.apple.com/design/human-interface-guidelines/motion)

## Efficiency work to consider next

- Measure idle CPU and energy in Activity Monitor with the dashboard visible, covered, and on another Space. Keep the visible clock as it is. If the hidden clock still wakes up in WebKit, test window visibility signals from AppKit.
- Measure launch and dashboard loading with a year of real-sized test data. If loading old records is the bottleneck, fetch those records only when their detail opens.
- Profile which clock, progress, and task updates repaint the dashboard. Scope updates to the pieces that changed while keeping the current appearance and interactions.
- Test backup and restore separately before adding any data migration or changing scoring.

## Athlete view proposal

Use the prebuilt Z-Anatomy model from Anatomy Atlas to make two still images of the same body, from the front and back. Keep the lighting and body position fixed, and export an aligned mask for each major muscle group. The app can recolor those masks locally when the workout details open. The model already comes in GLB format with named muscles. Its asset license is CC BY-SA 4.0. [Anatomy Atlas model and credits](https://github.com/SirwanAfifi/anatomy-atlas#model-attribution)

- Give the chest, shoulders, biceps, triceps, back, abs, glutes, quads, hamstrings, and calves their own regions. Keep the idle figure neutral and use two shades to show primary and supporting work.
- Add exercise-level logging before using the map to summarize your workouts. Curls highlight biceps. A dumbbell press highlights chest, with shoulders and triceps shown as supporting muscles. The current whole-session checkmark only stores the plan and the session completion.
- Let the workout preview show planned targets. Update the history view from logged exercises and show the date of the last direct work when a muscle is selected. Log boxing as conditioning alongside lifting.
