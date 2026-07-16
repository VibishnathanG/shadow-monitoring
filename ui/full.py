from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QColor
from ui.components import MetricCard, ClickableLabel
from ui.themes.style import THEME_DARK, get_status_color

class FullDashboard(QWidget):
    settings_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MainContainer")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # Main layout (Original spacing and margins)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)
        
        # 1. Header (Time, Date, Refresh Dot)
        self.header_layout = QHBoxLayout()
        
        # Left side: Date and Time
        self.time_date_layout = QVBoxLayout()
        self.lbl_time = QLabel("00:00:00")
        self.lbl_time.setObjectName("TimeLabel")
        time_font = QFont(THEME_DARK["font_family"])
        time_font.setPointSize(15)
        time_font.setWeight(QFont.Weight.Bold)
        self.lbl_time.setFont(time_font)
        
        self.lbl_date = QLabel("YYYY-MM-DD")
        self.lbl_date.setObjectName("DateLabel")
        date_font = QFont(THEME_DARK["font_family"])
        date_font.setPointSize(9)
        self.lbl_date.setFont(date_font)
        
        self.time_date_layout.addWidget(self.lbl_time)
        self.time_date_layout.addWidget(self.lbl_date)
        
        # Right side: Blinking status dot + Title
        self.indicator_layout = QHBoxLayout()
        self.indicator_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.lbl_app_title = ClickableLabel("🪄 SHADOW")
        self.lbl_app_title.setObjectName("ShadowTitleButton")
        self.lbl_app_title.clicked.connect(self.settings_clicked.emit)
        self.lbl_app_title.setCursor(Qt.CursorShape.PointingHandCursor)
        title_font = QFont(THEME_DARK["font_family"], 9, QFont.Weight.Bold)
        self.lbl_app_title.setFont(title_font)
        self.lbl_app_title.setStyleSheet("letter-spacing: 2px;")
        
        self.refresh_dot = QFrame()
        self.refresh_dot.setFixedSize(8, 8)
        self.refresh_dot.setStyleSheet("background-color: #34D399; border-radius: 4px;")
        self.dot_state = True
        
        self.indicator_layout.addWidget(self.lbl_app_title)
        self.indicator_layout.addWidget(self.refresh_dot)
        
        self.header_layout.addLayout(self.time_date_layout)
        self.header_layout.addLayout(self.indicator_layout)
        self.main_layout.addLayout(self.header_layout)
        
        # 2. Container for Cards
        self.cards_container = QWidget(self)
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        
        # 2.1 CPU Card
        self.card_cpu = MetricCard("🧠 CPU", show_progress=True, show_sparkline=True, parent=self)
        self.card_cpu.setObjectName("CardCPU")
        self.cards_layout.addWidget(self.card_cpu)
        
        # 2.2 GPU Card (hides dynamically if not active)
        self.card_gpu = MetricCard("🎮 GPU", show_progress=True, show_sparkline=True, parent=self)
        self.card_gpu.setObjectName("CardGPU")
        self.cards_layout.addWidget(self.card_gpu)
        
        # 2.3 RAM Card
        self.card_ram = MetricCard("💾 MEMORY", show_progress=True, parent=self)
        self.card_ram.setObjectName("CardRAM")
        self.cards_layout.addWidget(self.card_ram)
        
        # 2.4 Disk Card
        self.card_disk = MetricCard("💽 DISK I/O", show_progress=True, parent=self)
        self.card_disk.setObjectName("CardDisk")
        self.cards_layout.addWidget(self.card_disk)
        
        # 2.5 Network Card
        self.card_net = MetricCard("🌐 NETWORK", show_sparkline=True, parent=self)
        self.card_net.setObjectName("CardNet")
        self.cards_layout.addWidget(self.card_net)
        
        # 2.6 Top Processes Card
        self.card_procs = QFrame()
        self.card_procs.setObjectName("MetricCard")
        self.card_procs.setProperty("class", "MetricCard")
        self.procs_layout = QVBoxLayout(self.card_procs)
        self.procs_layout.setContentsMargins(10, 10, 10, 10)
        
        # Process title
        self.lbl_proc_title = QLabel("TOP PROCESSES")
        self.lbl_proc_title.setObjectName("CardTitle")
        proc_title_font = QFont(THEME_DARK["font_family"])
        proc_title_font.setPointSize(9)
        proc_title_font.setWeight(QFont.Weight.Bold)
        self.lbl_proc_title.setFont(proc_title_font)
        self.procs_layout.addWidget(self.lbl_proc_title)
        
        # Processes lines (simple table)
        self.proc_rows = []
        for i in range(3):
            row = QHBoxLayout()
            lbl_name = QLabel("--")
            lbl_name.setObjectName("ProcessNameHeader" if i == 0 else "ProcessNameRow")
            name_font = QFont(THEME_DARK["font_family"])
            name_font.setPointSize(8)
            lbl_name.setFont(name_font)
            
            lbl_cpu = QLabel("--")
            lbl_cpu.setObjectName("ProcessCpuHeader" if i == 0 else "ProcessCpuRow")
            cpu_font = QFont(THEME_DARK["font_family"])
            cpu_font.setPointSize(8)
            cpu_font.setWeight(QFont.Weight.Bold)
            lbl_cpu.setFont(cpu_font)
            lbl_cpu.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            lbl_ram = QLabel("--")
            lbl_ram.setObjectName("ProcessRamHeader" if i == 0 else "ProcessRamRow")
            ram_font = QFont(THEME_DARK["font_family"])
            ram_font.setPointSize(8)
            lbl_ram.setFont(ram_font)
            lbl_ram.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl_ram.setFixedWidth(60)
            
            row.addWidget(lbl_name)
            row.addWidget(lbl_cpu)
            row.addWidget(lbl_ram)
            self.procs_layout.addLayout(row)
            self.proc_rows.append((lbl_name, lbl_cpu, lbl_ram))
            
        self.cards_layout.addWidget(self.card_procs)
        self.main_layout.addWidget(self.cards_container)
        
        # Error display label
        self.lbl_error = QLabel("")
        err_font = QFont(THEME_DARK["font_family"])
        err_font.setPointSize(8)
        err_font.setWeight(QFont.Weight.Bold)
        self.lbl_error.setFont(err_font)
        self.lbl_error.setStyleSheet("color: #EF4444; margin-top: 4px; padding: 4px; border-radius: 4px; background-color: rgba(239, 68, 68, 0.1);")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()
        self.main_layout.addWidget(self.lbl_error)

    def update_metrics(self, data):
        # Update Time/Date
        self.lbl_time.setText(data["time"])
        self.lbl_date.setText(data["date"])
        
        # Skip heavy card updates when collapsed
        if not self.cards_container.isVisible():
            return
        
        # 1. Update CPU (Accent: Soft Violet)
        cpu = data["cpu"]
        cpu_val = cpu["usage"]
        cpu_temp_str = f"🌡 {cpu['temp']:.0f}°C" if cpu["temp"] is not None else ""
        freq_str = f"{cpu['freq']/1000:.2f} GHz" if cpu["freq"] > 0 else ""
        
        self.card_cpu.set_accent_color(THEME_DARK["accent_purple"])
        self.card_cpu.lbl_title.setText(f"🧠 CPU: {cpu['name']}")
        
        self.card_cpu.set_value(
            val_str=f"{cpu_val:.1f}%", 
            extra_str=cpu_temp_str, 
            meta_str=f"{freq_str} ({cpu['cores_logical']} Cores)"
        )
        self.card_cpu.update_progress(cpu_val, THEME_DARK["accent_purple"])
        self.card_cpu.add_sparkline_value(cpu_val)
        
        # 2. Update GPU (Accent: Electric Cyan)
        gpu = data["gpu"]
        if gpu["active"]:
            self.card_gpu.show()
            self.card_gpu.lbl_title.setText(f"🎮 GPU: {gpu['name']}")
            gpu_val = gpu["usage"]
            gpu_temp_str = f"🌡 {gpu['temp']:.0f}°C" if gpu["temp"] is not None else ""
            vram_gb = gpu["vram_used"] / 1024 / 1024 / 1024
            vram_total_gb = gpu["vram_total"] / 1024 / 1024 / 1024
            vram_str = f"{vram_gb:.1f}/{vram_total_gb:.1f} GB" if vram_total_gb > 0 else "--"
            
            gpu_extra = []
            if gpu["power"] is not None:
                gpu_extra.append(f"{gpu['power']:.0f}W")
            if gpu["clock"] is not None:
                gpu_extra.append(f"{gpu['clock']:.0f}MHz")
            gpu_extra_str = " | ".join(gpu_extra)
            
            self.card_gpu.set_accent_color(THEME_DARK["accent_cyan"])
            self.card_gpu.set_value(
                val_str=f"{gpu_val:.1f}%", 
                extra_str=gpu_temp_str, 
                meta_str=f"{vram_str}  {gpu_extra_str}"
            )
            self.card_gpu.update_progress(gpu_val, THEME_DARK["accent_cyan"])
            self.card_gpu.add_sparkline_value(gpu_val)
        else:
            self.card_gpu.hide()
            
        # 3. Update RAM (Accent: Emerald / Mint Green)
        ram = data["ram"]
        ram_used_gb = ram["used"] / 1024 / 1024 / 1024
        ram_total_gb = ram["total"] / 1024 / 1024 / 1024
        ram_avail_gb = ram["available"] / 1024 / 1024 / 1024
        ram_val = ram["usage"]
        
        self.card_ram.set_accent_color(THEME_DARK["color_normal"])
        self.card_ram.set_value(
            val_str=f"{ram_val:.1f}%", 
            extra_str=f"{ram_used_gb:.1f} / {ram_total_gb:.1f} GB", 
            meta_str=f"Avail: {ram_avail_gb:.1f} GB"
        )
        self.card_ram.update_progress(ram_val, THEME_DARK["color_normal"])
        
        # 4. Update Disk (Accent: Warm Amber)
        disk = data["disk"]
        active_val = disk["active_percent"]
        read_speed = disk["read_speed"]
        write_speed = disk["write_speed"]
        
        self.card_disk.set_accent_color(THEME_DARK["accent_magenta"])
        self.card_disk.set_value(
            val_str=f"Active: {active_val:.1f}%", 
            extra_str=f"↓ {read_speed:.1f} MB/s", 
            meta_str=f"↑ {write_speed:.1f} MB/s"
        )
        self.card_disk.update_progress(active_val, THEME_DARK["accent_magenta"])
        
        # 5. Update Network (Accent: Sky Blue)
        net = data["net"]
        down = net["down_speed"]
        up = net["up_speed"]
        
        total_speed = down + up
        if self.card_net.sparkline:
            self.card_net.sparkline.max_val = max(10.0, max(self.card_net.sparkline.history or [10.0]))
        
        self.card_net.set_accent_color(THEME_DARK["accent_blue"])
        self.card_net.set_value(
            val_str=f"↓ {down:.2f} MB/s", 
            extra_str=f"↑ {up:.2f} MB/s", 
            meta_str=f"{net['interface']} ({net['ip']})"
        )
        self.card_net.add_sparkline_value(total_speed)
        
        # 6. Update Top Processes
        procs = data["processes"]
        for idx, (lbl_name, lbl_cpu, lbl_ram) in enumerate(self.proc_rows):
            if idx < len(procs):
                p = procs[idx]
                name_trunc = p["name"]
                if len(name_trunc) > 18:
                    name_trunc = name_trunc[:15] + "..."
                lbl_name.setText(name_trunc)
                lbl_cpu.setText(f"{p['cpu']:.1f}%")
                lbl_ram.setText(f"{p['ram']:.0f} MB")
            else:
                lbl_name.setText("--")
                lbl_cpu.setText("--")
                lbl_ram.setText("--")

    def show_error(self, message):
        self.lbl_error.setText(f"⚠️ Error: {message}")
        self.lbl_error.show()
        
    def clear_error(self):
        self.lbl_error.setText("")
        self.lbl_error.hide()
