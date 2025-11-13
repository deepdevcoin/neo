"""
Global Hotkey Manager for Ctrl+Space activation
"""

from PyQt5.QtCore import QObject, pyqtSignal
import threading


class HotkeyManager(QObject):
    hotkey_pressed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.thread = None
        self._ctrl_pressed = False
    
    def start(self):
        """Start hotkey listener"""
        try:
            from pynput import keyboard
            self.running = True
            self.thread = threading.Thread(target=self._listen_hotkey, daemon=True)
            self.thread.start()
        except ImportError:
            print("[JARVIS] [WARNING] pynput not installed. Hotkey support disabled.")
            print("[JARVIS]Install with: pip install pynput")
    
    def _listen_hotkey(self):
        """Listen for Ctrl+Space hotkey"""
        try:
            from pynput import keyboard
            
            def on_press(key):
                try:
                    if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                        self._ctrl_pressed = True
                    elif key == keyboard.Key.space and self._ctrl_pressed:
                        self.hotkey_pressed.emit()
                except AttributeError:
                    pass
            
            def on_release(key):
                try:
                    if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                        self._ctrl_pressed = False
                except AttributeError:
                    pass
            
            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()
        except Exception as e:
            print(f"Hotkey error: {e}")
    
    def stop(self):
        """Stop hotkey listener"""
        self.running = False
