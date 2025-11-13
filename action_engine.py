"""
Action Engine - Executes system commands and automation tasks
"""

import subprocess
import os
try:
    import pyautogui # type: ignore
    print("[JARVIS] pyautogui installed. Mouse/keyboard actions enabled.")
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    print("[JARVIS] [WARNING] pyautogui not installed. Mouse/keyboard actions will be limited.")
    PYAUTOGUI_AVAILABLE = False

from PyQt5.QtCore import QObject, pyqtSignal
import datetime


class ActionEngine(QObject):
    action_completed = pyqtSignal(str)
    action_failed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.last_action = None
    
    def execute(self, command):
        """Execute a command based on intent"""
        try:
            print(f"[JARVIS] Executing action: {command}")
            command_lower = command.lower()
            
            # App launching
            if 'browser' in command_lower or 'chrome' in command_lower or 'firefox' in command_lower:
                self._open_browser()
                return "Opening browser, sir."
            
            elif 'terminal' in command_lower or 'console' in command_lower:
                self._open_terminal()
                return "Launching terminal, sir."
            
            elif 'code' in command_lower or 'editor' in command_lower or 'vscode' in command_lower:
                self._open_vscode()
                return "Opening code editor, sir."
            
            # System actions
            elif 'time' in command_lower:
                return self._get_time()
            
            elif 'date' in command_lower:
                return self._get_date()
            
            elif 'volume' in command_lower:
                if 'up' in command_lower:
                    self._volume_up()
                    return "Volume increased, sir."
                elif 'down' in command_lower or 'lower' in command_lower:
                    self._volume_down()
                    return "Volume decreased, sir."
                elif 'mute' in command_lower:
                    self._mute_volume()
                    return "Volume muted, sir."
            
            # Mouse/keyboard actions
            elif 'scroll' in command_lower and PYAUTOGUI_AVAILABLE:
                if 'down' in command_lower:
                    pyautogui.scroll(-5)
                    return "Scrolling down, sir."
                elif 'up' in command_lower:
                    pyautogui.scroll(5)
                    return "Scrolling up, sir."
            
            elif 'click' in command_lower and PYAUTOGUI_AVAILABLE:
                pyautogui.click()
                return "Clicked, sir."
            
            elif 'type' in command_lower and PYAUTOGUI_AVAILABLE:
                # Extract text after 'type' keyword
                text_to_type = command_lower.split('type', 1)[1].strip()
                pyautogui.typewrite(text_to_type, interval=0.05)
                return f"Typed {text_to_type}, sir."
            
            elif any(x in command_lower for x in ['scroll', 'click', 'type']) and not PYAUTOGUI_AVAILABLE:
                return "Mouse/keyboard control unavailable. Please install pyautogui."
            
            else:
                return "I'm not sure how to execute that, sir."
        
        except Exception as e:
            print(f"[ERROR] Action execution failed: {e}")
            self.action_failed.emit(str(e))
            return "I apologize, sir. I was unable to complete that action."
    
    def _open_browser(self):
        try:
            subprocess.Popen(['xdg-open', 'https://www.google.com'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            subprocess.Popen(['firefox', 'https://www.google.com'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def _open_terminal(self):
        try:
            subprocess.Popen(['gnome-terminal'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            try:
                subprocess.Popen(['xterm'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                print("[JARVIS] [ERROR] No terminal found")
    
    def _open_vscode(self):
        try:
            subprocess.Popen(['code'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            print("[JARVIS] [ERROR] VS Code not installed")
    
    def _get_time(self):
        now = datetime.datetime.now()
        return f"The time is {now.strftime('%I:%M %p')}, sir."
    
    def _get_date(self):
        today = datetime.datetime.now()
        return f"Today is {today.strftime('%A, %B %d, %Y')}, sir."
    
    def _volume_up(self):
        subprocess.run(['amixer', 'set', 'Master', '5%+'],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def _volume_down(self):
        subprocess.run(['amixer', 'set', 'Master', '5%-'],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def _mute_volume(self):
        subprocess.run(['amixer', 'set', 'Master', 'toggle'],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
