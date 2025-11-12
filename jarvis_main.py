"""
jarvis_main.py
==============
JARVIS Desktop AI Assistant - Iron Man Style

REQUIREMENTS:
pip install PyQt5 TTS soundfile sounddevice

OPTIONAL (Voice & AI):
pip install vosk sounddevice gpt4all

SETUP:
1. Save jarvis_orb.py and jarvis_tts.py in same directory
2. Run: python3 jarvis_main.py

FEATURES:
- Orange/amber holographic orb (Iron Man JARVIS style)
- Coqui TTS with natural male voice
- Talk mode: Centered with energy bars
- Act mode: Moves aside, semi-transparent
- Click orb to activate voice
- Drag to move window
"""

import sys
import json
import threading
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import (Qt, QPropertyAnimation, QEasingCurve, QPoint, 
                          QTimer, pyqtSignal, QObject)
from PyQt5.QtGui import QPainter, QColor

# Import JARVIS orb
from jarvis_orb import JarvisOrb

# Import Coqui TTS
from jarvis_tts import create_tts

# Voice recognition
try:
    from vosk import Model, KaldiRecognizer
    import sounddevice as sd
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

# AI model
try:
    from gpt4all import GPT4All
    GPT4ALL_AVAILABLE = True
except ImportError:
    GPT4ALL_AVAILABLE = False


# ============================================================================
# AI WORKER
# ============================================================================

class AIWorker(QObject):
    """Background AI processing with Coqui TTS."""
    
    response_ready = pyqtSignal(str)
    status_update = pyqtSignal(str)
    speech_started = pyqtSignal()
    speech_ended = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.llm = None
        self.tts = None
        self.vosk_model = None
        self.recognizer = None
        
    def initialize(self):
        """Initialize AI components with Coqui TTS."""
        try:
            self.status_update.emit("INITIALIZING SYSTEMS")
            
            # Initialize Coqui TTS
            self.status_update.emit("LOADING JARVIS VOICE")
            self.tts = create_tts(use_gpu=False)
            
            # Set callbacks
            self.tts.on_start = lambda: self.speech_started.emit()
            self.tts.on_end = lambda: self.speech_ended.emit()
            
            if self.tts.is_available():
                self.status_update.emit("VOICE SYSTEM ONLINE")
            else:
                self.status_update.emit("VOICE SYSTEM UNAVAILABLE")
            
            # Initialize LLM
            if GPT4ALL_AVAILABLE:
                self.status_update.emit("LOADING AI CORE")
                try:
                    self.llm = GPT4All("orca-mini-3b-gguf2-q4_0.gguf")
                    self.status_update.emit("AI CORE OPERATIONAL")
                except:
                    self.status_update.emit("AI CORE UNAVAILABLE")
                    self.llm = None
            
            # Initialize Voice Recognition
            if VOSK_AVAILABLE:
                self.status_update.emit("LOADING VOICE RECOGNITION")
                model_path = Path("vosk-model-small-en-us-0.15")
                if model_path.exists():
                    self.vosk_model = Model(str(model_path))
                    self.recognizer = KaldiRecognizer(self.vosk_model, 16000)
                    self.status_update.emit("VOICE RECOGNITION ONLINE")
                else:
                    self.status_update.emit("VOICE MODEL NOT FOUND")
            
            self.status_update.emit("ALL SYSTEMS OPERATIONAL")
            
        except Exception as e:
            self.status_update.emit(f"ERROR: {str(e)}")
    
    def speak(self, text):
        """Text to speech using Coqui TTS."""
        try:
            if self.tts and self.tts.is_available():
                self.tts.speak(text, blocking=False)
            else:
                print(f"[JARVIS] {text}")
                # Manually trigger callbacks if TTS unavailable
                self.speech_started.emit()
                import time
                time.sleep(len(text) * 0.05)  # Simulate speech duration
                self.speech_ended.emit()
        except Exception as e:
            print(f"TTS Error: {e}")
            self.speech_ended.emit()
    
    def listen(self, duration=5):
        """Voice input."""
        if not self.recognizer:
            return "Voice recognition unavailable"
        
        try:
            self.status_update.emit("LISTENING...")
            
            audio = sd.rec(int(duration * 16000), samplerate=16000, 
                          channels=1, dtype='int16')
            sd.wait()
            
            if self.recognizer.AcceptWaveform(audio.tobytes()):
                result = json.loads(self.recognizer.Result())
                text = result.get('text', '').strip()
                if text:
                    return text
            
            partial = json.loads(self.recognizer.PartialResult())
            text = partial.get('partial', '').strip()
            return text if text else "No input detected"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def process_text(self, user_input):
        """Process with LLM or simple responses."""
        if not self.llm:
            # JARVIS-style responses without AI
            responses = {
                "hello": "Good evening, sir. JARVIS interface active.",
                "hi": "Hello, sir. How may I assist you?",
                "how are you": "All systems operating within normal parameters.",
                "what can you do": "I can process voice commands, provide information, and assist with various tasks.",
                "thank you": "You're welcome, sir.",
                "thanks": "My pleasure, sir.",
                "bye": "Standing by. Call me anytime.",
                "goodbye": "Goodbye, sir. Systems on standby.",
                "status": "All systems nominal. Ready to assist.",
                "report": "Diagnostics complete. All functions operational.",
            }
            
            user_lower = user_input.lower()
            for key in responses:
                if key in user_lower:
                    return responses[key]
            
            return f"Command received: {user_input}. Awaiting AI core for advanced processing."
        
        try:
            self.status_update.emit("PROCESSING...")
            
            prompt = f"You are JARVIS, a sophisticated AI assistant like in Iron Man. Be concise, helpful, and slightly formal. Address the user as 'sir'. Respond in 1-2 sentences max.\n\nUser: {user_input}\nJARVIS:"
            
            response = ""
            for token in self.llm.generate(prompt, max_tokens=100, streaming=True):
                response += token
            
            return response.strip()
            
        except Exception as e:
            return f"Processing error: {str(e)}"


# ============================================================================
# MAIN WINDOW
# ============================================================================

class JarvisAssistant(QWidget):
    """JARVIS desktop assistant with holographic interface."""
    
    def __init__(self):
        super().__init__()
        
        # Frameless transparent window
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # State
        self.current_mode = "idle"
        self.is_listening = False
        self.drag_position = None
        
        # Position states
        self.center_pos = None
        self.side_pos = None
        
        # AI worker
        self.ai_worker = AIWorker()
        
        # Setup
        self.init_ui()
        self.init_ai()
        
    def init_ui(self):
        """Initialize UI with orange theme."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # JARVIS holographic orb
        self.orb = JarvisOrb(self, size=300)
        self.orb.mode_changed.connect(self.on_orb_mode_changed)
        layout.addWidget(self.orb, alignment=Qt.AlignCenter)
        
        # Status display (orange theme)
        self.status_label = QLabel("INITIALIZING", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 179, 71, 255);
                font-size: 13px;
                font-weight: 600;
                font-family: 'Courier New', 'Consolas', monospace;
                background: rgba(20, 10, 5, 220);
                border: 1px solid rgba(255, 140, 0, 120);
                border-radius: 5px;
                padding: 12px 18px;
                letter-spacing: 1px;
            }
        """)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.resize(340, 400)
        
        # Calculate positions
        self.calculate_positions()
        
        # Position animation
        self.pos_animation = QPropertyAnimation(self, b"pos")
        self.pos_animation.setDuration(400)
        self.pos_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.show()
    
    def calculate_positions(self):
        """Calculate center and side positions."""
        screen = QApplication.primaryScreen().geometry()
        
        # Center position
        center_x = (screen.width() - self.width()) // 2
        center_y = 60
        self.center_pos = QPoint(center_x, center_y)
        
        # Side position (top-right)
        side_x = screen.width() - self.width() - 40
        side_y = 40
        self.side_pos = QPoint(side_x, side_y)
        
        # Start at center
        self.move(self.center_pos)
    
    def init_ai(self):
        """Initialize AI worker."""
        self.ai_worker.response_ready.connect(self.handle_response)
        self.ai_worker.status_update.connect(self.update_status)
        self.ai_worker.speech_started.connect(self.on_speech_started)
        self.ai_worker.speech_ended.connect(self.on_speech_ended)
        
        # Start in background
        threading.Thread(target=self.ai_worker.initialize, daemon=True).start()
        
        # Startup greeting
        QTimer.singleShot(4500, self.greet)
    
    def greet(self):
        """JARVIS startup greeting."""
        greeting = "Systems online. Welcome back, sir."
        self.speak_async(greeting)
    
    def on_orb_mode_changed(self, mode):
        """Handle orb mode changes."""
        if mode == "talking":
            self.move_to_center()
        elif mode == "acting":
            self.move_to_side()
        else:  # idle
            self.move_to_center()
    
    def move_to_center(self):
        """Move window to center position."""
        if self.pos() != self.center_pos:
            self.pos_animation.setStartValue(self.pos())
            self.pos_animation.setEndValue(self.center_pos)
            self.pos_animation.start()
    
    def move_to_side(self):
        """Move window to side position."""
        if self.pos() != self.side_pos:
            self.pos_animation.setStartValue(self.pos())
            self.pos_animation.setEndValue(self.side_pos)
            self.pos_animation.start()
    
    def set_mode(self, mode):
        """Update mode and orb state."""
        self.current_mode = mode
        self.orb.set_mode(mode)
    
    def update_status(self, status):
        """Update status text."""
        self.status_label.setText(status)
    
    def on_speech_started(self):
        """Called when speech starts."""
        self.set_mode("talking")
    
    def on_speech_ended(self):
        """Called when speech ends."""
        QTimer.singleShot(500, lambda: self.set_mode("idle"))
    
    def speak_async(self, text):
        """Speak asynchronously."""
        self.set_mode("talking")
        self.update_status(f"OUTPUT: {text[:50]}...")
        
        threading.Thread(target=self.ai_worker.speak, args=(text,), daemon=True).start()
    
    def listen_async(self):
        """Listen for input."""
        if self.is_listening:
            return
        
        self.is_listening = True
        self.set_mode("talking")
        
        def listen_and_process():
            text = self.ai_worker.listen(duration=5)
            self.is_listening = False
            
            if text and "unavailable" not in text.lower() and "error" not in text.lower() and "no input" not in text.lower():
                self.update_status(f"INPUT: {text[:40]}...")
                QTimer.singleShot(500, lambda: self.process_input_async(text))
            else:
                self.update_status(text.upper())
                QTimer.singleShot(2500, lambda: self.set_mode("idle"))
        
        threading.Thread(target=listen_and_process, daemon=True).start()
    
    def process_input_async(self, user_input):
        """Process input."""
        self.set_mode("acting")
        
        def process():
            response = self.ai_worker.process_text(user_input)
            self.ai_worker.response_ready.emit(response)
        
        threading.Thread(target=process, daemon=True).start()
    
    def handle_response(self, response):
        """Handle response."""
        self.speak_async(response)
    
    def mousePressEvent(self, event):
        """Mouse press handler."""
        if event.button() == Qt.LeftButton:
            orb_rect = self.orb.geometry()
            if orb_rect.contains(event.pos()):
                self.listen_async()
            else:
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        """Mouse move handler."""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            self.center_pos = self.pos()
    
    def mouseReleaseEvent(self, event):
        """Mouse release handler."""
        self.drag_position = None
    
    def paintEvent(self, event):
        """Paint dark background with orange border."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Adjust opacity based on mode
        if self.current_mode == "acting":
            bg_alpha = 180
            border_alpha = 50
        else:
            bg_alpha = 230
            border_alpha = 70
        
        # Very dark background
        painter.setBrush(QColor(10, 5, 2, bg_alpha))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)
        
        # Orange border glow
        pen = QPen(QColor(255, 140, 0, border_alpha))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 15, 15)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS Assistant")
    
    assistant = JarvisAssistant()
    
    print("=" * 70)
    print("⚡ JARVIS INTERFACE ACTIVATED")
    print("=" * 70)
    print("• Click orb to speak")
    print("• Drag window to move")
    print("• Talk mode: Centered with energy bars")
    print("• Act mode: Moves aside, processing")
    print("• Voice: Coqui TTS (natural male voice)")
    print("• Theme: Orange/amber holographic (Iron Man style)")
    print("=" * 70)
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()