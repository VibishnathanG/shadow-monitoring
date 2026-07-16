import os
import json
from pathlib import Path

DEFAULT_CONFIG = {
    "refresh_rate_ms": 500,
    "opacity": 0.95,
    "always_on_top": True,
    "click_through": False,
    "compact_mode": False,
    "collapsed": False,
    "theme": "shadow",
    "window_x": -1,
    "window_y": -1,
    "window_w_full": 304,
    "window_h_full": 684,
    "window_w_compact": 617,
    "window_h_compact": 36,
}

class ConfigManager:
    def __init__(self):
        import sys
        if sys.platform == "win32":
            appdata = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            self.config_dir = Path(appdata) / "ShadowMonitor"
        else:
            self.config_dir = Path.home() / ".config" / "ShadowMonitor"
            
        self.config_path = self.config_dir / "settings.json"
        self.data = DEFAULT_CONFIG.copy()
        self._dirty = False
        self.load()

    def load(self):
        try:
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    loaded_data = json.load(f)
                    # Merge loaded keys to handle schema updates gracefully
                    for k, v in loaded_data.items():
                        if k in self.data:
                            self.data[k] = v
            else:
                self.save()
        except Exception as e:
            print(f"Error loading configuration: {e}")

    def save(self):
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.data, f, indent=4)
            self._dirty = False
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value, flush=False):
        """Sets a config value in memory. Only writes to disk if flush=True."""
        self.data[key] = value
        self._dirty = True
        if flush:
            self.save()

    def flush(self):
        """Writes pending changes to disk if any exist."""
        if self._dirty:
            self.save()
