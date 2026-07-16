from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from ui.themes.style import THEME_DARK
from ui.components import ClickableLabel

class CompactDashboard(QWidget):
    settings_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CompactContainer")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # 1. Main Horizontal Layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 4, 10, 4)
        self.main_layout.setSpacing(8)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        font_family = THEME_DARK["font_family"]
        lbl_font_bold = QFont(font_family)
        lbl_font_bold.setPointSize(8)
        lbl_font_bold.setWeight(QFont.Weight.Bold)
        
        lbl_font_reg = QFont(font_family)
        lbl_font_reg.setPointSize(8)
        
        self.separators = []
        
        # 2. CPU Stats Container (first visible, clickable for settings)
        self.cpu_widget = QWidget(self)
        cpu_lay = QHBoxLayout(self.cpu_widget)
        cpu_lay.setContentsMargins(0, 0, 0, 0)
        cpu_lay.setSpacing(4)
        
        self.lbl_cpu_val = ClickableLabel("⌬ CPU: --%")
        self.lbl_cpu_val.setObjectName("CompactCpuTitle")
        self.lbl_cpu_val.setFont(lbl_font_bold)
        self.lbl_cpu_val.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_cpu_val.clicked.connect(self.settings_clicked.emit)
        
        self.lbl_cpu_temp = QLabel("")
        self.lbl_cpu_temp.setObjectName("CompactTextSec")
        self.lbl_cpu_temp.setFont(lbl_font_reg)
        
        cpu_lay.addWidget(self.lbl_cpu_val)
        cpu_lay.addWidget(self.lbl_cpu_temp)
        self.main_layout.addWidget(self.cpu_widget)
        
        # 4. GPU Stats Container
        self.gpu_widget = QWidget(self)
        gpu_lay = QHBoxLayout(self.gpu_widget)
        gpu_lay.setContentsMargins(0, 0, 0, 0)
        gpu_lay.setSpacing(4)
        
        self.lbl_gpu_val = QLabel("⧉ GPU: --%")
        self.lbl_gpu_val.setObjectName("CompactGpuTitle")
        self.lbl_gpu_val.setFont(lbl_font_bold)
        
        self.lbl_gpu_meta = QLabel("")
        self.lbl_gpu_meta.setObjectName("CompactTextSec")
        self.lbl_gpu_meta.setFont(lbl_font_reg)
        
        gpu_lay.addWidget(self.lbl_gpu_val)
        gpu_lay.addWidget(self.lbl_gpu_meta)
        
        # Save reference of separators to hide them on collapse
        self.gpu_sep = self.add_separator()
        self.main_layout.addWidget(self.gpu_widget)
        
        # 5. RAM Stats Container
        self.ram_widget = QWidget(self)
        ram_lay = QHBoxLayout(self.ram_widget)
        ram_lay.setContentsMargins(0, 0, 0, 0)
        ram_lay.setSpacing(4)
        
        self.lbl_ram_val = QLabel("⎔ RAM: --%")
        self.lbl_ram_val.setObjectName("CompactRamTitle")
        self.lbl_ram_val.setFont(lbl_font_bold)
        
        self.lbl_ram_extra = QLabel("")
        self.lbl_ram_extra.setObjectName("CompactTextSec")
        self.lbl_ram_extra.setFont(lbl_font_reg)
        
        ram_lay.addWidget(self.lbl_ram_val)
        ram_lay.addWidget(self.lbl_ram_extra)
        
        self.ram_sep = self.add_separator()
        self.main_layout.addWidget(self.ram_widget)
        
        # 6. Network Stats Container
        self.net_widget = QWidget(self)
        net_lay = QHBoxLayout(self.net_widget)
        net_lay.setContentsMargins(0, 0, 0, 0)
        net_lay.setSpacing(6)
        
        self.lbl_net_down = QLabel("↓ 0.0M")
        self.lbl_net_down.setObjectName("CompactNetDown")
        self.lbl_net_down.setFont(lbl_font_bold)
        
        self.lbl_net_up = QLabel("↑ 0.0M")
        self.lbl_net_up.setObjectName("CompactNetUp")
        self.lbl_net_up.setFont(lbl_font_bold)
        
        net_lay.addWidget(self.lbl_net_down)
        net_lay.addWidget(self.lbl_net_up)
        
        self.net_sep = self.add_separator()
        self.main_layout.addWidget(self.net_widget)
        
        # 7. Processes Container
        self.proc_widget = QWidget(self)
        proc_lay = QHBoxLayout(self.proc_widget)
        proc_lay.setContentsMargins(0, 0, 0, 0)
        proc_lay.setSpacing(4)
        
        self.lbl_proc_val = QLabel("✦ --")
        self.lbl_proc_val.setObjectName("CompactTextPri")
        self.lbl_proc_val.setFont(lbl_font_reg)
        proc_lay.addWidget(self.lbl_proc_val)
        
        self.proc_sep = self.add_separator()
        self.main_layout.addWidget(self.proc_widget)
        
        # Error display label (floats at the end if errors occur)
        self.lbl_error = QLabel("")
        err_font = QFont(font_family)
        err_font.setPointSize(8)
        err_font.setWeight(QFont.Weight.Bold)
        self.lbl_error.setFont(err_font)
        self.lbl_error.setStyleSheet("color: #EF4444; padding: 2px; border-radius: 4px; background-color: rgba(239, 68, 68, 0.1);")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.hide()
        self.main_layout.addWidget(self.lbl_error)

    def add_separator(self):
        """Creates and appends a vertical separator to the layout."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: rgba(255, 255, 255, 0.12);")
        self.main_layout.addWidget(sep)
        self.separators.append(sep)
        return sep

    def update_metrics(self, data):
        """Processes live worker metrics and updates compact view labels."""
        # 1. Update CPU
        cpu = data["cpu"]
        cpu_val = cpu["usage"]
        self.lbl_cpu_val.setText(f"⌬ CPU: {cpu_val:.0f}%")
        self.lbl_cpu_temp.setText(f"({cpu['temp']:.0f}°C)" if cpu["temp"] is not None else "")
        
        # 2. Update GPU (Or fallback to Disk Active if inactive)
        gpu = data["gpu"]
        disk = data["disk"]
        if gpu["active"]:
            self.lbl_gpu_val.setText(f"⧉ GPU: {gpu['usage']:.0f}%")
            self.lbl_gpu_meta.setText(f"({gpu['temp']:.0f}°C)" if gpu["temp"] is not None else "")
        else:
            # Fallback label displaying Disk Active%
            self.lbl_gpu_val.setText(f"⛁ DSK: {disk['active_percent']:.0f}%")
            self.lbl_gpu_meta.setText("")
            
        # 3. Update RAM
        ram = data["ram"]
        ram_val = ram["usage"]
        ram_used_gb = ram["used"] / 1024 / 1024 / 1024
        self.lbl_ram_val.setText(f"⎔ RAM: {ram_val:.0f}%")
        self.lbl_ram_extra.setText(f"({ram_used_gb:.1f}G)")
        
        # 4. Update Network
        net = data["net"]
        self.lbl_net_down.setText(f"↓{net['down_speed']:.1f}M")
        self.lbl_net_up.setText(f"↑{net['up_speed']:.1f}M")
        
        # 5. Update Processes
        procs = data["processes"]
        if procs:
            p = procs[0]
            name_trunc = p["name"]
            # Shorten name if too long for overlay row
            if len(name_trunc) > 12:
                name_trunc = name_trunc[:9] + "..."
            self.lbl_proc_val.setText(f"✦ {name_trunc} ({p['cpu']:.0f}%)")
        else:
            self.lbl_proc_val.setText("✦ --")

    def show_error(self, message):
        """Displays error inside the status overlay."""
        # Hide standard widgets during global errors
        self.gpu_widget.hide()
        self.ram_widget.hide()
        self.net_widget.hide()
        self.proc_widget.hide()
        for sep in self.separators:
            sep.hide()
            
        self.lbl_error.setText(f"⚠️ {message}")
        self.lbl_error.show()
        
    def clear_error(self):
        """Hides error overlay and restores normal layout visibility (if not collapsed)."""
        self.lbl_error.setText("")
        self.lbl_error.hide()
        
        # Only restore containers if not collapsed
        # Checking parent collapsed state is done by window controller,
        # but as a safety, restore if the error is cleared.
        parent = self.window()
        if parent and hasattr(parent, 'collapsed') and parent.collapsed:
            return
            
        self.gpu_widget.show()
        self.ram_widget.show()
        self.net_widget.show()
        self.proc_widget.show()
        for sep in self.separators:
            sep.show()
