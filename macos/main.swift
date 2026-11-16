import AppKit
import LocalAuthentication
import WebKit

enum TrackerTheme: String, CaseIterable {
    case light, dark

    var appearance: NSAppearance? { NSAppearance(named: self == .light ? .aqua : .darkAqua) }
    var paper: NSColor { color(0xf8f7f3, 0x1b1a19) }
    var ink: NSColor { color(0x202124, 0xf2efe8) }
    var muted: NSColor { color(0x62605b, 0xbab5aa) }
    var yearFill: NSColor { color(0xdad8d0, 0x393633) }
    var progressTrack: NSColor { color(0xeceae5, 0x4b4641) }
    var indigo: NSColor { color(0x394bb6, 0xa6b1ff) }

    private func color(_ light: UInt32, _ dark: UInt32) -> NSColor {
        let value = self == .light ? light : dark
        return NSColor(srgbRed: Double(value >> 16) / 255, green: Double((value >> 8) & 255) / 255,
                       blue: Double(value & 255) / 255, alpha: 1)
    }
}

final class TrackerApp: NSObject, NSApplicationDelegate, NSWindowDelegate, NSMenuItemValidation, WKNavigationDelegate, WKUIDelegate {
    private static let taskChange = Notification.Name("local.goofy-mendeleev.tasksChanged")
    private static let lockPreference = "displayIsLocked"
    private static let themePreference = "trackerTheme"
    private var window: NSWindow!
    private var webView: WKWebView?
    private var lockedDisplay: LockedDisplay?
    private var lockMenuItem: NSMenuItem?
    private var authentication: LAContext?
    private var isLocked = UserDefaults.standard.bool(forKey: TrackerApp.lockPreference)
    private var theme = UserDefaults.standard.string(forKey: TrackerApp.themePreference)
        .flatMap(TrackerTheme.init(rawValue:)) ?? .light
    private var themeMenuItems: [NSMenuItem] = []
    private var backend: Process?
    private var input: Pipe?
    private var output: Pipe?
    private var readiness = Data()
    private var home: URL?
    private var failed = false
    private var quitting = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        makeMenu()
        DistributedNotificationCenter.default().addObserver(self, selector: #selector(reloadCLITasks(_:)),
            name: Self.taskChange, object: databaseURL.standardizedFileURL.path)
        let screen = NSScreen.main?.visibleFrame.size ?? NSSize(width: 1200, height: 800)
        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: min(1180, screen.width - 60), height: min(820, screen.height - 50)),
            styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false
        )
        window.title = "Goofy Mendeleev"
        applyTheme()
        window.delegate = self
        window.collectionBehavior.insert(.fullScreenPrimary)
        window.contentMinSize = NSSize(width: 790, height: 550)
        window.center()
        window.setFrameAutosaveName("TrackerWindow")
        if isLocked { showLockedDisplay() }
        else { showMessage("Opening Goofy Mendeleev…") }
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        if isLocked { enterFullScreen() }
        else { startBackend() }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    func applicationWillTerminate(_ notification: Notification) {
        quitting = true
        DistributedNotificationCenter.default().removeObserver(self)
        authentication?.invalidate()
        lockedDisplay?.setClockActive(false)
        stopBackend()
    }

    func windowDidChangeOcclusionState(_ notification: Notification) {
        lockedDisplay?.setClockActive(window.occlusionState.contains(.visible))
    }

    private func makeMenu() {
        let menu = NSMenu()
        let applicationItem = NSMenuItem()
        let applicationMenu = NSMenu()
        applicationMenu.addItem(withTitle: "Open Data Folder", action: #selector(openDataFolder), keyEquivalent: "").target = self
        applicationMenu.addItem(.separator())
        applicationMenu.addItem(withTitle: "Quit Goofy Mendeleev", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        applicationItem.submenu = applicationMenu
        menu.addItem(applicationItem)

        let editItem = NSMenuItem()
        let editMenu = NSMenu(title: "Edit")
        editMenu.addItem(withTitle: "Undo", action: Selector(("undo:")), keyEquivalent: "z")
        editMenu.addItem(.separator())
        editMenu.addItem(withTitle: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        editMenu.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        editMenu.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editItem.submenu = editMenu
        menu.addItem(editItem)

        let viewItem = NSMenuItem()
        let viewMenu = NSMenu(title: "View")
        let lock = viewMenu.addItem(withTitle: isLocked ? "Unlock Display" : "Lock Display",
                                   action: #selector(toggleDisplayLock), keyEquivalent: "l")
        lock.keyEquivalentModifierMask = [.command, .shift]
        lock.target = self
        lockMenuItem = lock
        let fullScreen = viewMenu.addItem(withTitle: "Toggle Full Screen", action: #selector(NSWindow.toggleFullScreen(_:)), keyEquivalent: "f")
        fullScreen.keyEquivalentModifierMask = [.control, .command]
        viewMenu.addItem(.separator())
        viewMenu.addItem(withTitle: "Performance…", action: #selector(showPerformance), keyEquivalent: "").target = self
        viewItem.submenu = viewMenu
        menu.addItem(viewItem)

        let themeItem = NSMenuItem(title: "Theme", action: nil, keyEquivalent: "")
        let themeMenu = NSMenu(title: "Theme")
        themeMenuItems = TrackerTheme.allCases.map { choice in
            let item = themeMenu.addItem(withTitle: choice.rawValue.capitalized, action: #selector(selectTheme(_:)), keyEquivalent: "")
            item.target = self
            item.representedObject = choice.rawValue
            return item
        }
        themeItem.submenu = themeMenu
        menu.addItem(themeItem)
        NSApp.mainMenu = menu
    }

    @objc private func selectTheme(_ item: NSMenuItem) {
        guard let value = item.representedObject as? String, let choice = TrackerTheme(rawValue: value) else { return }
        theme = choice
        UserDefaults.standard.set(choice.rawValue, forKey: Self.themePreference)
        applyTheme()
    }

    private func applyTheme() {
        NSApp.appearance = theme.appearance
        window.backgroundColor = theme.paper
        for item in themeMenuItems { item.state = (item.representedObject as? String) == theme.rawValue ? .on : .off }
        lockedDisplay?.setTheme(theme)
        if let webView {
            setWebThemeScript(webView.configuration.userContentController)
            applyWebTheme(webView)
        }
    }

    private func setWebThemeScript(_ controller: WKUserContentController) {
        controller.removeAllUserScripts()
        controller.addUserScript(WKUserScript(source: "window.goofyNativeTheme = '\(theme.rawValue)'",
                                              injectionTime: .atDocumentStart, forMainFrameOnly: true))
    }

    private func applyWebTheme(_ webView: WKWebView) {
        webView.underPageBackgroundColor = theme.paper
        webView.evaluateJavaScript("document.documentElement.dataset.theme = '\(theme.rawValue)'", completionHandler: nil)
    }

    @objc private func reloadCLITasks(_ notification: Notification) {
        if let lockedDisplay { refreshLockedProgress(lockedDisplay) }
        else if !isLocked { webView?.evaluateJavaScript("window.goofyReloadTasks?.()", completionHandler: nil) }
    }

    @objc private func showPerformance() {
        guard window.attachedSheet == nil else { return }
        let first = hostCPUSample()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
            guard let self, !self.quitting, self.window.attachedSheet == nil else { return }
            let second = hostCPUSample()
            let usage: String
            if let first, let second {
                let busy = second.busy &- first.busy
                let total = second.total &- first.total
                usage = total > 0 ? (Double(busy) / Double(total)).formatted(.percent.precision(.fractionLength(0))) : "Unavailable"
            } else { usage = "Unavailable" }
            let alert = NSAlert()
            alert.messageText = "Mac Performance"
            let mode = self.isLocked ? "Locked display · dashboard server off" : "Dashboard · local server \(self.backend?.isRunning == true ? "running" : "off")"
            alert.informativeText = "System CPU: \(usage)\n\(mode)"
            alert.addButton(withTitle: "Done")
            alert.addButton(withTitle: "Open Activity Monitor")
            alert.beginSheetModal(for: self.window) { response in
                if response == .alertSecondButtonReturn {
                    NSWorkspace.shared.open(URL(fileURLWithPath: "/System/Applications/Utilities/Activity Monitor.app"))
                }
            }
        }
    }

    private var databaseURL: URL {
        let environment = ProcessInfo.processInfo.environment
        if let path = environment["GOOFY_DB_PATH"], !path.isEmpty {
            return URL(fileURLWithPath: (path as NSString).expandingTildeInPath)
        }
        return FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/Goofy Mendeleev/tracker.db")
    }

    @objc private func openDataFolder() {
        guard !isLocked else { return }
        NSWorkspace.shared.open(databaseURL.deletingLastPathComponent())
    }

    func validateMenuItem(_ item: NSMenuItem) -> Bool {
        if item.action == #selector(openDataFolder) { return !isLocked }
        if item.action == #selector(toggleDisplayLock) { return authentication == nil }
        return true
    }

    @objc private func toggleDisplayLock() {
        if isLocked { requestUnlock(); return }
        setLocked(true)
        if let sheet = window.attachedSheet { window.endSheet(sheet, returnCode: .cancel) }
        webView?.navigationDelegate = nil
        webView?.uiDelegate = nil
        webView?.stopLoading()
        webView = nil
        showLockedDisplay()
        stopBackend()
        enterFullScreen()
    }

    private func setLocked(_ locked: Bool) {
        isLocked = locked
        UserDefaults.standard.set(locked, forKey: Self.lockPreference)
        lockMenuItem?.title = locked ? "Unlock Display" : "Lock Display"
    }

    private func enterFullScreen() {
        if !window.styleMask.contains(.fullScreen) { window.toggleFullScreen(nil) }
    }

    private func showLockedDisplay() {
        let display = LockedDisplay(theme: theme, target: self, unlock: #selector(requestUnlock))
        lockedDisplay = display
        window.contentView = display
        display.setClockActive(window.occlusionState.contains(.visible))
        refreshLockedProgress(display)
    }

    private func refreshLockedProgress(_ display: LockedDisplay) {
        let database = databaseURL
        DispatchQueue.global(qos: .utility).async { [weak self, weak display] in
            let value = LockedDisplay.personalProgress(in: database)
            DispatchQueue.main.async {
                guard let self, let display, self.isLocked, self.lockedDisplay === display else { return }
                display.setPersonalProgress(value)
            }
        }
    }

    @objc private func requestUnlock() {
        guard isLocked, authentication == nil else { return }
        let context = LAContext()
        let policy = LAPolicy.deviceOwnerAuthentication
        var error: NSError?
        guard context.canEvaluatePolicy(policy, error: &error) else {
            showUnlockError(error?.localizedDescription ?? "Mac authentication is unavailable.")
            return
        }
        authentication = context
        context.evaluatePolicy(policy, localizedReason: "Unlock your tracker dashboard") { [weak self, weak context] success, error in
            DispatchQueue.main.async {
                guard let self, let context, self.authentication === context, self.isLocked, !self.quitting else { return }
                self.authentication = nil
                if success {
                    self.setLocked(false)
                    self.lockedDisplay?.setClockActive(false)
                    self.lockedDisplay = nil
                    self.showMessage("Opening Goofy Mendeleev…")
                    self.startBackend()
                } else if let error, let code = (error as? LAError)?.code,
                          ![.userCancel, .systemCancel, .appCancel].contains(code) {
                    self.showUnlockError(error.localizedDescription)
                }
            }
        }
    }

    private func showUnlockError(_ detail: String) {
        guard window.attachedSheet == nil else { return }
        let alert = NSAlert()
        alert.messageText = "Could not unlock the display"
        alert.informativeText = detail
        alert.beginSheetModal(for: window)
    }

    private func showMessage(_ title: String, detail: String? = nil) {
        let view = NSView()
        let titleLabel = NSTextField(labelWithString: title)
        titleLabel.font = .systemFont(ofSize: 19, weight: .medium)
        let stack = NSStackView(views: [titleLabel])
        stack.orientation = .vertical
        stack.spacing = 12
        if let detail {
            let label = NSTextField(wrappingLabelWithString: detail)
            label.alignment = .center
            label.textColor = .secondaryLabelColor
            label.preferredMaxLayoutWidth = 430
            stack.addArrangedSubview(label)
        }
        stack.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            stack.centerYAnchor.constraint(equalTo: view.centerYAnchor),
            stack.widthAnchor.constraint(lessThanOrEqualToConstant: 460),
        ])
        window.contentView = view
    }

    private func startBackend() {
        guard !isLocked, !quitting, backend == nil else { return }
        failed = false
        guard let resources = Bundle.main.resourceURL,
              let python = Bundle.main.object(forInfoDictionaryKey: "GoofyPythonPath") as? String,
              FileManager.default.isExecutableFile(atPath: python) else {
            fail("The Python installation used to build this app could not be found. Run the installer again from the source folder.")
            return
        }
        let process = Process()
        let input = Pipe()
        let output = Pipe()
        process.executableURL = URL(fileURLWithPath: python)
        process.currentDirectoryURL = resources
        process.arguments = ["-m", "backend.server", "--port", "0", "--managed"]
        var environment = ProcessInfo.processInfo.environment
        environment["PYTHONPATH"] = resources.appendingPathComponent("vendor").path
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONNOUSERSITE"] = "1"
        process.environment = environment
        process.standardInput = input
        process.standardOutput = output
        process.standardError = FileHandle.standardError
        process.terminationHandler = { [weak self] process in
            DispatchQueue.main.async {
                guard let self, self.backend === process, !self.quitting else { return }
                self.fail("The local server stopped (code \(process.terminationStatus)). Reopen the app, or run ./run.sh from the source folder for details.")
            }
        }
        output.fileHandleForReading.readabilityHandler = { [weak self, weak process] handle in
            let data = handle.availableData
            if data.isEmpty { handle.readabilityHandler = nil }
            else {
                DispatchQueue.main.async {
                    guard let self, let process, self.backend === process else { return }
                    self.receive(data)
                }
            }
        }
        self.backend = process
        self.input = input
        self.output = output
        do {
            try process.run()
        } catch {
            fail(error.localizedDescription)
            return
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 15) { [weak self, weak process] in
            guard let self, let process, self.backend === process, self.home == nil, !self.failed else { return }
            self.fail("The local server did not respond. Reopen the app, or run ./run.sh from the source folder for details.")
        }
    }

    private func receive(_ data: Data) {
        guard home == nil, !failed, !isLocked else { return }
        readiness.append(data)
        if let newline = readiness.firstIndex(of: 10) {
            let line = String(decoding: readiness[..<newline], as: UTF8.self)
            guard line.hasPrefix("READY "), let port = Int(line.dropFirst(6)), (1...65535).contains(port),
                  let address = URL(string: "http://127.0.0.1:\(port)/") else {
                fail("The local server returned an unexpected startup response.")
                return
            }
            home = address
            let config = WKWebViewConfiguration()
            config.websiteDataStore = .nonPersistent()
            setWebThemeScript(config.userContentController)
            let webView = WKWebView(frame: .zero, configuration: config)
            webView.underPageBackgroundColor = theme.paper
            self.webView = webView
            webView.navigationDelegate = self
            webView.uiDelegate = self
            window.contentView = webView
            webView.load(URLRequest(url: address))
        } else if readiness.count > 128 {
            fail("The local server returned an unexpected startup response.")
        }
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        guard self.webView === webView else { return }
        applyWebTheme(webView)
    }

    private func stopBackend() {
        let process = backend
        backend = nil
        home = nil
        readiness.removeAll()
        output?.fileHandleForReading.readabilityHandler = nil
        try? input?.fileHandleForWriting.close()
        input = nil
        output = nil
        if let process, process.isRunning { process.terminate() }
    }

    private func fail(_ detail: String) {
        guard !failed, !isLocked else { return }
        failed = true
        stopBackend()
        showMessage("Goofy Mendeleev could not open", detail: detail)
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        let url = navigationAction.request.url
        let local = url?.scheme == "http" && url?.host == home?.host && url?.port == home?.port
        decisionHandler(local ? .allow : .cancel)
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        guard self.webView === webView else { return }
        fail(error.localizedDescription)
    }

    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        guard !isLocked, self.webView === webView else { completionHandler(); return }
        let alert = NSAlert()
        alert.messageText = message
        alert.beginSheetModal(for: window) { _ in completionHandler() }
    }
}

private func hostCPUSample() -> (busy: UInt32, total: UInt32)? {
    var stats = host_cpu_load_info_data_t()
    var count = mach_msg_type_number_t(MemoryLayout<host_cpu_load_info_data_t>.size / MemoryLayout<integer_t>.size)
    let host = mach_host_self()
    defer { mach_port_deallocate(mach_task_self_, host) }
    let result = withUnsafeMutablePointer(to: &stats) { pointer in
        pointer.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
            host_statistics(host, HOST_CPU_LOAD_INFO, $0, &count)
        }
    }
    guard result == KERN_SUCCESS else { return nil }
    let busy = stats.cpu_ticks.0 &+ stats.cpu_ticks.1 &+ stats.cpu_ticks.3
    return (busy, busy &+ stats.cpu_ticks.2)
}

if CommandLine.arguments.dropFirst().first == "--cli" {
    guard let resources = Bundle.main.resourceURL,
          let python = Bundle.main.object(forInfoDictionaryKey: "GoofyPythonPath") as? String else { exit(1) }
    let arguments = Array(CommandLine.arguments.dropFirst(2))
    let process = Process()
    process.executableURL = URL(fileURLWithPath: python)
    var environment = ProcessInfo.processInfo.environment
    let database = environment["GOOFY_DB_PATH"].flatMap { $0.isEmpty ? nil : $0 }
        .map { URL(fileURLWithPath: ($0 as NSString).expandingTildeInPath).standardizedFileURL.path }
        ?? FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support/Goofy Mendeleev/tracker.db").path
    environment["GOOFY_DB_PATH"] = database
    environment["PYTHONPATH"] = resources.appendingPathComponent("vendor").path
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONNOUSERSITE"] = "1"
    process.environment = environment
    process.currentDirectoryURL = resources
    process.arguments = ["-m", "backend.cli"] + arguments
    do { try process.run() }
    catch {
        FileHandle.standardError.write(Data("Goofy Mendeleev: \(error.localizedDescription)\n".utf8))
        exit(1)
    }
    process.waitUntilExit()
    let words = arguments.filter { $0 != "--json" }
    if process.terminationStatus == 0, words.count >= 2, words[0] == "tasks", ["add", "done"].contains(words[1]) {
        DistributedNotificationCenter.default().post(name: Notification.Name("local.goofy-mendeleev.tasksChanged"),
                                                      object: database, userInfo: nil)
    }
    exit(process.terminationStatus)
}

let app = NSApplication.shared
let delegate = TrackerApp()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
