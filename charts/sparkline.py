from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath
from PySide6.QtCore import Qt, QPointF
from collections import deque

class Sparkline(QWidget):
    def __init__(self, parent=None, max_points=60, line_color="#00ADB5", fill_opacity=0.10, min_val=0.0, max_val=100.0, auto_scale=False):
        super().__init__(parent)
        self.max_points = max_points
        self.line_color = QColor(line_color)
        self.fill_opacity = fill_opacity
        self.min_val = min_val
        self.max_val = max_val
        self.auto_scale = auto_scale
        self.history = deque(maxlen=max_points)
        
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        # Low height by default, scales dynamically
        self.setMinimumHeight(30)
        self.setMaximumHeight(80)

    def add_value(self, val):
        if val is None:
            val = 0.0
        self.history.append(val)
        self.update()

    def clear(self):
        self.history.clear()
        self.update()

    def paintEvent(self, event):
        if not self.history or len(self.history) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = self.width()
        h = self.height()

        # Find min/max values for scaling
        history_min = min(self.history)
        history_max = max(self.history)
        
        current_min = history_min if self.auto_scale else self.min_val
        current_max = history_max if self.auto_scale else self.max_val
        
        # Avoid division by zero
        val_range = current_max - current_min
        if val_range <= 0:
            val_range = 1.0

        # Calculate coordinates
        pts = []
        dx = w / (self.max_points - 1) if self.max_points > 1 else w
        
        # Shift X coordinates so that the latest value is always on the rightmost edge
        offset_x = w - ((len(self.history) - 1) * dx)
        
        for i, val in enumerate(self.history):
            val = max(current_min, min(current_max, val))
            norm = (val - current_min) / val_range
            x = offset_x + (i * dx)
            y = h - (norm * (h - 6)) - 3 # 3px margin top/bottom
            pts.append(QPointF(x, y))

        if len(pts) < 2:
            painter.end()
            return

        # 1. Draw fill area under the smooth curve
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor(self.line_color.red(), self.line_color.green(), self.line_color.blue(), int(255 * self.fill_opacity)))
        gradient.setColorAt(1, QColor(self.line_color.red(), self.line_color.green(), self.line_color.blue(), 0))
        
        fill_path = QPainterPath()
        fill_path.moveTo(pts[0].x(), h) # Start bottom-left below first point
        fill_path.lineTo(pts[0])        # Move up to first point
        
        for i in range(len(pts) - 1):
            p1 = pts[i]
            p2 = pts[i + 1]
            # Calculate control points for cubic Bezier
            c_dx = (p2.x() - p1.x()) / 2.0
            cp1 = QPointF(p1.x() + c_dx, p1.y())
            cp2 = QPointF(p2.x() - c_dx, p2.y())
            fill_path.cubicTo(cp1, cp2, p2)
            
        fill_path.lineTo(pts[-1].x(), h) # Line down to bottom-right below last point
        fill_path.closeSubpath()
        painter.fillPath(fill_path, QBrush(gradient))

        # 2. Draw smooth Bezier curve line
        line_path = QPainterPath()
        line_path.moveTo(pts[0])
        for i in range(len(pts) - 1):
            p1 = pts[i]
            p2 = pts[i + 1]
            c_dx = (p2.x() - p1.x()) / 2.0
            cp1 = QPointF(p1.x() + c_dx, p1.y())
            cp2 = QPointF(p2.x() - c_dx, p2.y())
            line_path.cubicTo(cp1, cp2, p2)

        # 2.1 Soft neon glow underneath line
        glow_pen = QPen(
            QColor(self.line_color.red(), self.line_color.green(), self.line_color.blue(), 45),
            4.0,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin
        )
        painter.setPen(glow_pen)
        painter.drawPath(line_path)

        # 2.2 Sharp foreground line
        pen = QPen(
            self.line_color,
            1.75,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin
        )
        painter.setPen(pen)
        painter.drawPath(line_path)

        # 3. Draw end indicator dot (neon node point)
        end_pt = pts[-1]
        painter.setPen(Qt.PenStyle.NoPen)
        # Glow outer dot
        glow_color = QColor(self.line_color.red(), self.line_color.green(), self.line_color.blue(), 120)
        painter.setBrush(QBrush(glow_color))
        painter.drawEllipse(end_pt, 4.5, 4.5)
        # Solid center dot
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawEllipse(end_pt, 2.0, 2.0)

        painter.end()
