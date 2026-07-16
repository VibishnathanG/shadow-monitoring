import sys

class HotkeyManager:
    # Win32 modifier flags
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_WIN = 0x0008
    MOD_NOREPEAT = 0x4000

    def __init__(self, hwnd=None):
        self.hwnd = hwnd
        self.registered = {}

    def register(self, hotkey_id, modifiers, vk):
        """
        Registers a global hotkey with Windows.
        modifiers: combination of MOD_CONTROL, MOD_SHIFT, etc.
        vk: virtual key code (e.g., ord('M'), ord('T'))
        """
        if sys.platform != "win32" or not self.hwnd:
            return False
            
        try:
            import ctypes
            # BOOL RegisterHotKey(HWND hWnd, int id, UINT fsModifiers, UINT vk)
            result = ctypes.windll.user32.RegisterHotKey(
                int(self.hwnd),
                hotkey_id,
                modifiers | self.MOD_NOREPEAT,
                vk
            )
            if result:
                self.registered[hotkey_id] = (modifiers, vk)
                return True
            else:
                print(f"Failed to register hotkey {hotkey_id}. Error code: {ctypes.windll.kernel32.GetLastError()}")
        except Exception as e:
            print(f"Error registering hotkey {hotkey_id}: {e}")
        return False

    def unregister_all(self):
        """Unregisters all active hotkeys."""
        if sys.platform != "win32" or not self.hwnd:
            return
            
        import ctypes
        for hotkey_id in list(self.registered.keys()):
            try:
                ctypes.windll.user32.UnregisterHotKey(int(self.hwnd), hotkey_id)
            except Exception as e:
                print(f"Error unregistering hotkey {hotkey_id}: {e}")
        self.registered.clear()
