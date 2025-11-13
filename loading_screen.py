
import sys
import io
import time
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont


class Stream(QObject):
    """A custom stream to redirect stdout/stderr to a pyqtSignal."""
    newText = pyqtSignal(str)

    def write(self, text):
        self.newText.emit(str(text))

    def flush(self):
        pass

class LoadingSignals(QObject):
    status_update = pyqtSignal(str)
    loading_complete = pyqtSignal()
    loading_error = pyqtSignal(str)

class InitializationWorker(QThread):
    """Background thread for loading heavy modules only during startup."""
    def __init__(self, speech_engine):
        super().__init__()
        self.signals = LoadingSignals()
        self.speech_engine = speech_engine
    
    def run(self):
        try:
            steps = [
                ("Initializing Neural Core…", None),
                ("Loading Speech Recognition (Vosk)…", self.speech_engine.init_recognition),
                ("Loading Text-to-Speech Engine (Coqui)…", self.speech_engine.init_tts),
                ("Loading AI Brain (GPT4All)…", self.speech_engine.init_gpt4all),
                ("Finalizing…", None),
            ]
            
            for step_text, init_func in steps:
                self.signals.status_update.emit(step_text)
                time.sleep(0.5)
                if init_func:
                    try:
                        init_func()
                    except Exception as e:
                        print(f"[JARVIS] Warning during {step_text}: {e}")
                time.sleep(0.3)
            
            self.signals.loading_complete.emit()
        except Exception as e:
            self.signals.loading_error.emit(str(e))

class LogViewer(QWidget):
    """A persistent window to display logs and system status."""
    loading_complete = pyqtSignal()
    
    def __init__(self, speech_engine):
        super().__init__()
        self.speech_engine = speech_engine
        self.init_ui()
        self.redirect_stdout()
        self.start_loading()
    
    def init_ui(self):
        """Setup the UI for the log viewer."""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Position in top-left corner
        self.setGeometry(10, 40, 600, 500) 

        # Layout
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("J.A.R.V.I.S. STATUS")
        title_font = QFont("Consolas", 24, QFont.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00FF7F;")
        layout.addWidget(title)

        # Status label
        self.status_label = QLabel("Initializing…")
        status_font = QFont("Courier New", 12)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #E0E0E0;")
        layout.addWidget(self.status_label)
        
        # Log display
        self.log_label = QLabel("")
        log_font = QFont("Courier New", 9)
        self.log_label.setFont(log_font)
        self.log_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.log_label.setWordWrap(True)
        self.log_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 180);
            color: #00FF7F;
            border: 1px solid #00FF7F;
            border-radius: 5px;
            padding: 10px;
        """)
        self.log_label.setMinimumHeight(350) # Make log area larger
        layout.addWidget(self.log_label)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 20, 230);
                border: 1px solid #00FF7F;
                border-radius: 10px;
            }
        """)
    
    def redirect_stdout(self):
        """Redirect stdout and stderr to the log label."""
        sys.stdout = Stream(newText=self.append_log)
        sys.stderr = Stream(newText=self.append_log)
        print("[LOG] Console output redirected to log viewer.")

    def append_log(self, text):
        """Appends text to the log display."""
        current_text = self.log_label.text()
        lines = (current_text + text).split('\n')
        max_lines = 100
        new_text = '\n'.join(lines[-max_lines:])
        self.log_label.setText(new_text)

    def start_loading(self):
        """Start the background initialization worker."""
        self.worker = InitializationWorker(self.speech_engine)
        self.worker.signals.status_update.connect(self.update_status)
        self.worker.signals.loading_complete.connect(self.on_complete)
        self.worker.signals.loading_error.connect(self.on_error)
        self.worker.start()
    
    def update_status(self, status):
        """Update the status text."""
        self.status_label.setText(f"Status: {status}")
    
    def on_complete(self):
        """Handle successful initialization."""
        print("[JARVIS] System is online.")
        self.status_label.setText("Status: ONLINE")
        self.loading_complete.emit()
    
    def on_error(self, error):
        """Handle initialization error."""
        print(f"[JARVIS] CRITICAL ERROR: {error}")
        self.status_label.setText("Status: DEGRADED MODE")
        self.status_label.setStyleSheet("color: #FF6B6B;")
        self.loading_complete.emit() # Still start the app

    def closeEvent(self, event):
        """Restore stdout on close."""
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        super().closeEvent(event)
