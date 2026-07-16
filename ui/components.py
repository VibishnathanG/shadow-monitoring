from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from charts.sparkline import Sparkline
from ui.themes.style import THEME_DARK

class ClickableLabel(QLabel):
    clicked = Signal()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

class MetricCard(QFrame):
    def __init__(self, title, accent_color=None, show_progress=False, show_sparkline=False, sparkline_max=100.0, parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.setProperty("class", "MetricCard")
        
        self.accent_color = accent_color or THEME_DARK["accent_cyan"]
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(6)
        
        # 1. Header Layout (Title + Detail/Value right-aligned)
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("CardTitle")
        title_font = QFont(THEME_DARK["font_family"])
        title_font.setPointSize(9)
        title_font.setWeight(QFont.Weight.Bold)
        self.lbl_title.setFont(title_font)
        
        self.lbl_meta = QLabel("")
        self.lbl_meta.setObjectName("CardMeta")
        meta_font = QFont(THEME_DARK["font_family"])
        meta_font.setPointSize(8)
        self.lbl_meta.setFont(meta_font)
        self.lbl_meta.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.header_layout.addWidget(self.lbl_title)
        self.header_layout.addWidget(self.lbl_meta)
        self.layout.addLayout(self.header_layout)
        
        # 2. Main Value / Body Layout
        self.body_layout = QHBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_value = QLabel("--")
        self.lbl_value.setObjectName("CardValue")
        val_font = QFont(THEME_DARK["font_family"])
        val_font.setPointSize(13)
        val_font.setWeight(QFont.Weight.Bold)
        self.lbl_value.setFont(val_font)
        
        self.lbl_extra = QLabel("")
        self.lbl_extra.setObjectName("CardExtra")
        extra_font = QFont(THEME_DARK["font_family"])
        extra_font.setPointSize(9)
        self.lbl_extra.setFont(extra_font)
        self.lbl_extra.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        
        self.body_layout.addWidget(self.lbl_value)
        self.body_layout.addWidget(self.lbl_extra)
        self.layout.addLayout(self.body_layout)
        
        # 3. Optional Progress Bar
        self.progress_bar = None
        if show_progress:
            self.progress_bar = QProgressBar()
            self.progress_bar.setValue(0)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setTextVisible(False)
            
            # Use gradient chunk
            self.progress_bar.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {self.accent_color}, stop:1 #22D3EE);
                }}
            """)
            self.layout.addWidget(self.progress_bar)
            
        # 4. Optional Sparkline
        self.sparkline = None
        if show_sparkline:
            self.sparkline = Sparkline(
                parent=self, 
                line_color=self.accent_color,
                fill_opacity=0.10,
                max_val=sparkline_max
            )
            self.layout.addWidget(self.sparkline)

    def set_value(self, val_str, extra_str=None, meta_str=None):
        self.lbl_value.setText(val_str)
        if extra_str is not None:
            self.lbl_extra.setText(extra_str)
        if meta_str is not None:
            self.lbl_meta.setText(meta_str)

    def update_progress(self, percent, color_hex=None):
        if self.progress_bar:
            self.progress_bar.setValue(int(percent))
            if color_hex:
                if color_hex != getattr(self, '_last_bar_color', None):
                    self._last_bar_color = color_hex
                    self.progress_bar.setStyleSheet(f"""
                        QProgressBar::chunk {{
                            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {color_hex}, stop:1 #22D3EE);
                        }}
                    """)

    def add_sparkline_value(self, val):
        if self.sparkline:
            self.sparkline.add_value(val)
            
    def set_accent_color(self, color_hex):
        if color_hex == self.accent_color:
            return
        self.accent_color = color_hex
        if self.progress_bar:
            self.progress_bar.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {color_hex}, stop:1 #22D3EE);
                }}
            """)
        if self.sparkline:
            self.sparkline.line_color = QColor(color_hex)
            self.sparkline.update()
