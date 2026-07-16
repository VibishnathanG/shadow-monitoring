# Shadow Monitor

An elegant, high-performance, frameless system monitoring widget for Windows and Linux. Built with PySide6 and `psutil`, Shadow Monitor provides a stunning dynamic UI with real-time metrics for your CPU, RAM, Disk, Network, and GPU—all while maintaining an incredibly low background footprint.

![Shadow Monitor Preview](placeholder.png)

## Features

- **Beautiful Dynamic Themes**: Ships with Shadow (Default), Obsidian, Dracula, One Dark, and Light themes. Smooth fading, translucency, and radial gradients out of the box.
- **Floating Widget**: Frameless, draggable, and can be pinned "Always On Top".
- **Compact & Full Modes**: Double-click to instantly collapse into a sleek, minimal bar showing just the essentials.
- **Click-Through Mode**: Lock the widget to your desktop so it never interrupts your clicks.
- **Hardware Accelerated**: Zero-lag right-click dragging utilizing native OS window management on Windows.
- **Zero-Stutter Architecture**: Background threads handle heavy metrics (WMI, psutil) so the UI remains butter-smooth.

## Requirements

- **OS**: Windows 10/11 or modern Linux.
- **Python**: 3.10+ (if running from source).
- **No Python Required** if you use the pre-built standalone executable!

## Installation

### Windows User Guide

If you just want to run the application without touching code:
1. Go to the **Releases** tab and download `ShadowMonitor.exe`.
2. Double-click the executable to run it immediately. No installation required.
3. The app will appear on your desktop. Right-click anywhere on the widget to access the settings menu.
4. **Settings & Config**: Your preferences are saved automatically to `%LOCALAPPDATA%\ShadowMonitor\settings.json`.
5. **Logs**: If you encounter issues, logs are stored in `%TEMP%\ShadowMonitor\`.
6. **Uninstall**: Simply delete `ShadowMonitor.exe` and the `%LOCALAPPDATA%\ShadowMonitor\` folder.

### Linux User Guide

Currently, Linux requires running from source (AppImage coming soon):
1. Clone the repository: `git clone https://github.com/yourname/shadow-monitor.git`
2. Run the dev script: `./scripts/run-dev.sh`
3. **Settings & Config**: Saved to `~/.config/ShadowMonitor/settings.json`.
4. **Logs**: Stored in `/tmp/ShadowMonitor/`.

## Developer Guide

### Project Structure

- `app.py` - Application entry point.
- `ui/` - Contains all UI components (`dashboard.py`, `full.py`, `compact.py`, `tray.py`).
- `ui/themes/` - Edit `style.py` to add new themes or modify colors.
- `monitor/` - Contains `worker.py` which tracks system metrics via `psutil`.
- `charts/` - Custom drawn widgets like `sparkline.py`.
- `config/` - Manages `settings.json` saving/loading.
- `scripts/` - CI/CD and developer automation scripts.

### Modifying the App

1. **Adding Widgets**: Add a new `MetricCard` in `ui/full.py` and map it to data from `worker.py`.
2. **Themes**: Add a dictionary entry to `BUILTIN_THEMES` in `ui/themes/style.py`. The gradient engine will automatically adapt.
3. **Debugging**: Logs are highly detailed. Check `%TEMP%/ShadowMonitor/shadow_monitor.log`.

## Building & Packaging

We use `PyInstaller` to bundle the app into a portable executable. 

### Building on Windows
Open PowerShell as Administrator (or standard user) and run:
```powershell
.\scripts\ci.ps1
```
To generate the final release zip/folder, run:
```powershell
.\scripts\release.ps1
```
The compiled executable will be located in the `release\` folder.

### Building on Linux
```bash
./scripts/ci.sh
./scripts/release.sh
```

### Build Optimization
The build scripts automatically:
- Clean old artifacts (removing `__pycache__` and old `.pyc` files).
- Create a fresh `venv`.
- Install dependencies.
- Strip unused modules (like tkinter, xml, pydoc).
- Apply UPX compression if installed on your system.

## Troubleshooting

- **Widget disappeared**: Delete `%LOCALAPPDATA%\ShadowMonitor\settings.json` to reset its coordinates.
- **Anti-virus flag**: Some heuristics flag PyInstaller executables. This is a false positive. You can safely whitelist it or build from source.
- **Logs**: If it won't start, read `%TEMP%\ShadowMonitor\shadow_monitor.log` for Python tracebacks.

## License

MIT License. See `LICENSE` for details.

## Future Roadmap

- macOS Support.
- Custom plugins for individual processes.
- Network port monitoring.
