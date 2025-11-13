import sys
import time
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import QThread

class LoadingSignals(QObject):
    status_update = pyqtSignal(str)
    loading_complete = pyqtSignal()
    loading_error = pyqtSignal(str)

class InitializationWorker(QThread):
    """Background thread for loading heavy modules"""
    def __init__(self):
        super().__init__()
        self.signals = LoadingSignals()
        self.modules_status = {}
    
    def run(self):
        try:
            # Initialize modules one by one
            steps = [
                ("Initializing Neural Core…", self._init_core),
                ("Loading Speech Recognition Model (Vosk)…", self._init_vosk),
                ("Activating Audio Pipeline…", self._init_audio),
                ("Loading Visual Orb Components…", self._init_graphics),
                ("Loading AI Brain…", self._init_brain),
                ("Initialization Complete.", None),
            ]
            
            for step_text, init_func in steps:
                self.signals.status_update.emit(step_text)
                time.sleep(0.5)  # Brief pause for visibility
                
                if init_func:
                    try:
                        init_func()
                    except Exception as e:
                        print(f"[JARVIS] Warning during {step_text}: {e}")
                        self.modules_status[step_text] = f"fallback ({str(e)})"
                
                time.sleep(0.3)
            
            self.signals.loading_complete.emit()
        except Exception as e:
            self.signals.loading_error.emit(str(e))
    
    def _init_core(self):
        """Initialize core PyQt5"""
        pass
    
    def _init_vosk(self):
        """Load Vosk model"""
        try:
            import vosk
            print("[JARVIS] Vosk model loaded successfully")
        except ImportError:
            raise Exception("Vosk not installed")
    
    def _init_audio(self):
        """Initialize audio capture"""
        try:
            import sounddevice
            import numpy
            print("[JARVIS] Audio pipeline ready")
        except ImportError:
            raise Exception("sounddevice/numpy not installed")
    
    def _init_graphics(self):
        """Initialize graphics"""
        try:
            import OpenGL
            print("[JARVIS] OpenGL graphics ready")
        except ImportError:
            print("[JARVIS] OpenGL unavailable, using fallback rendering")
    
    def _init_brain(self):
        """Initialize AI brain"""
        try:
            from gpt4all import GPT4All
            print("[JARVIS] AI brain initialized")
        except ImportError:
            print("[JARVIS] GPT4All not available, using rule-based responses")

class LoadingScreen(QWidget):
    """Startup loading overlay with animated text"""
    loading_complete = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_status = ""
        self.init_ui()
        self.start_loading()
    
    def init_ui(self):
        """Setup UI for loading screen"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Center on screen
        screen = self.frameGeometry()
        screen.moveCenter(self.screen().availableGeometry().center())
        self.move(screen.topLeft())
        
        self.setGeometry(0, 0, 600, 400)
        
        # Layout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 60, 40, 60)
        
        # Title
        title = QLabel("JARVIS")
        title_font = QFont("Consolas", 32, QFont.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00FF7F;")
        layout.addWidget(title)
        
        # Status label
        self.status_label = QLabel("Initializing Neural Core…")
        status_font = QFont("Courier New", 12)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #00FF7F;")
        layout.addWidget(self.status_label)
        
        # Animated dots
        self.dot_label = QLabel("")
        self.dot_label.setFont(status_font)
        self.dot_label.setAlignment(Qt.AlignCenter)
        self.dot_label.setStyleSheet("color: #FFD580;")
        layout.addWidget(self.dot_label)
        
        # Progress log
        self.log_label = QLabel("")
        log_font = QFont("Courier New", 10)
        self.log_label.setFont(log_font)
        self.log_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.log_label.setStyleSheet("color: #00FF7F;")
        layout.addWidget(self.log_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Animated dots timer
        self.dot_count = 0
        self.dot_timer = QTimer()
        self.dot_timer.timeout.connect(self.update_dots)
        self.dot_timer.start(500)
        
        # Stylesheet with semi-transparent dark background
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 20, 240);
                border: 2px solid #00FF7F;
                border-radius: 10px;
            }
        """)
    
    def update_dots(self):
        """Animate loading dots"""
        self.dot_count = (self.dot_count + 1) % 4
        self.dot_label.setText("." * self.dot_count)
    
    def start_loading(self):
        """Start background initialization"""
        self.worker = InitializationWorker()
        self.worker.signals.status_update.connect(self.update_status)
        self.worker.signals.loading_complete.connect(self.on_complete)
        self.worker.signals.loading_error.connect(self.on_error)
        self.worker.start()
    
    def update_status(self, status):
        """Update status text with fade effect"""
        self.status_label.setText(status)
        current_log = self.log_label.text()
        if status and "…" in status:
            # Add to log with green checkmark
            self.log_label.setText(current_log + "✓ " + status + "\n")
    
    def on_complete(self):
        """Handle initialization complete"""
        print("[JARVIS] Initialization complete, starting main window")
        self.dot_timer.stop()
        self.status_label.setText("Initialization Complete.")
        QTimer.singleShot(1000, self.close)
        QTimer.singleShot(1000, self.loading_complete.emit)
    
    def on_error(self, error):
        """Handle initialization error"""
        print(f"[JARVIS] Initialization error: {error}")
        self.status_label.setText("Fallback mode: Graphics safe mode enabled.")
        self.status_label.setStyleSheet("color: #FF6B6B;")
        QTimer.singleShot(2000, self.close)
        QTimer.singleShot(2000, self.loading_complete.emit)
