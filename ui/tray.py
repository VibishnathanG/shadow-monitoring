from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PySide6.QtCore import Qt, QObject

def create_tray_icon():
    """Generates a high-contrast monitor glyph icon programmatically."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    
    # Draw bezel
    painter.setPen(QColor("#06B6D4")) # Cyan accent
    painter.setBrush(QColor("#1F2937")) # Dark gray body
    painter.drawRoundedRect(2, 4, 28, 20, 3, 3)
    
    # Draw chart line (heartbeat sparkline inside monitor)
    painter.setPen(QColor("#10B981")) # Emerald green
    painter.drawLine(6, 16, 12, 10)
    painter.drawLine(12, 10, 18, 18)
    painter.drawLine(18, 18, 26, 8)
    
    # Draw stand
    painter.setPen(QColor("#06B6D4"))
    painter.setBrush(QColor("#06B6D4"))
    painter.drawRect(13, 24, 6, 2)
    painter.drawRect(9, 26, 14, 2)
    
    painter.end()
    return QIcon(pixmap)


class SystemTrayManager(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(create_tray_icon())
        self.tray_icon.setToolTip("Shadow Monitor")
        
        self.setup_menu()
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def setup_menu(self):
        self.menu = QMenu()
        
        # Visibility
        self.act_show = QAction("Show Dashboard", self)
        self.act_show.triggered.connect(self.main_window.show_window)
        
        self.act_hide = QAction("Hide Dashboard", self)
        self.act_hide.triggered.connect(self.main_window.hide)
        
        # Window properties
        self.act_always_on_top = QAction("Always On Top", self)
        self.act_always_on_top.setCheckable(True)
        self.act_always_on_top.setChecked(self.main_window.always_on_top)
        self.act_always_on_top.triggered.connect(self.main_window.toggle_always_on_top)
        
        self.act_click_through = QAction("Click Through", self)
        self.act_click_through.setCheckable(True)
        self.act_click_through.setChecked(self.main_window.click_through)
        self.act_click_through.triggered.connect(self.main_window.toggle_click_through)
        
        # Modes
        self.act_compact_mode = QAction("Compact Mode", self)
        self.act_compact_mode.setCheckable(True)
        self.act_compact_mode.setChecked(self.main_window.compact_mode)
        self.act_compact_mode.triggered.connect(self.main_window.toggle_compact_mode)
        
        # Exit
        self.act_exit = QAction("Exit Application", self)
        self.act_exit.triggered.connect(self.main_window.close_application)
        
        # Build menu
        self.menu.addAction(self.act_show)
        self.menu.addAction(self.act_hide)
        self.menu.addSeparator()
        self.menu.addAction(self.act_always_on_top)
        self.menu.addAction(self.act_click_through)
        self.menu.addAction(self.act_compact_mode)
        self.menu.addSeparator()
        self.menu.addAction(self.act_exit)
        
        self.tray_icon.setContextMenu(self.menu)

    def on_tray_activated(self, reason):
        # Double click toggles visibility
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self.main_window.show_window()

    def update_menu_states(self):
        """Syncs the menu checkboxes with the current main window state variables."""
        self.act_always_on_top.setChecked(self.main_window.always_on_top)
        self.act_click_through.setChecked(self.main_window.click_through)
        self.act_compact_mode.setChecked(self.main_window.compact_mode)
