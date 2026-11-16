import AppKit
import SQLite3

final class LockedDisplay: NSView {
    private let clock: NSButton
    private let yearLabel = NSTextField(labelWithString: "Year Progress")
    private var yearFraction = 0.0
    private let personal = LockedProgressBar(label: "Your Progress")
    private var theme: TrackerTheme
    private var timer: Timer?

    init(theme: TrackerTheme, target: AnyObject, unlock: Selector) {
        self.theme = theme
        clock = NSButton(title: "", target: target, action: unlock)
        super.init(frame: .zero)
        clock.isBordered = false
        clock.font = .monospacedDigitSystemFont(ofSize: 144, weight: .light)
        clock.toolTip = "Unlock Display"

        yearLabel.font = .monospacedDigitSystemFont(ofSize: 12, weight: .medium)
        for view in [clock, personal, yearLabel] {
            view.translatesAutoresizingMaskIntoConstraints = false
            addSubview(view)
        }
        let preferredWidth = personal.widthAnchor.constraint(equalToConstant: 620)
        preferredWidth.priority = .defaultHigh
        NSLayoutConstraint.activate([
            clock.centerXAnchor.constraint(equalTo: centerXAnchor),
            clock.centerYAnchor.constraint(equalTo: centerYAnchor),
            personal.centerXAnchor.constraint(equalTo: centerXAnchor),
            personal.topAnchor.constraint(equalTo: clock.bottomAnchor, constant: 34),
            personal.widthAnchor.constraint(lessThanOrEqualTo: widthAnchor, multiplier: 0.78),
            preferredWidth,
            yearLabel.centerXAnchor.constraint(equalTo: centerXAnchor),
            yearLabel.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -30),
        ])
        setTheme(theme)
        updateClock()
    }

    required init?(coder: NSCoder) { nil }

    override func draw(_ dirtyRect: NSRect) {
        theme.paper.setFill()
        NSBezierPath(rect: dirtyRect).fill()
        theme.yearFill.setFill()
        NSBezierPath(rect: NSRect(x: bounds.minX, y: bounds.minY,
                                 width: bounds.width * yearFraction, height: bounds.height)).fill()
    }

    func setTheme(_ theme: TrackerTheme) {
        self.theme = theme
        appearance = theme.appearance
        clock.contentTintColor = theme.ink
        yearLabel.textColor = theme.muted
        personal.setTheme(theme)
        needsDisplay = true
    }

    func setPersonalProgress(_ value: Double?) { personal.setProgress(value) }

    func setClockActive(_ active: Bool) {
        if !active {
            timer?.invalidate()
            timer = nil
            return
        }
        guard timer == nil else { return }
        updateClock()
        let nextMinute = Date(timeIntervalSince1970: (floor(Date().timeIntervalSince1970 / 60) + 1) * 60)
        let timer = Timer(fire: nextMinute, interval: 60, repeats: true) { [weak self] _ in
            self?.updateClock()
        }
        timer.tolerance = 1
        self.timer = timer
        RunLoop.main.add(timer, forMode: .common)
    }

    private func updateClock() {
        let now = Date()
        let time = DateFormatter.localizedString(from: now, dateStyle: .none, timeStyle: .short)
        clock.title = time
        clock.setAccessibilityLabel("Unlock Display, \(time)")
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = .autoupdatingCurrent
        if let interval = calendar.dateInterval(of: .year, for: now) {
            let fraction = now.timeIntervalSince(interval.start) / interval.duration
            yearLabel.stringValue = "Year Progress · \(fraction.formatted(.percent.precision(.fractionLength(1))))"
            if fraction != yearFraction {
                let oldEdge = bounds.width * yearFraction
                let newEdge = bounds.width * fraction
                yearFraction = fraction
                setNeedsDisplay(NSRect(x: min(oldEdge, newEdge), y: 0, width: abs(newEdge - oldEdge) + 1, height: bounds.height))
            }
        }
    }

    static func personalProgress(in database: URL) -> Double? {
        if !FileManager.default.fileExists(atPath: database.path) { return 0 }
        var connection: OpaquePointer?
        defer { if let connection { sqlite3_close(connection) } }
        guard sqlite3_open_v2(database.path, &connection, SQLITE_OPEN_READONLY, nil) == SQLITE_OK,
              let connection else { return nil }
        sqlite3_busy_timeout(connection, 250)
        var statement: OpaquePointer?
        guard sqlite3_prepare_v2(connection, "SELECT value FROM settings WHERE key = 'task_points'", -1, &statement, nil) == SQLITE_OK else { return nil }
        defer { sqlite3_finalize(statement) }
        switch sqlite3_step(statement) {
        case SQLITE_ROW:
            guard let text = sqlite3_column_text(statement, 0), let points = Double(String(cString: text)), points.isFinite else { return nil }
            return min(1, max(0, points / 1000))
        case SQLITE_DONE:
            return 0
        default:
            return nil
        }
    }
}

private final class LockedProgressBar: NSView {
    private let title: NSTextField
    private let percent = NSTextField(labelWithString: "—")
    private let track = ProgressTrack()

    init(label: String) {
        title = NSTextField(labelWithString: label)
        super.init(frame: .zero)
        title.font = .systemFont(ofSize: 14, weight: .medium)
        percent.font = .monospacedDigitSystemFont(ofSize: 14, weight: .medium)
        let heading = NSStackView(views: [title, NSView(), percent])
        heading.orientation = .horizontal
        heading.alignment = .firstBaseline
        let stack = NSStackView(views: [heading, track])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 8
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: leadingAnchor),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor),
            stack.topAnchor.constraint(equalTo: topAnchor),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor),
            heading.widthAnchor.constraint(equalTo: stack.widthAnchor),
            track.widthAnchor.constraint(equalTo: stack.widthAnchor),
            track.heightAnchor.constraint(equalToConstant: 23),
        ])
        setAccessibilityElement(true)
        setAccessibilityRole(.progressIndicator)
        setAccessibilityLabel(label)
        setProgress(nil)
    }

    required init?(coder: NSCoder) { nil }

    func setTheme(_ theme: TrackerTheme) {
        title.textColor = theme.ink
        percent.textColor = theme.ink
        track.theme = theme
        track.needsDisplay = true
    }

    func setProgress(_ fraction: Double?) {
        let text = fraction?.formatted(.percent.precision(.fractionLength(1)))
        percent.stringValue = text ?? "—"
        setAccessibilityValue(text ?? "Unavailable")
        track.fraction = fraction ?? 0
        track.needsDisplay = true
    }
}

private final class ProgressTrack: NSView {
    var theme: TrackerTheme = .light
    var fraction = 0.0

    override func draw(_ dirtyRect: NSRect) {
        let frame = bounds.insetBy(dx: 0.5, dy: 0.5)
        let path = NSBezierPath(roundedRect: frame, xRadius: frame.height / 2, yRadius: frame.height / 2)
        theme.progressTrack.setFill()
        path.fill()
        NSGraphicsContext.saveGraphicsState()
        path.addClip()
        theme.indigo.setFill()
        let width = frame.width * fraction
        if width > 0 {
            let radius = min(width, frame.height) / 2
            let filled = NSRect(x: frame.minX, y: frame.minY, width: width, height: frame.height)
            NSBezierPath(roundedRect: filled, xRadius: radius, yRadius: radius).fill()
        }
        NSGraphicsContext.restoreGraphicsState()
        let highContrast = NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast
        (highContrast ? NSColor.secondaryLabelColor : NSColor.separatorColor).setStroke()
        path.stroke()
    }
}
