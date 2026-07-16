import sys
import os
import time
import traceback
import psutil
import threading
from PySide6.QtCore import QThread, Signal

import warnings
# Silence legacy pynvml deprecation warnings (since we transitioned to nvidia-ml-py)
warnings.simplefilter("ignore", category=FutureWarning)

# Optional GPU libraries
try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False


def shorten_cpu_name(name):
    name = name.replace("Intel(R) Core(TM)", "Core")
    name = name.replace("AMD Ryzen", "Ryzen")
    name = name.replace("CPU @", "@")
    name = name.replace("Processor", "")
    name = name.replace("with Radeon Graphics", "")
    name = name.replace("(TM)", "")
    name = name.replace("(R)", "")
    name = name.replace("8-Core", "")
    name = name.replace("16-Core", "")
    name = " ".join(name.split())
    if " @ " in name:
        name = name.split(" @ ")[0]
    return name

def shorten_gpu_name(name):
    name = name.replace("NVIDIA", "")
    name = name.replace("GeForce", "")
    name = name.replace("Laptop GPU", "")
    name = name.replace("Graphics", "")
    name = name.replace("AMD", "")
    name = name.replace("Radeon", "")
    name = name.replace("(TM)", "")
    name = name.replace("(R)", "")
    name = name.replace("Intel", "")
    name = " ".join(name.split())
    return name

def get_cpu_model_name():
    import sys
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            winreg.CloseKey(key)
            return cpu_name.strip()
        except Exception:
            pass
    elif sys.platform.startswith("linux"):
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            import subprocess
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
        except Exception:
            pass
    return "Intel/AMD Processor"


class MetricsWorker(QThread):
    metrics_updated = Signal(dict)
    status_message = Signal(str)

    def __init__(self, refresh_rate_ms=500):
        super().__init__()
        self.refresh_rate_ms = refresh_rate_ms
        self.running = True
        
        # State variables for delta calculations
        self.prev_time = time.time()
        self.prev_disk_read = 0
        self.prev_disk_write = 0
        self.prev_net_recv = 0
        self.prev_net_sent = 0
        
        # Performance cache and throttling timestamps
        self.process_cache = {}
        self.net_cache_counter = 0
        self.last_proc_update = 0.0
        self.last_disk_net_update = 0.0
        self.cached_top_processes = []
        self.cached_disk_metrics = {"read_speed": 0.0, "write_speed": 0.0, "active_percent": 0.0}
        self.cached_net_metrics = {"down_speed": 0.0, "up_speed": 0.0, "interface": "Unknown", "ip": "127.0.0.1"}
        
        # Cached values
        self.cached_ip = "127.0.0.1"
        self.cached_net_iface = "Unknown"
        self.logical_cores = psutil.cpu_count(logical=True)
        self.physical_cores = psutil.cpu_count(logical=False)
        self.cpu_name = shorten_cpu_name(get_cpu_model_name())
        
        # GPU detection state
        self.nvml_initialized = False
        self.gpu_type = "None"  # "NVIDIA", "AMD", "Intel", "Generic", "None"
        self.gpu_name = "N/A"
        
        # Initialize GPU support
        self._init_gpu()

    def _init_gpu(self):
        """Initializes NVML or detects alternative GPUs."""
        self.gpu_init_error = None
        
        # Check if libraries are missing entirely
        if not NVML_AVAILABLE and not GPUTIL_AVAILABLE:
            self.gpu_init_error = "pynvml and GPUtil libraries are missing. Run pip install -r requirements.txt"
            self.status_message.emit(self.gpu_init_error)

        if sys.platform == "win32":
            # Add standard NVSMI directory to PATH so Windows can locate nvml.dll and nvidia-smi.exe
            pf = os.environ.get("ProgramFiles", "C:\\Program Files")
            nvsmi = os.path.join(pf, "NVIDIA Corporation", "NVSMI")
            if os.path.exists(nvsmi) and nvsmi not in os.environ["PATH"]:
                os.environ["PATH"] += os.path.pathsep + nvsmi

        if NVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.nvml_initialized = True
                self.gpu_type = "NVIDIA"
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name_bytes = pynvml.nvmlDeviceGetName(handle)
                raw_name = name_bytes.decode('utf-8') if isinstance(name_bytes, bytes) else str(name_bytes)
                self.gpu_name = shorten_gpu_name(raw_name)
                self.status_message.emit(f"NVIDIA NVML initialized: {self.gpu_name}")
                return
            except Exception as e:
                self.nvml_initialized = False
                self.gpu_init_error = f"NVML initialization failed: {e}"
                self.status_message.emit(self.gpu_init_error)

        # Fallback to GPUtil
        if GPUTIL_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    self.gpu_type = "NVIDIA"
                    self.gpu_name = shorten_gpu_name(gpus[0].name)
                    self.status_message.emit(f"GPUtil detected: {self.gpu_name}")
                    return
            except Exception as e:
                self.gpu_init_error = f"GPUtil detection failed: {e}"
                self.status_message.emit(self.gpu_init_error)

        # Linux AMD check
        if sys.platform.startswith("linux"):
            if os.path.exists("/sys/class/drm/card0/device/gpu_busy_percent"):
                self.gpu_type = "AMD"
                self.gpu_name = "Radeon"
                self.status_message.emit("AMD Radeon sysfs detected")
                return

        # Windows Generic Video Controller detection (Prioritize Discrete GPUs)
        if sys.platform == "win32":
            try:
                import winreg
                best_type = "None"
                best_name = "N/A"
                
                # Check up to 5 adapter slots in registry to prefer discrete cards
                for i in range(5):
                    path = f"SYSTEM\\CurrentControlSet\\Control\\Class\\{{4d36e968-e325-11ce-bfc1-08002be10318}}\\{i:04d}"
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                            desc, _ = winreg.QueryValueEx(key, "DriverDesc")
                            name = str(desc)
                            gtype = "Generic"
                            if "NVIDIA" in name.upper() or "GEFORCE" in name.upper() or "RTX" in name.upper() or "GTX" in name.upper():
                                gtype = "NVIDIA"
                            elif "AMD" in name.upper() or "RADEON" in name.upper():
                                gtype = "AMD"
                            elif "INTEL" in name.upper():
                                gtype = "Intel"
                                
                            # Take NVIDIA discrete immediately
                            if gtype == "NVIDIA":
                                best_type = gtype
                                best_name = name
                                break
                            elif gtype == "AMD" and best_type in ["None", "Intel", "Generic"]:
                                best_type = gtype
                                best_name = name
                            elif gtype == "Intel" and best_type == "None":
                                best_type = gtype
                                best_name = name
                            elif gtype == "Generic" and best_type == "None":
                                best_type = gtype
                                best_name = name
                    except Exception:
                        continue
                        
                if best_type != "None":
                    self.gpu_type = best_type
                    self.gpu_name = shorten_gpu_name(best_name)
                    self.status_message.emit(f"Windows Registry GPU: {self.gpu_name} ({self.gpu_type})")
                    return
            except Exception:
                pass

        self.status_message.emit("No dedicated GPU detected or libraries missing")

    def run(self):
        # Initialize io baselines
        try:
            disk = psutil.disk_io_counters()
            if disk:
                self.prev_disk_read = disk.read_bytes
                self.prev_disk_write = disk.write_bytes
        except Exception:
            pass

        try:
            net = psutil.net_io_counters()
            if net:
                self.prev_net_recv = net.bytes_recv
                self.prev_net_sent = net.bytes_sent
        except Exception:
            pass

        self.prev_time = time.time()

        # Initial cache load
        self._update_network_meta()

        while self.running:
            start_tick = time.time()
            try:
                metrics = self._collect_all_metrics()
                metrics["error"] = None
                self.metrics_updated.emit(metrics)
            except Exception as e:
                # Emit a dummy metrics dictionary with error info to display in widget
                err_metrics = {
                    "error": str(e),
                    "time": time.strftime("%I:%M:%S %p"),
                    "date": time.strftime("%a, %b %d"),
                    "cpu": {"name": self.cpu_name, "usage": 0.0, "cores_logical": self.logical_cores, "cores_physical": self.physical_cores, "freq": 0.0, "temp": None},
                    "ram": {"used": 0, "available": 0, "total": 1, "usage": 0.0},
                    "disk": {"read_speed": 0.0, "write_speed": 0.0, "active_percent": 0.0},
                    "net": {"down_speed": 0.0, "up_speed": 0.0, "interface": self.cached_net_iface, "ip": self.cached_ip},
                    "gpu": {"name": "N/A", "usage": 0.0, "vram_used": 0.0, "vram_total": 0.0, "vram_percent": 0.0, "temp": None, "power": None, "clock": None, "active": False},
                    "processes": []
                }
                self.metrics_updated.emit(err_metrics)

            # Calculate sleep to preserve refresh rate interval
            elapsed = time.time() - start_tick
            sleep_time = max(0.01, (self.refresh_rate_ms / 1000.0) - elapsed)
            self.msleep(int(sleep_time * 1000))

    def stop(self):
        self.running = False
        if self.nvml_initialized:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass
        self.wait()

    def update_refresh_rate(self, rate_ms):
        self.refresh_rate_ms = rate_ms

    def _collect_all_metrics(self):
        current_time = time.time()

        # 1. CPU Metrics
        cpu_usage = psutil.cpu_percent(interval=None)
        cpu_freq_val = 0.0
        try:
            freq = psutil.cpu_freq()
            if freq:
                cpu_freq_val = freq.current
        except Exception:
            pass

        cpu_temp = self._get_cpu_temp()

        # 2. RAM Metrics
        mem = psutil.virtual_memory()
        ram_total = mem.total
        ram_used = mem.used
        ram_available = mem.available
        ram_usage = mem.percent

        # 3 & 4. Disk & Network Metrics (throttled to 1.0s update interval)
        if current_time - self.last_disk_net_update >= 1.0:
            dt = current_time - self.last_disk_net_update if self.last_disk_net_update > 0 else 1.0
            self.last_disk_net_update = current_time
            
            # Disk Metrics
            disk_read_speed = 0.0
            disk_write_speed = 0.0
            disk_active_percent = 0.0
            try:
                disk = psutil.disk_io_counters()
                if disk:
                    disk_read_speed = max(0.0, (disk.read_bytes - self.prev_disk_read) / dt / 1024 / 1024)
                    disk_write_speed = max(0.0, (disk.write_bytes - self.prev_disk_write) / dt / 1024 / 1024)
                    
                    rt_delta = getattr(disk, 'read_time', 0) - getattr(self, 'prev_disk_read_time', 0)
                    wt_delta = getattr(disk, 'write_time', 0) - getattr(self, 'prev_disk_write_time', 0)
                    
                    self.prev_disk_read_time = getattr(disk, 'read_time', 0)
                    self.prev_disk_write_time = getattr(disk, 'write_time', 0)
                    
                    dt_ms = dt * 1000.0
                    if dt_ms > 0:
                        disk_active_percent = min(100.0, max(0.0, (rt_delta + wt_delta) / dt_ms * 100.0))
                    
                    self.prev_disk_read = disk.read_bytes
                    self.prev_disk_write = disk.write_bytes
            except Exception:
                pass
                
            self.cached_disk_metrics = {
                "read_speed": disk_read_speed,
                "write_speed": disk_write_speed,
                "active_percent": disk_active_percent
            }
            
            # Network Metrics
            net_down_speed = 0.0
            net_up_speed = 0.0
            try:
                net = psutil.net_io_counters()
                if net:
                    net_down_speed = max(0.0, (net.bytes_recv - self.prev_net_recv) / dt / 1024 / 1024)
                    net_up_speed = max(0.0, (net.bytes_sent - self.prev_net_sent) / dt / 1024 / 1024)
                    self.prev_net_recv = net.bytes_recv
                    self.prev_net_sent = net.bytes_sent
            except Exception:
                pass
                
            self.cached_net_metrics = {
                "down_speed": net_down_speed,
                "up_speed": net_up_speed,
                "interface": self.cached_net_iface,
                "ip": self.cached_ip
            }

        # Update cached network meta-data (IP and active interface) every 10 seconds
        self.net_cache_counter += 1
        if self.net_cache_counter >= 20:
            self.net_cache_counter = 0
            self._update_network_meta()
            self.cached_net_metrics["interface"] = self.cached_net_iface
            self.cached_net_metrics["ip"] = self.cached_ip

        # 5. GPU Metrics
        gpu_metrics = self._collect_gpu_metrics()
        gpu_error = gpu_metrics.get("error")

        # 6. Top 3 Processes (throttled to 3.0s update interval)
        if current_time - self.last_proc_update >= 3.0 or not self.cached_top_processes:
            self.last_proc_update = current_time
            self.cached_top_processes = self._collect_top_processes()

        return {
            "error": gpu_error,
            "time": time.strftime("%I:%M:%S %p"),
            "date": time.strftime("%a, %b %d"),
            "cpu": {
                "name": self.cpu_name,
                "usage": cpu_usage,
                "cores_logical": self.logical_cores,
                "cores_physical": self.physical_cores,
                "freq": cpu_freq_val,
                "temp": cpu_temp
            },
            "ram": {
                "used": ram_used,
                "available": ram_available,
                "total": ram_total,
                "usage": ram_usage
            },
            "disk": self.cached_disk_metrics,
            "net": self.cached_net_metrics,
            "gpu": gpu_metrics,
            "processes": self.cached_top_processes
        }

    def _get_cpu_temp(self):
        """Attempts to read the CPU temperature across platforms."""
        # 1. Windows Native Query
        if sys.platform == "win32":
            if not hasattr(self, '_win_temp_tick'):
                self._win_temp_tick = 0
                self._cached_win_temp = None
                self._temp_thread = None
                
            self._win_temp_tick += 1
            
            # Helper function to run in a separate thread
            def fetch_temp_async():
                try:
                    import subprocess
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0
                    
                    cmd = 'powershell -NoProfile -Command "(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature).CurrentTemperature"'
                    res = subprocess.check_output(cmd, shell=True, startupinfo=startupinfo, timeout=1.5, cwd="C:\\").decode().strip()
                    if res:
                        lines = [l.strip() for l in res.split() if l.strip().isdigit()]
                        if lines:
                            celsius = (float(lines[0]) / 10.0) - 273.15
                            if 0 < celsius < 125:
                                self._cached_win_temp = celsius
                                return
                except Exception:
                    pass
                try:
                    import subprocess
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0
                    cmd = 'powershell -NoProfile -Command "(Get-CimInstance -Namespace root/cimv2 -ClassName Win32_PerfFormattedData_Counters_ThermalZoneInformation).Temperature"'
                    res = subprocess.check_output(cmd, shell=True, startupinfo=startupinfo, timeout=1.5, cwd="C:\\").decode().strip()
                    if res:
                        lines = [l.strip() for l in res.split() if l.strip().isdigit()]
                        if lines:
                            celsius = float(lines[0]) - 273.15
                            if 0 < celsius < 125:
                                self._cached_win_temp = celsius
                except Exception:
                    pass

            # Query every 10 ticks (approx 5 seconds) asynchronously
            if self._win_temp_tick >= 10 or (self._cached_win_temp is None and self._win_temp_tick == 1):
                self._win_temp_tick = 0
                if self._temp_thread is None or not self._temp_thread.is_alive():
                    self._temp_thread = threading.Thread(target=fetch_temp_async, daemon=True)
                    self._temp_thread.start()
            
            return self._cached_win_temp

        # 2. Linux / macOS standard query
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return None
            # Search common keys
            for key in ['coretemp', 'cpu_thermal', 'k10temp', 'acpitz', 'nouveau', 'zenpower']:
                if key in temps and temps[key]:
                    # Return the average of all entries under this sensor
                    valid_temps = [t.current for t in temps[key] if t.current > 0]
                    if valid_temps:
                        return sum(valid_temps) / len(valid_temps)
            # Fallback to the first temperature found
            for sensor_list in temps.values():
                valid_temps = [t.current for t in sensor_list if t.current > 0]
                if valid_temps:
                    return sum(valid_temps) / len(valid_temps)
        except Exception:
            pass
        return None

    def _collect_gpu_metrics(self):
        """Collects GPU metrics depending on GPU type."""
        metrics = {
            "name": self.gpu_name,
            "usage": 0.0,
            "vram_used": 0.0,
            "vram_total": 0.0,
            "vram_percent": 0.0,
            "temp": None,
            "power": None,
            "clock": None,
            "active": False,
            "error": None
        }

        if self.gpu_type == "None" or self.gpu_name == "N/A":
            if self.gpu_init_error:
                metrics["error"] = self.gpu_init_error
            return metrics

        metrics["active"] = True

        # NVIDIA GPU collection via NVML
        if self.gpu_type == "NVIDIA" and self.nvml_initialized:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                # Usage
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                metrics["usage"] = float(util.gpu)
                
                # Memory
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                metrics["vram_used"] = float(mem.used)
                metrics["vram_total"] = float(mem.total)
                metrics["vram_percent"] = (metrics["vram_used"] / metrics["vram_total"] * 100.0) if metrics["vram_total"] > 0 else 0.0
                
                # Temperature
                try:
                    metrics["temp"] = float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
                except Exception:
                    pass
                
                # Power (NVML returns mW)
                try:
                    metrics["power"] = float(pynvml.nvmlDeviceGetPowerUsage(handle)) / 1000.0
                except Exception:
                    pass
                
                # Graphics Clock (NVML returns MHz)
                try:
                    metrics["clock"] = float(pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS))
                except Exception:
                    pass
                
                return metrics
            except Exception as e:
                metrics["error"] = f"NVML Query Error: {e}"
                # If NVML fails, fall through to GPUtil

        # NVIDIA GPU collection via GPUtil (fallback)
        if self.gpu_type == "NVIDIA" and GPUTIL_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    metrics["usage"] = gpu.load * 100.0
                    metrics["vram_used"] = gpu.memoryUsed * 1024 * 1024 # GPUtil is in MB
                    metrics["vram_total"] = gpu.memoryTotal * 1024 * 1024
                    metrics["vram_percent"] = gpu.memoryUtil * 100.0
                    metrics["temp"] = gpu.temperature
                    return metrics
            except Exception as e:
                metrics["error"] = f"GPUtil Query Error: {e}"

        # If we got here and have an init error, pass it along
        if self.gpu_type == "NVIDIA":
            if self.gpu_init_error and not metrics.get("error"):
                metrics["error"] = self.gpu_init_error
            return metrics

        # Linux AMD GPU sysfs collection
        if self.gpu_type == "AMD" and sys.platform.startswith("linux"):
            try:
                # Usage
                if os.path.exists("/sys/class/drm/card0/device/gpu_busy_percent"):
                    with open("/sys/class/drm/card0/device/gpu_busy_percent", "r") as f:
                        metrics["usage"] = float(f.read().strip())
                
                # VRAM (in bytes)
                used_vram_path = "/sys/class/drm/card0/device/mem_info_vram_used"
                total_vram_path = "/sys/class/drm/card0/device/mem_info_vram_total"
                if os.path.exists(used_vram_path) and os.path.exists(total_vram_path):
                    with open(used_vram_path, "r") as f:
                        metrics["vram_used"] = float(f.read().strip())
                    with open(total_vram_path, "r") as f:
                        metrics["vram_total"] = float(f.read().strip())
                    metrics["vram_percent"] = (metrics["vram_used"] / metrics["vram_total"] * 100.0) if metrics["vram_total"] > 0 else 0.0
                
                # Temperature
                # Search in hwmon directory
                hwmon_root = "/sys/class/drm/card0/device/hwmon"
                if os.path.exists(hwmon_root):
                    for hwmon in os.listdir(hwmon_root):
                        temp_path = os.path.join(hwmon_root, hwmon, "temp1_input")
                        if os.path.exists(temp_path):
                            with open(temp_path, "r") as f:
                                metrics["temp"] = float(f.read().strip()) / 1000.0  # millidegrees
                            break
                            
                # Power
                if os.path.exists(hwmon_root):
                    for hwmon in os.listdir(hwmon_root):
                        power_path = os.path.join(hwmon_root, hwmon, "power1_average")
                        if not os.path.exists(power_path):
                            power_path = os.path.join(hwmon_root, hwmon, "power1_input")
                        if os.path.exists(power_path):
                            with open(power_path, "r") as f:
                                metrics["power"] = float(f.read().strip()) / 1000000.0  # microwatts to Watts
                            break

                # Clock
                clk_path = "/sys/class/drm/card0/device/pp_dpm_sclk"
                if os.path.exists(clk_path):
                    with open(clk_path, "r") as f:
                        lines = f.readlines()
                        # Typically format is "0: 300Mhz *\n1: 800Mhz\n" with * indicating current active clock
                        for line in lines:
                            if "*" in line:
                                parts = line.split()
                                if len(parts) >= 2:
                                    clk_str = parts[1].replace("Mhz", "").replace("MHz", "")
                                    metrics["clock"] = float(clk_str)
                                break
                return metrics
            except Exception:
                pass

        # Generic Windows GPU fallback using WMI if possible, or dummy active data if no sensors found
        # (This prevents empty/broken layout panels on systems where GPU metrics are inaccessible without administrative privileges)
        if sys.platform == "win32":
            # Set memory stats using psutil or default logic since direct WMI query can be slow.
            # We can mock GPU memory as 0, and usage as 0.
            # However, if it's detected, we can report it as active so the card is drawn.
            pass

        return metrics

    def _update_network_meta(self):
        """Helper to get current active network interface and external/local IP."""
        try:
            # 1. Identify primary interface by checking gateways
            # Since standard psutil does not give gateway, we look for the first interface with a non-loopback IP
            # that is active and has sent/received bytes.
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()
            io = psutil.net_io_counters(pernic=True)
            
            best_iface = "Unknown"
            best_ip = "127.0.0.1"
            max_traffic = -1
            
            for iface, addr_list in addrs.items():
                # Verify interface is UP
                if iface in stats and not stats[iface].isup:
                    continue
                
                # Check for IPv4
                ipv4 = None
                for a in addr_list:
                    if a.family == 2:  # AF_INET
                        ipv4 = a.address
                        break
                
                if not ipv4 or ipv4.startswith("127."):
                    continue
                
                # Check traffic
                if iface in io:
                    traffic = io[iface].bytes_recv + io[iface].bytes_sent
                    if traffic > max_traffic:
                        max_traffic = traffic
                        best_iface = iface
                        best_ip = ipv4
            
            self.cached_net_iface = best_iface
            self.cached_ip = best_ip
        except Exception:
            pass

    def _collect_top_processes(self):
        """Collects top 3 CPU consuming processes with caching and validation."""
        procs = []
        # Querying all processes every 500ms is heavy.
        # So we iterate and query.
        # To avoid overhead: we only fetch names, cpu_percent, and rss memory.
        # We reuse psutil.Process objects from our cache to ensure they track CPU percent over time.
        current_pids = set()
        
        # Limit iteration to avoid holding the lock/thread for too long
        for proc in psutil.process_iter():
            pid = proc.pid
            current_pids.add(pid)
            if pid not in self.process_cache:
                self.process_cache[pid] = proc
                # Initialize cpu_percent on new process object
                try:
                    proc.cpu_percent(interval=None)
                except Exception:
                    pass

        # Remove dead processes from cache
        dead_pids = set(self.process_cache.keys()) - current_pids
        for pid in dead_pids:
            del self.process_cache[pid]

        # Gather CPU percent and Memory RSS for all cached processes
        valid_procs = []
        for pid, proc in list(self.process_cache.items()):
            try:
                # Normalize process CPU percentage by dividing by logical core count (Task Manager standard)
                raw_cpu = proc.cpu_percent(interval=None)
                cpu = min(100.0, raw_cpu / self.logical_cores)
                name = proc.name()
                
                # Skip System Idle Process
                if name.lower() in ["system idle process", "idle", "kernel_task"]:
                    continue
                
                mem_bytes = proc.memory_info().rss
                mem_mb = mem_bytes / (1024 * 1024)
                
                valid_procs.append({
                    "name": name,
                    "cpu": cpu,
                    "ram": mem_mb
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Clean up immediately if process terminates during inspection
                if pid in self.process_cache:
                    del self.process_cache[pid]
            except Exception:
                pass

        # Sort by CPU usage descending
        valid_procs.sort(key=lambda x: x["cpu"], reverse=True)
        return valid_procs[:3]
