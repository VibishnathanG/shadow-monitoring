# Design and Theme Constants for Shadow System Monitor
import os
import json
from pathlib import Path

# 1. Fallback Built-in Theme Palettes in case JSON files are missing
BUILTIN_THEMES = {
    "shadow": {
        "name": "Shadow",
        "window_bg": "background-color: transparent; border-radius: 24px; border: none;",
        "window_bg_plain": "rgba(6, 7, 12, 0.72)",
        "card_bg": "background-color: rgba(255, 255, 255, 0.04); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.08);",
        "card_bg_cpu": "background-color: rgba(255, 255, 255, 0.03); border-radius: 20px; border: 1px solid rgba(189, 147, 249, 0.20);",
        "card_bg_gpu": "background-color: rgba(255, 255, 255, 0.03); border-radius: 20px; border: 1px solid rgba(34, 211, 238, 0.20);",
        "card_bg_ram": "background-color: rgba(255, 255, 255, 0.03); border-radius: 20px; border: 1px solid rgba(52, 211, 153, 0.20);",
        "card_bg_disk": "background-color: rgba(255, 255, 255, 0.03); border-radius: 20px; border: 1px solid rgba(251, 191, 36, 0.20);",
        "card_bg_net": "background-color: rgba(255, 255, 255, 0.03); border-radius: 20px; border: 1px solid rgba(56, 189, 248, 0.20);",
        "card_hover_cpu": "background-color: rgba(255, 255, 255, 0.06); border-radius: 20px; border: 1px solid rgba(189, 147, 249, 0.38);",
        "card_hover_gpu": "background-color: rgba(255, 255, 255, 0.06); border-radius: 20px; border: 1px solid rgba(34, 211, 238, 0.38);",
        "card_hover_ram": "background-color: rgba(255, 255, 255, 0.06); border-radius: 20px; border: 1px solid rgba(52, 211, 153, 0.38);",
        "card_hover_disk": "background-color: rgba(255, 255, 255, 0.06); border-radius: 20px; border: 1px solid rgba(251, 191, 36, 0.38);",
        "card_hover_net": "background-color: rgba(255, 255, 255, 0.06); border-radius: 20px; border: 1px solid rgba(56, 189, 248, 0.38);",
        "text_primary": "#FFFFFF",
        "text_secondary": "#E2E8F0",
        "text_dim": "#94A3B8",
        "color_normal": "#34D399",
        "color_moderate": "#F59E0B",
        "color_warn": "#F97316",
        "color_danger": "#F87171",
        "accent_cyan": "#22D3EE",
        "accent_magenta": "#FBBF24",
        "accent_purple": "#BD93F9",
        "accent_blue": "#38BDF8",
        "menu_sel": "rgba(189, 147, 249, 0.15)",
        "font_family": "Segoe UI, Inter, Arial, sans-serif"
    },
    "obsidian": {
        "name": "Obsidian",
        "window_bg": "background-color: transparent; border-radius: 24px; border: none;",
        "window_bg_plain": "rgba(18, 20, 22, 0.68)",
        "card_bg": "background-color: rgba(28, 32, 35, 0.82); border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.04);",
        "text_primary": "#E8EAED",
        "text_secondary": "#8B9DA4",
        "text_dim": "#5C6B73",
        "color_normal": "#4ADE80",
        "color_moderate": "#FBBF24",
        "color_warn": "#FB923C",
        "color_danger": "#F87171",
        "accent_cyan": "#34D399",
        "accent_magenta": "#A78BFA",
        "accent_purple": "#818CF8",
        "accent_blue": "#38BDF8",
        "menu_sel": "rgba(74, 222, 128, 0.1)",
        "font_family": "Segoe UI, Inter, Arial, sans-serif"
    },
    "dracula": {
        "name": "Dracula",
        "window_bg": "background-color: transparent; border-radius: 24px; border: none;",
        "window_bg_plain": "rgba(40, 42, 54, 0.68)",
        "card_bg": "background-color: rgba(68, 71, 90, 0.80); border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.05);",
        "text_primary": "#F8F8F2",
        "text_secondary": "#FF79C6",
        "text_dim": "#6272A4",
        "color_normal": "#50FA7B",
        "color_moderate": "#F1FA8C",
        "color_warn": "#FFB86C",
        "color_danger": "#FF5555",
        "accent_cyan": "#8BE9FD",
        "accent_magenta": "#FF79C6",
        "accent_purple": "#BD93F9",
        "accent_blue": "#6272A4",
        "menu_sel": "rgba(255, 255, 255, 0.1)",
        "font_family": "Segoe UI, Inter, Arial, sans-serif"
    },
    "onedark": {
        "name": "One Dark",
        "window_bg": "background-color: transparent; border-radius: 24px; border: none;",
        "window_bg_plain": "rgba(33, 37, 43, 0.68)",
        "card_bg": "background-color: rgba(40, 44, 52, 0.50); border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.05);",
        "text_primary": "#ABB2BF",
        "text_secondary": "#98C379",
        "text_dim": "#5C6370",
        "color_normal": "#98C379",
        "color_moderate": "#D19A66",
        "color_warn": "#E5C07B",
        "color_danger": "#E06C75",
        "accent_cyan": "#56B6C2",
        "accent_magenta": "#C678DD",
        "accent_purple": "#C678DD",
        "accent_blue": "#61AFEF",
        "menu_sel": "rgba(97, 175, 239, 0.15)",
        "font_family": "Segoe UI, Inter, Arial, sans-serif"
    },
    "light": {
        "name": "Light Theme",
        "window_bg": "background-color: transparent; border-radius: 24px; border: none;",
        "window_bg_plain": "rgba(245, 245, 247, 0.60)",
        "card_bg": "background-color: rgba(255, 255, 255, 0.85); border-radius: 16px; border: 1px solid rgba(0, 0, 0, 0.06);",
        "text_primary": "#1D1D1F",
        "text_secondary": "#515154",
        "text_dim": "#86868B",
        "color_normal": "#10B981",
        "color_moderate": "#D97706",
        "color_warn": "#EA580C",
        "color_danger": "#DC2626",
        "accent_cyan": "#0891B2",
        "accent_magenta": "#C084FC",
        "accent_purple": "#7C3AED",
        "accent_blue": "#2563EB",
        "menu_sel": "rgba(0, 0, 0, 0.05)",
        "font_family": "Segoe UI, Inter, Arial, sans-serif"
    }
}

THEMES = {}

def load_themes():
    """Dynamically registers JSON themes from the themes/ directory."""
    global THEMES
    THEMES.clear()
    THEMES.update(BUILTIN_THEMES)
    
    app_root = Path(__file__).resolve().parent.parent.parent
    themes_dir = app_root / "themes"
    
    if themes_dir.exists() and themes_dir.is_dir():
        for file in themes_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    theme_data = json.load(f)
                    theme_key = file.stem.lower()
                    THEMES[theme_key] = theme_data
            except Exception as e:
                print(f"Error loading theme JSON {file.name}: {e}")

# Run dynamic theme registry
load_themes()

# Active runtime theme reference (Default is Shadow)
THEME_DARK = dict(THEMES.get("shadow", BUILTIN_THEMES["shadow"]))

def set_active_theme(name):
    """Updates the active THEME_DARK dictionary in-place to restyle all elements dynamically."""
    load_themes()
    name_lower = name.lower()
    if name_lower in THEMES:
        THEME_DARK.clear()
        THEME_DARK.update(THEMES[name_lower])
    return THEME_DARK

def get_status_color(value, normal_thresh=50, moderate_thresh=75, warn_thresh=90):
    """Returns a hex color depending on load value thresholds."""
    if value < normal_thresh:
        return THEME_DARK["color_normal"]
    elif value < moderate_thresh:
        return THEME_DARK["color_moderate"]
    elif value < warn_thresh:
        return THEME_DARK["color_warn"]
    else:
        return THEME_DARK["color_danger"]

def get_stylesheet():
    """Generates the global stylesheet for the widget UI."""
    return f"""
    QWidget {{
        font-family: "{THEME_DARK['font_family']}";
        color: {THEME_DARK['text_primary']};
    }}
    
    #DashboardWindow {{
        background: transparent;
    }}
    
    #MainContainer {{
        background: transparent;
        border: none;
    }}
    
    #CompactContainer {{
        background: transparent;
        border: none;
    }}

    QLabel {{
        border: none;
        background: transparent;
    }}
    
    /* Title Button styles and hovers */
    #ShadowTitleButton {{
        color: {THEME_DARK['accent_cyan']};
    }}
    
    #ShadowTitleButton:hover {{
        color: {THEME_DARK['accent_purple']};
    }}
    
    #CompactTitleButton {{
        color: {THEME_DARK['accent_cyan']};
    }}
    
    #CompactTitleButton:hover {{
        color: {THEME_DARK['accent_purple']};
    }}
    
    /* Styled labels mapped to objectNames */
    QLabel[objectName="TimeLabel"] {{
        color: {THEME_DARK['text_primary']};
    }}
    
    QLabel[objectName="DateLabel"] {{
        color: {THEME_DARK['text_dim']};
    }}
    
    QLabel[objectName="CardTitle"] {{
        color: {THEME_DARK['accent_cyan']};
        font-weight: bold;
    }}
    
    QLabel[objectName="CardMeta"] {{
        color: {THEME_DARK['text_dim']};
    }}
    
    QLabel[objectName="CardValue"] {{
        color: {THEME_DARK['text_primary']};
    }}
    
    QLabel[objectName="CardExtra"] {{
        color: {THEME_DARK['text_dim']};
    }}
    
    QLabel[objectName="ProcessNameHeader"] {{
        color: {THEME_DARK['text_dim']};
    }}
    QLabel[objectName="ProcessCpuHeader"] {{
        color: {THEME_DARK['text_dim']};
    }}
    QLabel[objectName="ProcessRamHeader"] {{
        color: {THEME_DARK['text_dim']};
    }}
    
    QLabel[objectName="ProcessNameRow"] {{
        color: {THEME_DARK['text_primary']};
    }}
    QLabel[objectName="ProcessCpuRow"] {{
        color: {THEME_DARK['accent_cyan']};
    }}
    QLabel[objectName="ProcessRamRow"] {{
        color: {THEME_DARK['accent_blue']};
    }}
    
    /* Compact mode elements */
    QLabel[objectName="CompactTimeLabel"] {{
        color: {THEME_DARK['text_primary']};
    }}
    QLabel[objectName="CompactTextSec"] {{
        color: {THEME_DARK['text_dim']};
    }}
    QLabel[objectName="CompactTextPri"] {{
        color: {THEME_DARK['text_primary']};
    }}
    QLabel[objectName="CompactCpuTitle"] {{
        color: {THEME_DARK['accent_purple']};
    }}
    QLabel[objectName="CompactGpuTitle"] {{
        color: {THEME_DARK['accent_cyan']};
    }}
    QLabel[objectName="CompactRamTitle"] {{
        color: {THEME_DARK['accent_blue']};
    }}
    QLabel[objectName="CompactNetDown"] {{
        color: {THEME_DARK['accent_cyan']};
    }}
    QLabel[objectName="CompactNetUp"] {{
        color: {THEME_DARK['accent_purple']};
    }}
    
    .MetricCard {{
        {THEME_DARK['card_bg']}
    }}
    
    #CardCPU {{
        {THEME_DARK.get('card_bg_cpu', THEME_DARK['card_bg'])}
    }}
    #CardCPU:hover {{
        {THEME_DARK.get('card_hover_cpu', THEME_DARK['card_bg'])}
    }}
    
    #CardGPU {{
        {THEME_DARK.get('card_bg_gpu', THEME_DARK['card_bg'])}
    }}
    #CardGPU:hover {{
        {THEME_DARK.get('card_hover_gpu', THEME_DARK['card_bg'])}
    }}
    
    #CardRAM {{
        {THEME_DARK.get('card_bg_ram', THEME_DARK['card_bg'])}
    }}
    #CardRAM:hover {{
        {THEME_DARK.get('card_hover_ram', THEME_DARK['card_bg'])}
    }}
    
    #CardDisk {{
        {THEME_DARK.get('card_bg_disk', THEME_DARK['card_bg'])}
    }}
    #CardDisk:hover {{
        {THEME_DARK.get('card_hover_disk', THEME_DARK['card_bg'])}
    }}
    
    #CardNet {{
        {THEME_DARK.get('card_bg_net', THEME_DARK['card_bg'])}
    }}
    #CardNet:hover {{
        {THEME_DARK.get('card_hover_net', THEME_DARK['card_bg'])}
    }}
    
    /* Individual card text accent coloring */
    #CardCPU QLabel#CardTitle {{
        color: {THEME_DARK.get('accent_purple', THEME_DARK['text_secondary'])};
    }}
    
    #CardGPU QLabel#CardTitle {{
        color: {THEME_DARK.get('accent_cyan', THEME_DARK['text_secondary'])};
    }}
    
    #CardRAM QLabel#CardTitle {{
        color: {THEME_DARK.get('color_normal', THEME_DARK['text_secondary'])};
    }}
    
    #CardDisk QLabel#CardTitle {{
        color: {THEME_DARK.get('accent_magenta', THEME_DARK['text_secondary'])};
    }}
    
    #CardNet QLabel#CardTitle {{
        color: {THEME_DARK.get('accent_blue', THEME_DARK['text_secondary'])};
    }}
    
    .MetricCard QLabel {{
        border: none;
        background: transparent;
    }}
    
    /* Custom QProgressBar styling */
    QProgressBar {{
        background-color: rgba(255, 255, 255, 0.05);
        border: none;
        border-radius: 6px;
        height: 8px;
        margin-top: 8px;
        margin-bottom: 2px;
    }}
    
    QProgressBar::chunk {{
        border-radius: 6px;
    }}
    
    /* Context menu styling */
    QMenu {{
        background-color: {THEME_DARK['window_bg_plain']};
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 4px 0px;
    }}
    
    QMenu::item {{
        padding: 6px 20px;
        background-color: transparent;
        color: {THEME_DARK['text_primary']};
        border-radius: 6px;
        margin: 2px 6px;
    }}
    
    QMenu::item:selected {{
        background-color: {THEME_DARK['menu_sel']};
        color: {THEME_DARK['text_primary']};
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: rgba(255, 255, 255, 0.08);
        margin: 4px 0px;
    }}
    """
