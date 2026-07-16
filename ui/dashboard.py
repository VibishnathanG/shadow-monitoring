import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMenu, QSystemTrayIcon, QApplication
from PySide6.QtCore import Qt, QPoint, QSize, QEvent
from PySide6.QtGui import QCursor, QAction, QActionGroup

from ui.full import FullDashboard
from ui.compact import CompactDashboard
from ui.themes.style import get_stylesheet
from ui.tray import SystemTrayManager
from utils.win32_utils import set_click_through
from utils.hotkeys import HotkeyManager

class DashboardWindow(QWidget):
    def __init__(self, config_manager, metrics_worker):
        super().__init__()
        self.config = config_manager
        self.worker = metrics_worker
        self.tray = None
        self.hotkeys = None
        
        # Load configurations
        self.always_on_top = self.config.get("always_on_top", True)
        self.click_through = self.config.get("click_through", False)
        self.compact_mode = self.config.get("compact_mode", False)
        self.collapsed = self.config.get("collapsed", False)
        self.opacity = self.config.get("opacity", 0.95)
        
        # Window attributes
        self.setObjectName("DashboardWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        
        # Resize margins and state
        self.resize_margin = 8
        self.is_resizing = False
        self.is_moving = False
        self.resize_edge = None  # "R", "B", "BR"
        self.drag_position = QPoint()
        self.initial_geometry = None
        self.initial_mouse_pos = QPoint()
        
        # Set up UI layouts
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget to switch views
        self.stack = QStackedWidget(self)
        self.view_full = FullDashboard(self)
        self.view_compact = CompactDashboard(self)
        self.stack.addWidget(self.view_full)
        self.stack.addWidget(self.view_compact)
        self.main_layout.addWidget(self.stack)
        
        # Apply active theme on startup
        from ui.themes.style import set_active_theme, get_stylesheet
        saved_theme = self.config.get("theme", "shadow")
        set_active_theme(saved_theme)
        self.setStyleSheet(get_stylesheet())
        
        # Initialize flags
        self.update_window_flags()
        
        # Restore position and size
        self.restore_geometry()
        
        # Connect metrics worker
        self.worker.metrics_updated.connect(self.on_metrics_updated)
        
        # Install global mouse event filters on all child widgets to support dragging/resizing from anywhere
        self.install_mouse_filter(self.view_full)
        self.install_mouse_filter(self.view_compact)

        # Connect left-click settings launchers
        self.view_full.settings_clicked.connect(self.open_settings_menu)
        self.view_compact.settings_clicked.connect(self.open_compact_settings_menu)

        # Connect screen changes to handle monitor disconnection dynamically
        QApplication.instance().screenRemoved.connect(self.handle_screens_changed)

    def init_tray_and_hotkeys(self):
        """Initializes tray and hotkeys once the window is shown and window handle is active."""
        from PySide6.QtWidgets import QSystemTrayIcon
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = SystemTrayManager(self)
        else:
            self.tray = None
        
        # Register global hotkeys (Windows only)
        if sys.platform == "win32":
            self.hotkeys = HotkeyManager(self.winId())
            # Hotkey ID 1: Ctrl+Shift+M (Toggle Visibility)
            # Modifiers: Control (0x02) | Shift (0x04) = 0x06
            # Virtual Key: ord('M') (0x4D)
            self.hotkeys.register(1, HotkeyManager.MOD_CONTROL | HotkeyManager.MOD_SHIFT, 0x4D)
            # Hotkey ID 2: Ctrl+Shift+T (Toggle Click-through)
            # Modifiers: Control (0x02) | Shift (0x04) = 0x06
            # Virtual Key: ord('T') (0x54)
            self.hotkeys.register(2, HotkeyManager.MOD_CONTROL | HotkeyManager.MOD_SHIFT, 0x54)

    def update_window_flags(self):
        """Re-evaluates Qt window flags for frameless windowing."""
        # Using Qt.WindowType.Tool hides the application taskbar icon, sending it to the background
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        
        if self.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
            
        if self.click_through:
            flags |= Qt.WindowType.WindowTransparentForInput
            
        self.setWindowFlags(flags)
        self.setWindowOpacity(self.opacity)
        
        # Apply native Windows click-through if already shown
        if self.isVisible():
            # Standard Qt hide/show to refresh flags
            self.hide()
            self.show()
            
        if sys.platform == "win32" and self.isVisible():
            set_click_through(int(self.winId()), self.click_through)

    def restore_geometry(self):
        """Restores window size and coordinates from configuration."""
        # Switch stacked widget index
        self.stack.setCurrentIndex(1 if self.compact_mode else 0)
        
        # Dimensions
        if self.compact_mode:
            w = self.config.get("window_w_compact", 617)
            h = self.config.get("window_h_compact", 36)
            if w == 250 or h == 180:
                w = 617
                h = 36
            if self.collapsed:
                self.setMinimumSize(114, 36)
                self.setMaximumSize(114, 36)
                self.resize(114, 36)
            else:
                self.setMinimumSize(617, 36)
                self.setMaximumSize(617, 36)
                self.resize(617, 36)
        else:
            w = self.config.get("window_w_full", 304)
            h = self.config.get("window_h_full", 684)
            if self.collapsed:
                self.setMinimumSize(266, 68)
                self.setMaximumSize(570, 68)
                self.resize(w, 68)
            else:
                self.setMinimumSize(266, 190)
                self.setMaximumSize(570, 950)
                self.resize(w, h)
        
        # Coordinates
        x = self.config.get("window_x")
        y = self.config.get("window_y")
        
        # Verify if coordinates are on any active screen
        pos_valid = False
        if x != -1 and y != -1:
            from PySide6.QtCore import QRect
            win_rect = QRect(x, y, w, h)
            for s in QApplication.screens():
                if s.geometry().intersects(win_rect):
                    pos_valid = True
                    break
        
        if pos_valid:
            self.move(x, y)
        else:
            primary_screen = QApplication.primaryScreen()
            if primary_screen:
                screen_geom = primary_screen.availableGeometry()
            else:
                screen_geom = self.screen().availableGeometry()
            self.move(screen_geom.right() - w - 40, screen_geom.top() + 80)
            
        # Collapse state
        if self.collapsed:
            # We don't animate, just set it
            self.set_collapsed_ui(True)

    def handle_screens_changed(self, screen):
        """Triggered when display topology changes (e.g. monitor disconnected)."""
        from PySide6.QtCore import QTimer
        # Wait for OS geometry and layout metrics to stabilize before recalculating
        QTimer.singleShot(500, self.restore_geometry)

    def restore_defaults(self):
        """Resets all app settings, layout, and window coordinates back to default values."""
        self.always_on_top = True
        self.click_through = False
        self.compact_mode = False
        self.collapsed = False
        self.opacity = 0.95
        
        self.config.set("window_x", -1)
        self.config.set("window_y", -1)
        self.config.set("window_w_full", 304)
        self.config.set("window_h_full", 684)
        self.config.set("window_w_compact", 617)
        self.config.set("window_h_compact", 36)
        self.config.set("theme", "shadow")
        self.config.set("always_on_top", True)
        self.config.set("click_through", False)
        self.config.set("compact_mode", False)
        self.config.set("collapsed", False)
        self.config.set("opacity", 0.95)
        self.config.set("refresh_rate_ms", 500, flush=True)
        
        from ui.themes.style import set_active_theme, get_stylesheet
        set_active_theme("shadow")
        self.setStyleSheet(get_stylesheet())
        
        self.update_window_flags()
        self.restore_geometry()
        
        self.worker.update_refresh_rate(500)
        
        if self.tray:
            self.tray.update_menu_states()

    def save_geometry(self):
        """Saves current window coordinates and dimensions to configuration."""
        pos = self.pos()
        self.config.set("window_x", pos.x())
        self.config.set("window_y", pos.y())
        
        if not self.collapsed:
            if self.compact_mode:
                self.config.set("window_w_compact", self.width())
                self.config.set("window_h_compact", self.height())
            else:
                self.config.set("window_w_full", self.width())
                self.config.set("window_h_full", self.height())

    def on_metrics_updated(self, data):
        """Receives data from background thread and updates active layout."""
        if self.compact_mode:
            if data.get("error"):
                self.view_compact.show_error(data["error"])
            else:
                self.view_compact.clear_error()
            self.view_compact.update_metrics(data)
        else:
            if data.get("error"):
                self.view_full.show_error(data["error"])
            else:
                self.view_full.clear_error()
            self.view_full.update_metrics(data)

    def install_mouse_filter(self, widget):
        """Recursively registers the window as an event filter for all child widgets."""
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self)

    def eventFilter(self, watched, event):
        """Intercepts child mouse events and translates them to window move/resize actions."""
        if watched != self:
            # We filter left clicks and double clicks
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
                    # Check edge resize
                    win_pos = self.mapFromGlobal(event.globalPosition().toPoint())
                    margin = self.resize_margin
                    dx = self.width() - win_pos.x()
                    dy = self.height() - win_pos.y()
                    
                    can_resize = not self.collapsed and not self.compact_mode
                    if can_resize and dx < margin and dy < margin:
                        self.is_resizing = True
                        self.resize_edge = "BR"
                    elif can_resize and dx < margin:
                        self.is_resizing = True
                        self.resize_edge = "R"
                    elif can_resize and dy < margin:
                        self.is_resizing = True
                        self.resize_edge = "B"
                    else:
                        if sys.platform == "win32":
                            # Windows native DWM dragging (zero lag, hardware accelerated)
                            from ctypes import windll
                            windll.user32.ReleaseCapture()
                            windll.user32.SendMessageW(int(self.winId()), 0x00A1, 2, 0)
                            return True
                        else:
                            # Qt6 startSystemMove (works on Wayland and X11)
                            window = self.windowHandle()
                            if window:
                                window.startSystemMove()
                            return True
                        
                    self.initial_geometry = self.geometry()
                    self.initial_mouse_pos = event.globalPosition().toPoint()
                    return True
                    
            elif event.type() == QEvent.Type.MouseMove:
                if self.is_resizing:
                    curr_mouse = event.globalPosition().toPoint()
                    delta_x = curr_mouse.x() - self.initial_mouse_pos.x()
                    delta_y = curr_mouse.y() - self.initial_mouse_pos.y()
                    w = self.initial_geometry.width()
                    h = self.initial_geometry.height()
                    
                    if self.resize_edge == "R":
                        self.resize(max(280, w + delta_x), self.height())
                    elif self.resize_edge == "B":
                        self.resize(self.width(), max(200, h + delta_y))
                    elif self.resize_edge == "BR":
                        self.resize(max(280, w + delta_x), max(200, h + delta_y))
                    return True
                elif getattr(self, 'is_moving', False):
                    self.move(event.globalPosition().toPoint() - self.drag_position)
                    return True
                    
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if self.is_resizing or self.is_moving:
                    self.is_resizing = False
                    self.is_moving = False
                    self.resize_edge = None
                    self.save_geometry()
                    self.config.flush()
                    return True
                    
            elif event.type() == QEvent.Type.MouseButtonDblClick:
                if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
                    self.toggle_collapse()
                    return True
        return super().eventFilter(watched, event)

    # --- Mouse Event Resizing & Moving ---
    def mousePressEvent(self, event):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            # Check edge resize
            pos = event.position().toPoint()
            margin = self.resize_margin
            
            # Disable dragging resize if collapsed or in fixed-size compact mode
            can_resize = not self.collapsed and not self.compact_mode
            
            dx = self.width() - pos.x()
            dy = self.height() - pos.y()
            
            if can_resize and dx < margin and dy < margin:
                self.is_resizing = True
                self.resize_edge = "BR"
            elif can_resize and dx < margin:
                self.is_resizing = True
                self.resize_edge = "R"
            elif can_resize and dy < margin:
                self.is_resizing = True
                self.resize_edge = "B"
            else:
                if sys.platform == "win32":
                    # Windows native DWM dragging (zero lag, hardware accelerated)
                    from ctypes import windll
                    windll.user32.ReleaseCapture()
                    windll.user32.SendMessageW(int(self.winId()), 0x00A1, 2, 0)
                    event.accept()
                    return
                else:
                    window = self.windowHandle()
                    if window:
                        window.startSystemMove()
                    event.accept()
                    return
                
            self.initial_geometry = self.geometry()
            self.initial_mouse_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        margin = self.resize_margin
        dx = self.width() - pos.x()
        dy = self.height() - pos.y()
        
        can_resize = not self.collapsed and not self.compact_mode
        
        if self.is_resizing and can_resize:
            curr_mouse = event.globalPosition().toPoint()
            delta_x = curr_mouse.x() - self.initial_mouse_pos.x()
            delta_y = curr_mouse.y() - self.initial_mouse_pos.y()
            
            w = self.initial_geometry.width()
            h = self.initial_geometry.height()
            
            if self.resize_edge == "R":
                self.resize(max(280, w + delta_x), self.height())
            elif self.resize_edge == "B":
                self.resize(self.width(), max(200, h + delta_y))
            elif self.resize_edge == "BR":
                self.resize(max(280, w + delta_x), max(200, h + delta_y))
                
            event.accept()
        elif getattr(self, 'is_moving', False):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            # Set cursor hover shape
            if can_resize and dx < margin and dy < margin:
                self.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
            elif can_resize and dx < margin:
                self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
            elif can_resize and dy < margin:
                self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mouseReleaseEvent(self, event):
        self.is_resizing = False
        self.is_moving = False
        self.resize_edge = None
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.save_geometry()
        self.config.flush()
        event.accept()

    def mouseDoubleClickEvent(self, event):
        """Double click collapses or expands the window."""
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.toggle_collapse()
            event.accept()

    def toggle_collapse(self):
        self.collapsed = not self.collapsed
        self.config.set("collapsed", self.collapsed, flush=True)
        self.set_collapsed_ui(self.collapsed)

    def set_collapsed_ui(self, collapse):
        if collapse:
            # Save normal size
            if not self.compact_mode:
                self.normal_w = self.width()
                self.normal_h = self.height()
                self.view_full.cards_container.hide()
                # Set collapsed height
                self.setMinimumSize(266, 68)
                self.setMaximumSize(570, 68)
                self.resize(self.width(), 68)
            else:
                self.view_compact.gpu_widget.hide()
                self.view_compact.ram_widget.hide()
                self.view_compact.net_widget.hide()
                self.view_compact.proc_widget.hide()
                for sep in self.view_compact.separators:
                    sep.hide()
                self.setMinimumSize(114, 36)
                self.setMaximumSize(114, 36)
                self.resize(114, 36)
        else:
            # Restore normal size
            if not self.compact_mode:
                self.view_full.cards_container.show()
                self.setMinimumSize(266, 190)
                self.setMaximumSize(570, 950)
                self.resize(getattr(self, 'normal_w', 304), getattr(self, 'normal_h', 684))
            else:
                self.view_compact.gpu_widget.show()
                self.view_compact.ram_widget.show()
                self.view_compact.net_widget.show()
                self.view_compact.proc_widget.show()
                for sep in self.view_compact.separators:
                    sep.show()
                self.setMinimumSize(617, 36)
                self.setMaximumSize(617, 36)
                self.resize(617, 36)

    # --- Right Click & Left Click Settings Menu ---
    def contextMenuEvent(self, event):
        self.show_context_menu(QCursor.pos())

    def open_settings_menu(self):
        btn = self.view_full.lbl_app_title
        pos = btn.mapToGlobal(QPoint(0, btn.height()))
        self.show_context_menu(pos)

    def open_compact_settings_menu(self):
        btn = self.view_compact.lbl_cpu_val
        pos = btn.mapToGlobal(QPoint(0, btn.height()))
        self.show_context_menu(pos)

    def _build_context_menu(self):
        """Pre-builds the context menu once. Called from setup_ui_connections."""
        from ui.themes.style import THEMES
        self._ctx_menu = QMenu(self)
        
        # Collapse/Expand
        self._act_collapse = QAction("Collapse", self)
        self._act_collapse.triggered.connect(self.toggle_collapse)
        self._ctx_menu.addAction(self._act_collapse)
        
        self._ctx_menu.addSeparator()
        
        self._act_ontop = QAction("Always On Top", self)
        self._act_ontop.setCheckable(True)
        self._act_ontop.triggered.connect(self.toggle_always_on_top)
        self._ctx_menu.addAction(self._act_ontop)
        
        self._act_thru = QAction("Click Through", self)
        self._act_thru.setCheckable(True)
        self._act_thru.triggered.connect(self.toggle_click_through)
        self._ctx_menu.addAction(self._act_thru)
        
        self._act_compact = QAction("Compact Mode", self)
        self._act_compact.setCheckable(True)
        self._act_compact.triggered.connect(self.toggle_compact_mode)
        self._ctx_menu.addAction(self._act_compact)
        
        self._ctx_menu.addSeparator()
        
        # Opacity
        opacity_menu = self._ctx_menu.addMenu("Opacity")
        self._opacity_group = QActionGroup(self)
        self._opacity_acts = []
        opacities = [(("100%", 1.0)), ("95%", 0.95), ("90%", 0.90), ("80%", 0.80), ("70%", 0.70), ("60%", 0.60), ("50%", 0.50)]
        for label, val in opacities:
            act = QAction(label, self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked=False, v=val: self.change_opacity(v))
            self._opacity_group.addAction(act)
            opacity_menu.addAction(act)
            self._opacity_acts.append((act, val))
        
        # Refresh Rate
        refresh_menu = self._ctx_menu.addMenu("Refresh Rate")
        self._refresh_group = QActionGroup(self)
        self._refresh_acts = []
        rates = [("100ms (Ultra)", 100), ("250ms", 250), ("500ms", 500), ("1.0s", 1000), ("2.0s", 2000)]
        for label, val in rates:
            act = QAction(label, self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked=False, r=val: self.change_refresh_rate(r))
            self._refresh_group.addAction(act)
            refresh_menu.addAction(act)
            self._refresh_acts.append((act, val))
        
        # Theme
        theme_menu = self._ctx_menu.addMenu("Theme")
        self._theme_group = QActionGroup(self)
        self._theme_acts = []
        for key, val in THEMES.items():
            act = QAction(val["name"], self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked=False, k=key: self.change_theme(k))
            self._theme_group.addAction(act)
            theme_menu.addAction(act)
            self._theme_acts.append((act, key))
        
        self._ctx_menu.addSeparator()
        
        act_restore = QAction("Restore to Default", self)
        act_restore.triggered.connect(self.restore_defaults)
        self._ctx_menu.addAction(act_restore)
        
        act_exit = QAction("Exit", self)
        act_exit.triggered.connect(self.close_application)
        self._ctx_menu.addAction(act_exit)

    def show_context_menu(self, global_pos):
        # Build menu on first call (lazy init)
        if not hasattr(self, '_ctx_menu'):
            self._build_context_menu()
        
        # Update checked states (zero allocation, just bool flips)
        self._act_collapse.setText("Expand" if self.collapsed else "Collapse")
        self._act_ontop.setChecked(self.always_on_top)
        self._act_thru.setChecked(self.click_through)
        self._act_compact.setChecked(self.compact_mode)
        
        for act, val in self._opacity_acts:
            act.setChecked(abs(self.opacity - val) < 0.01)
        
        current_rate = self.worker.refresh_rate_ms
        for act, val in self._refresh_acts:
            act.setChecked(current_rate == val)
        
        current_theme = self.config.get("theme", "shadow")
        for act, key in self._theme_acts:
            act.setChecked(current_theme == key)
        
        self._ctx_menu.exec(global_pos)

    # --- Property Controls ---
    def change_theme(self, theme_key):
        """Changes active layout colors and re-applies style rules instantly."""
        from ui.themes.style import set_active_theme, get_stylesheet
        set_active_theme(theme_key)
        self.config.set("theme", theme_key, flush=True)
        self._bg_cache = None
        self.setStyleSheet(get_stylesheet())
        self.view_full.updateGeometry()
        self.view_compact.updateGeometry()
        # if sys.platform == "win32":
        #     from utils.win32_utils import apply_blur_effect
        #     apply_blur_effect(int(self.winId()), dark_mode=(theme_key != "light"))
        self.update()

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.config.set("always_on_top", self.always_on_top, flush=True)
        self.update_window_flags()
        if self.tray:
            self.tray.update_menu_states()

    def toggle_click_through(self):
        self.click_through = not self.click_through
        self.config.set("click_through", self.click_through, flush=True)
        self.update_window_flags()
        if self.tray:
            self.tray.update_menu_states()
            if self.click_through:
                self.tray.tray_icon.showMessage(
                    "Click-Through Enabled",
                    "Shadow is now input-transparent. Press Ctrl+Shift+T or use this system tray icon to disable.",
                    QSystemTrayIcon.MessageIcon.Information,
                    6000
                )

    def toggle_compact_mode(self):
        self.compact_mode = not self.compact_mode
        self.config.set("compact_mode", self.compact_mode)
        
        # Reset collapse when switching mode to avoid height conflicts
        self.collapsed = False
        self.config.set("collapsed", False, flush=True)
        
        self.restore_geometry()
        if self.tray:
            self.tray.update_menu_states()

    def change_opacity(self, opacity_val):
        self.opacity = opacity_val
        self.config.set("opacity", self.opacity, flush=True)
        self.setWindowOpacity(self.opacity)

    def change_refresh_rate(self, rate_ms):
        self.config.set("refresh_rate_ms", rate_ms, flush=True)
        self.worker.update_refresh_rate(rate_ms)

    def show_window(self):
        self.show()
        # Restore focus
        self.raise_()
        self.activateWindow()

    def showEvent(self, event):
        super().showEvent(event)
        # if sys.platform == "win32":
        #     from utils.win32_utils import apply_blur_effect
        #     is_dark = self.config.get("theme", "shadow") != "light"
        #     apply_blur_effect(int(self.winId()), dark_mode=is_dark)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Removed setMask to prevent jagged aliased corners and "white curves"
        pass

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QRadialGradient, QColor, QBrush, QPen, QPixmap
        from PySide6.QtCore import QRectF, Qt
        
        # Initialize or clear pixmap cache if size changed
        if not hasattr(self, '_bg_cache') or self._bg_cache is None or self._bg_cache.size() != self.size():
            self._bg_cache = QPixmap(self.size())
            self._bg_cache.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(self._bg_cache)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            
            theme_key = self.config.get("theme", "shadow").lower()
            rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
            radius = 24.0
            
            from ui.themes.style import THEME_DARK
            
            # Calculate reversed positions for gradients
            if self.compact_mode:
                blue_x = self.width()
                blue_y = self.height()
                orange_x = self.width() * 0.65
                orange_y = 0
            else:
                blue_x = 0
                blue_y = 0
                orange_x = self.width() * 0.35
                orange_y = self.height()
                
            if theme_key == "shadow":
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(6, 7, 12, int(255 * self.opacity))))
                painter.drawRoundedRect(rect, radius, radius)

                blue_glow = QRadialGradient(blue_x, blue_y, max(self.width(), self.height()) * 0.9)
                blue_glow.setColorAt(0.0, QColor(26, 54, 210, int(130 * self.opacity)))
                blue_glow.setColorAt(0.4, QColor(15, 25, 90, int(60 * self.opacity)))
                blue_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
                painter.setBrush(QBrush(blue_glow))
                painter.drawRoundedRect(rect, radius, radius)
                
                orange_glow = QRadialGradient(orange_x, orange_y, max(self.width(), self.height()) * 0.8)
                orange_glow.setColorAt(0.0, QColor(245, 120, 10, int(90 * self.opacity)))
                orange_glow.setColorAt(0.4, QColor(217, 70, 239, int(25 * self.opacity)))
                orange_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
                painter.setBrush(QBrush(orange_glow))
                painter.drawRoundedRect(rect, radius, radius)
                
                purple_glow = QRadialGradient(self.width() * 0.5, self.height() * 0.5, max(self.width(), self.height()) * 0.6)
                purple_glow.setColorAt(0.0, QColor(139, 92, 246, int(55 * self.opacity)))
                purple_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
                painter.setBrush(QBrush(purple_glow))
                painter.drawRoundedRect(rect, radius, radius)
                
                border_pen = QPen(QColor(255, 255, 255, int(20 * self.opacity)), 1.5)
                painter.setPen(border_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(rect, radius, radius)
            else:
                # Dynamic generic gradients for other themes
                bg_plain = THEME_DARK.get("window_bg_plain", "rgba(30, 30, 30, 0.95)")
                if bg_plain.startswith("rgba"):
                    parts = [float(p.strip()) for p in bg_plain.replace("rgba(", "").replace(")", "").split(",")]
                    # Ignore the hardcoded alpha from style.py so it's fully opaque at 100% opacity slider
                    base_color = QColor(int(parts[0]), int(parts[1]), int(parts[2]), int(255 * self.opacity))
                else:
                    base_color = QColor(bg_plain)
                    base_color.setAlpha(int(255 * self.opacity))
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(base_color))
                painter.drawRoundedRect(rect, radius, radius)
                
                # Fetch accent colors for dynamic gradient
                c_cyan = QColor(THEME_DARK.get("accent_cyan", "#22D3EE"))
                c_purple = QColor(THEME_DARK.get("accent_purple", "#BD93F9"))
                
                # Glow 1
                glow1 = QRadialGradient(blue_x, blue_y, max(self.width(), self.height()) * 0.9)
                glow1.setColorAt(0.0, QColor(c_cyan.red(), c_cyan.green(), c_cyan.blue(), int(60 * self.opacity)))
                glow1.setColorAt(1.0, QColor(0, 0, 0, 0))
                painter.setBrush(QBrush(glow1))
                painter.drawRoundedRect(rect, radius, radius)
                
                # Glow 2
                glow2 = QRadialGradient(orange_x, orange_y, max(self.width(), self.height()) * 0.8)
                glow2.setColorAt(0.0, QColor(c_purple.red(), c_purple.green(), c_purple.blue(), int(60 * self.opacity)))
                glow2.setColorAt(1.0, QColor(0, 0, 0, 0))
                painter.setBrush(QBrush(glow2))
                painter.drawRoundedRect(rect, radius, radius)
                
                border_pen = QPen(QColor(255, 255, 255, int(15 * self.opacity)), 1.0)
                painter.setPen(border_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(rect, radius, radius)
                
            painter.end()

        # Just draw the cached pixmap
        main_painter = QPainter(self)
        main_painter.drawPixmap(0, 0, self._bg_cache)
        main_painter.end()

    def close_application(self):
        # Stop worker thread safely
        self.worker.stop()
        if self.hotkeys:
            self.hotkeys.unregister_all()
        # Save geometry one last time
        self.save_geometry()
        self.config.flush()
        self.close()
        sys.exit(0)

    # --- Windows Native Event Overrides (Hotkeys) ---
    def nativeEvent(self, event_type, message):
        """Captures OS level global hotkeys on Windows."""
        if sys.platform == "win32" and event_type == b"windows_generic_MSG":
            try:
                import ctypes
                from ctypes.wintypes import MSG
                
                # Retrieve the raw struct pointer address from message voidptr
                msg_addr = int(message)
                msg = MSG.from_address(msg_addr)
                
                if msg.message == 0x0312:  # WM_HOTKEY
                    hotkey_id = msg.wParam
                    self.handle_global_hotkey(hotkey_id)
                    return True, 0  # Tell Windows we consumed the message
            except Exception as e:
                print(f"Error parsing native event: {e}")
                
        return super().nativeEvent(event_type, message)

    def handle_global_hotkey(self, hotkey_id):
        """Action handler when global hotkey triggered."""
        if hotkey_id == 1:
            # Ctrl+Shift+M -> Toggle Visibility
            if self.isVisible():
                self.hide()
            else:
                self.show_window()
        elif hotkey_id == 2:
            # Ctrl+Shift+T -> Toggle Click-through
            self.toggle_click_through()
