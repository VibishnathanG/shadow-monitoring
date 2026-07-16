import re

with open("ui/dashboard.py", "r") as f:
    code = f.read()

# 1. Right-Click Drag
code = code.replace("if event.button() == Qt.MouseButton.LeftButton:", "if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):")

# 2. Pixmap Cache & Gradients in paintEvent
old_paint = """    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QRadialGradient, QColor, QBrush, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        theme_key = self.config.get("theme", "shadow").lower()
        from PySide6.QtCore import QRectF
        
        # Use QRectF and 0.5 inset for perfect anti-aliasing on 1px borders
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = 24.0
        
        if theme_key == "shadow":
            # Multi-layer premium gradient: warm amber top-left, golden orange top-center,
            # royal blue bottom-left, midnight navy base, subtle purple haze center.
            # 1. Base dark background
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(6, 7, 12, int(255 * self.opacity))))
            painter.drawRoundedRect(rect, radius, radius)
            
            # Calculate reversed positions for gradients
            if self.compact_mode:
                # Reverse right to left and left to right
                blue_x = self.width()
                blue_y = self.height()
                orange_x = self.width() * 0.65
                orange_y = 0
            else:
                # Reverse up to down and down to up
                blue_x = 0
                blue_y = 0
                orange_x = self.width() * 0.35
                orange_y = self.height()

            # 2. Top-Left Royal Blue Glow (reversed from Bottom-Left)
            blue_glow = QRadialGradient(blue_x, blue_y, max(self.width(), self.height()) * 0.9)
            blue_glow.setColorAt(0.0, QColor(26, 54, 210, int(130 * self.opacity)))
            blue_glow.setColorAt(0.4, QColor(15, 25, 90, int(60 * self.opacity)))
            blue_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(blue_glow))
            painter.drawRoundedRect(rect, radius, radius)
            
            # 3. Bottom-Center Golden Orange Glow (reversed from Top-Center)
            orange_glow = QRadialGradient(orange_x, orange_y, max(self.width(), self.height()) * 0.8)
            orange_glow.setColorAt(0.0, QColor(245, 120, 10, int(90 * self.opacity)))
            orange_glow.setColorAt(0.4, QColor(217, 70, 239, int(25 * self.opacity))) # Subtle purple transition
            orange_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(orange_glow))
            painter.drawRoundedRect(rect, radius, radius)
            
            # 4. Center Subtle Purple Haze Glow
            purple_glow = QRadialGradient(self.width() * 0.5, self.height() * 0.5, max(self.width(), self.height()) * 0.6)
            purple_glow.setColorAt(0.0, QColor(139, 92, 246, int(55 * self.opacity)))
            purple_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(purple_glow))
            painter.drawRoundedRect(rect, radius, radius)
            
            # 5. Draw border
            border_pen = QPen(QColor(255, 255, 255, int(20 * self.opacity)), 1.5)
            painter.setPen(border_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)
        else:
            # Traditional themes fallback using simple backgrounds
            from ui.themes.style import THEME_DARK
            bg_plain = THEME_DARK.get("window_bg_plain", "rgba(30, 30, 30, 0.95)")
            
            # Parse color string
            if bg_plain.startswith("rgba"):
                parts = [float(p.strip()) for p in bg_plain.replace("rgba(", "").replace(")", "").split(",")]
                color = QColor(int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3] * 255 * self.opacity / 0.95))
            else:
                color = QColor(bg_plain)
                color.setAlpha(int(255 * self.opacity))
                
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(rect, radius, radius)
            
            # Draw subtle outline
            border_pen = QPen(QColor(255, 255, 255, int(15 * self.opacity)), 1.0)
            painter.setPen(border_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)
            
        painter.end()"""

new_paint = """    def paintEvent(self, event):
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
                    base_color = QColor(int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3] * 255 * self.opacity / 0.95))
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
        main_painter.end()"""
        
code = code.replace(old_paint, new_paint)

# 3. Change Opacity to reset cache
old_opacity = """    def change_opacity(self, val):
        self.opacity = val
        self.config.set("opacity", val, flush=True)
        self.update()"""
        
new_opacity = """    def change_opacity(self, val):
        self.opacity = val
        self.config.set("opacity", val, flush=True)
        self._bg_cache = None
        self.update()"""
        
code = code.replace(old_opacity, new_opacity)

with open("ui/dashboard.py", "w") as f:
    f.write(code)

