import sys

def set_click_through(hwnd, enabled=True):
    """
    Toggles the click-through property of a window on Windows using native ctypes.
    Fails gracefully on non-Windows platforms.
    """
    if sys.platform != "win32":
        return False
        
    try:
        import ctypes
        user32 = ctypes.windll.user32
        
        # Win32 Constants
        GWL_EXSTYLE = -20
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_LAYERED = 0x00080000
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOZORDER = 0x0004
        SWP_FRAMECHANGED = 0x0020
        SWP_NOACTIVATE = 0x0010
        
        # Get current extended window styles
        current_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        
        if enabled:
            # Add transparent & layered flags
            new_style = current_style | WS_EX_TRANSPARENT | WS_EX_LAYERED
        else:
            # Remove transparent flag (preserve layered for alpha transparency support)
            new_style = current_style & ~WS_EX_TRANSPARENT
            
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        
        # Force window manager update to apply styles instantly
        user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED | SWP_NOACTIVATE
        )
        return True
    except Exception as e:
        print(f"Error setting win32 click-through: {e}")
        return False

def apply_blur_effect(hwnd, dark_mode=True):
    """
    Applies a hardware-accelerated frosted glass composition blur (Acrylic / Mica)
    behind the window using native DWM APIs.
    """
    if sys.platform != "win32":
        return False
        
    try:
        import ctypes
        dwmapi = ctypes.windll.dwmapi
        
        # Check Windows Version
        win_version = sys.getwindowsversion()
        build = win_version.build
        
        # Windows 11 (Build 22000+) supports native backdrop types via DWM
        if win_version.major == 10 and build >= 22000:
            # DWMWA_SYSTEMBACKDROP_TYPE = 38
            # DWMSBT_TRANSLUCENTBACKGROUND = 3 (Acrylic blur)
            attr = 38
            backdrop_type = ctypes.c_int(3)
            dwmapi.DwmSetWindowAttribute(
                hwnd, 
                attr, 
                ctypes.byref(backdrop_type), 
                ctypes.sizeof(backdrop_type)
            )
            
            # Round corners attribute: DWMWA_WINDOW_CORNER_PREFERENCE = 33, DWMWCP_ROUND = 2
            attr_corners = 33
            corner_pref = ctypes.c_int(2)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                attr_corners,
                ctypes.byref(corner_pref),
                ctypes.sizeof(corner_pref)
            )
            
            # Set DWM native border color to dark purple to eliminate OS white outline (DWMWA_BORDER_COLOR = 34)
            attr_border = 34
            border_color = ctypes.c_int(0x00100810)  # Dark purple (0x00BBGGRR)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                attr_border,
                ctypes.byref(border_color),
                ctypes.sizeof(border_color)
            )
            
            # Enable immersive dark mode style borders
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            dark = ctypes.c_int(1 if dark_mode else 0)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                20,
                ctypes.byref(dark),
                ctypes.sizeof(dark)
            )
            return True
            
        # Windows 10 (Build 17134+) supports Acrylic composition via SetWindowCompositionAttribute
        user32 = ctypes.windll.user32
        class ACCENT_POLICY(ctypes.Structure):
            _fields_ = [
                ("AccentState", ctypes.c_int),
                ("AccentFlags", ctypes.c_int),
                ("GradientColor", ctypes.c_int),
                ("AnimationId", ctypes.c_int)
            ]
            
        class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
            _fields_ = [
                ("Attribute", ctypes.c_int),
                ("Data", ctypes.c_void_p),
                ("SizeOfData", ctypes.c_int)
            ]
            
        # ACCENT_ENABLE_ACRYLICBLURBEHIND = 4, AccentFlags = 2 (Draw borders)
        policy = ACCENT_POLICY()
        policy.AccentState = 4
        policy.AccentFlags = 2
        # Alpha masked background color
        policy.GradientColor = 0x20101010 if dark_mode else 0x20f0f0f0
        policy.AnimationId = 0
        
        data = WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute = 19  # WCA_ACCENT_POLICY
        data.Data = ctypes.cast(ctypes.pointer(policy), ctypes.c_void_p)
        data.SizeOfData = ctypes.sizeof(policy)
        
        user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
        return True
    except Exception as e:
        print(f"Error applying win32 blur effect: {e}")
        return False
