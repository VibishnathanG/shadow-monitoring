import sys
from PySide6.QtWidgets import QApplication
from config.manager import ConfigManager
from monitor.worker import MetricsWorker
from ui.dashboard import DashboardWindow
from utils.logger import log as logger

def main():
    logger.info("Starting Shadow System Monitor...")
    
    # 1. Initialize PySide6 QApplication
    from PySide6.QtCore import Qt
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("ShadowSystemMonitor")
    app.setApplicationDisplayName("Shadow System Monitor")
    app.setOrganizationName("Shadow")
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray if window hidden

    # 2. Load configuration manager
    config = ConfigManager()
    logger.info("Configuration loaded.")
    
    # 3. Start background metrics worker
    refresh_rate = config.get("refresh_rate_ms", 500)
    worker = MetricsWorker(refresh_rate_ms=refresh_rate)
    worker.status_message.connect(lambda msg: logger.info(f"[Worker] {msg}"))
    worker.start()
    logger.info("Background metric collection thread started.")

    # 4. Construct floating dashboard window
    window = DashboardWindow(config, worker)
    
    # 5. Show window and initialize native modules (Tray icon and global hotkeys)
    window.show_window()
    window.init_tray_and_hotkeys()
    logger.info("Dashboard UI showing. Native system tray & hotkeys registered.")

    # 5.1 Configure SIGINT (Ctrl+C) handler for clean terminal exits
    import signal
    from PySide6.QtCore import QTimer

    def sigint_handler(*args):
        logger.info("SIGINT (Ctrl+C) captured. Exiting cleanly...")
        window.close_application()

    signal.signal(signal.SIGINT, sigint_handler)

    # Small QTimer prevents Qt from blocking Python's interpreter signal dispatch
    sigint_timer = QTimer()
    sigint_timer.start(300)
    sigint_timer.timeout.connect(lambda: None)

    # 6. Execute Application event loop
    try:
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Application crashed: {e}")
        worker.stop()

if __name__ == "__main__":
    main()
