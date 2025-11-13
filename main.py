"""
JARVIS Neural Core - Complete Desktop AI Assistant
Fully offline, speech-enabled, visually interactive 3D neural orb
"""

import sys
import os
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QFont

# Import all components
from ui_loader import LoadingScreen
from ui_orb import OrbRenderer
from ui_text_overlay import TextOverlay
from terminal_panel import TerminalPanel
from audio_listener import AudioListener
from speech_engine import SpeechEngine
from action_engine import ActionEngine
from brain import Brain
from hotkey_manager import HotkeyManager


class JarvisCore(QMainWindow):
    """Main Jarvis Neural Core window"""
    
    def __init__(self):
        super().__init__()
        print("[JARVIS] Initializing core...")
        
        # Window setup
        self.setWindowTitle("Jarvis Neural Core")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Screen geometry
        screen = QApplication.primaryScreen()
        screen_geo = screen.geometry()
        self.screen_width = screen_geo.width()
        self.screen_height = screen_geo.height()
        
        orb_size = 300
        self.setGeometry(
            (self.screen_width - orb_size) // 2,
            (self.screen_height - orb_size) // 2,
            orb_size,
            orb_size
        )
        
        # Initialize components
        self.orb = OrbRenderer()
        self.setCentralWidget(self.orb)
        
        self.text_overlay = TextOverlay()
        self.terminal_panel = TerminalPanel()
        self.audio_listener = AudioListener()
        self.speech_engine = SpeechEngine()
        self.action_engine = ActionEngine()
        self.brain = Brain()
        self.hotkey_manager = HotkeyManager()
        
        # State
        self.is_listening = False
        self.is_speaking = False
        self.current_state = "idle"
        
        # Connect signals
        self.audio_listener.amplitude_updated.connect(self.on_audio_update)
        self.speech_engine.speech_recognized.connect(self.on_speech_recognized)
        self.speech_engine.tts_started.connect(self.on_tts_started)
        self.hotkey_manager.hotkey_pressed.connect(self.toggle_listening)
        
        # Start background threads
        self._start_audio_thread()
        self._start_speech_thread()
        self.hotkey_manager.start()
        
        # Log
        self.terminal_panel.add_log("Jarvis Neural Core initialized", "INFO")
        self.terminal_panel.add_log("Press Ctrl+Space to activate", "INFO")
        self.terminal_panel.show()
        
        print("[JARVIS] Ready for commands")
    
    def _start_audio_thread(self):
        """Start audio listening in background"""
        self.audio_thread = QThread()
        self.audio_listener.moveToThread(self.audio_thread)
        self.audio_thread.started.connect(self.audio_listener.start)
        self.audio_thread.start()
    
    def _start_speech_thread(self):
        """Start speech engine in background"""
        self.speech_thread = QThread()
        self.speech_engine.moveToThread(self.speech_thread)
        self.speech_thread.started.connect(self.speech_engine.start)
        self.speech_thread.start()
    
    def on_audio_update(self, amplitude):
        """Update orb based on audio level"""
        normalized = min(amplitude / 0.1, 1.0)
        self.orb.set_audio_level(normalized)
    
    def toggle_listening(self):
        """Toggle listening mode"""
        self.is_listening = not self.is_listening
        
        if self.is_listening:
            print("[JARVIS] Listening...")
            self.current_state = "listening"
            self.orb.set_state("listening")
            self.audio_listener.start_listening()
            self.speech_engine.start_recognition()
            self.terminal_panel.set_state("listening")
            self.terminal_panel.add_log("Listening activated", "ACTION")
        else:
            print("[JARVIS] Not listening")
            self.current_state = "idle"
            self.orb.set_state("idle")
            self.audio_listener.stop_listening()
            self.speech_engine.stop_recognition()
            self.terminal_panel.set_state("idle")
            self.terminal_panel.add_log("Listening deactivated", "INFO")
    
    def on_speech_recognized(self, text):
        """Handle recognized speech"""
        print(f"[JARVIS] Heard: {text}")
        self.terminal_panel.add_log(f"Recognized: {text}", "INFO")
        self.process_command(text)
    
    def on_tts_started(self, text):
        """Handle TTS start"""
        self.is_speaking = True
        self.current_state = "speaking"
        self.orb.set_state("speaking")
        self.terminal_panel.set_state("speaking")
        self.text_overlay.show_typing_animation(text)
        self.terminal_panel.add_log(f"Speaking: {text}", "ACTION")
    
    def process_command(self, text):
        """Process user command"""
        self.terminal_panel.add_log(f"Processing: {text}", "INFO")
        
        # Check if it's an action command
        action_keywords = ['open', 'click', 'scroll', 'type', 'volume', 'time', 'date', 
                          'terminal', 'browser', 'editor', 'launch', 'start']
        is_action = any(kw in text.lower() for kw in action_keywords)
        
        if is_action:
            response = self.action_engine.execute(text)
            self.current_state = "executing"
            self.orb.set_state("executing")
            self.terminal_panel.set_state("executing")
        else:
            response = self.brain.process_input(text)
        
        self.speech_engine.speak(response)
        QTimer.singleShot(100, lambda: self.orb.set_state("idle"))
    
    def closeEvent(self, event):
        print("[JARVIS] Shutting down...")
        self.audio_listener.stop()
        self.speech_engine.stop()
        self.audio_thread.quit()
        self.audio_thread.wait()
        self.speech_thread.quit()
        self.speech_thread.wait()
        self.hotkey_manager.stop()
        event.accept()



def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Show loading screen
    loader = LoadingScreen()
    loader.loading_complete.connect(lambda: start_main(app))
    loader.show()
    
    sys.exit(app.exec_())


def start_main(app):
    """Start main window after loading complete"""
    window = JarvisCore()
    window.show()


if __name__ == "__main__":
    main()
