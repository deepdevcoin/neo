"""
Jarvis Neural Core - Main Entry Point
A desktop holographic neural orb with voice interaction
"""

import sys
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from orb_renderer import NeuralOrbRenderer
from audio_listener import AudioListener
from speech_engine import SpeechEngine


class JarvisWindow(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        
        # Window size and position
        self.resize(400, 400)
        self.move(100, 100)
        
        # Initialize components
        self.orb_renderer = NeuralOrbRenderer(self)
        self.audio_listener = AudioListener()
        self.speech_engine = SpeechEngine()
        
        # State
        self.listening_active = False
        self.current_amplitude = 0.0
        
        # Connect signals
        self.audio_listener.amplitude_changed.connect(self.on_amplitude_changed)
        self.speech_engine.speech_recognized.connect(self.on_speech_recognized)
        
        # Setup hotkey (Ctrl+Space)
        self.toggle_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        self.toggle_shortcut.activated.connect(self.toggle_listening)
        
        # Render timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS
        
        print("🌌 Jarvis Neural Core initialized")
        print("Press Ctrl+Space to toggle listening mode")
        
    def initializeGL(self):
        self.orb_renderer.initialize()
        
    def paintGL(self):
        self.orb_renderer.render(self.current_amplitude, self.listening_active)
        
    def resizeGL(self, w, h):
        self.orb_renderer.resize(w, h)
        
    def on_amplitude_changed(self, amplitude):
        self.current_amplitude = amplitude
        
    def toggle_listening(self):
        self.listening_active = not self.listening_active
        if self.listening_active:
            print("🎤 Listening activated...")
            self.speech_engine.start_listening()
        else:
            print("🔇 Listening deactivated")
            self.speech_engine.stop_listening()
            
    def on_speech_recognized(self, text):
        if text:
            print(f"💬 Recognized: {text}")
            response = self.get_jarvis_response(text)
            print(f"🤖 Jarvis: {response}")
            self.speech_engine.speak(response)
            
    def get_jarvis_response(self, text):
        """Simple response logic - can be enhanced with AI"""
        text_lower = text.lower()
        
        if "hello" in text_lower or "hi" in text_lower:
            return "Hello sir, how may I assist you?"
        elif "time" in text_lower:
            from datetime import datetime
            return f"The time is {datetime.now().strftime('%I:%M %p')}"
        elif "thank" in text_lower:
            return "You're welcome, sir"
        elif "bye" in text_lower or "goodbye" in text_lower:
            return "Goodbye, sir"
        else:
            return "I'm processing your request, sir"
            
    def closeEvent(self, event):
        self.audio_listener.stop()
        self.speech_engine.cleanup()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = JarvisWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()