
import sys
import time
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication, QTextEdit, QSizePolicy, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QRunnable, QThreadPool
from PyQt5.QtGui import QFont, QTextCursor

class Stream(QObject):
    newText = pyqtSignal(str)
    def write(self, text):
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        log_entry = text
        # Prevent double-timestamping
        if not text.startswith(f"[{timestamp}]"):
             log_entry = f"[{timestamp}] {text}"
        self.newText.emit(str(log_entry))
    def flush(self):
        pass

class LoadingSignals(QObject):
    status_update = pyqtSignal(str)
    loading_complete = pyqtSignal()
    loading_error = pyqtSignal(str)
    step_finished = pyqtSignal(str)

class InitStep(QRunnable):
    def __init__(self, text, func, signals):
        super().__init__()
        self.text = text
        self.func = func
        self.signals = signals
    def run(self):
        try:
            self.signals.status_update.emit(self.text)
            start_time = time.time()
            if self.func:
                self.func()
            duration = time.time() - start_time
            print(f"[INIT] Task '{self.text}' completed in {duration:.2f} seconds.")
            self.signals.step_finished.emit(self.text)
        except Exception as e:
            self.signals.loading_error.emit(f"Error during {self.text}: {e}")

class InitializationWorker(QObject):
    def __init__(self, speech_engine):
        super().__init__()
        self.signals = LoadingSignals()
        self.speech_engine = speech_engine
        self.threadpool = QThreadPool()
        self.steps_to_finish = 0
    def run(self):
        self.steps = [
            ("Initializing Neural Core…", None),
            ("Loading Speech Recognition (Vosk)…", self.speech_engine.init_recognition),
            ("Loading Text-to-Speech Engine (Coqui)…", self.speech_engine.init_tts),
            ("Finalizing…", None),
        ]
        self.steps_to_finish = len(self.steps)
        self.signals.step_finished.connect(self.on_step_finished)
        for step_text, init_func in self.steps:
            step_runnable = InitStep(step_text, init_func, self.signals)
            self.threadpool.start(step_runnable)
    def on_step_finished(self, step_text):
        self.steps_to_finish -= 1
        if self.steps_to_finish == 0:
            self.signals.loading_complete.emit()

class LogViewer(QWidget):
    loading_complete = pyqtSignal()
    
    def __init__(self, speech_engine):
        super().__init__()
        print("[LOG_VIEWER] Initializing UI.")
        self.speech_engine = speech_engine
        self.init_ui()
        self.redirect_stdout()
        self.start_loading()

        print("[LOG_VIEWER] Connecting to speech engine signals.")
        self.speech_engine.generation_started.connect(self.clear_response_display)
        self.speech_engine.response_chunk_ready.connect(self.append_response_chunk)
    
    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen_geo = QApplication.desktop().screenGeometry()
        self.setGeometry(10, 40, 700, screen_geo.height() - 80)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("J.A.R.V.I.S. STATUS")
        title.setFont(QFont("Consolas", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00FF7F;")
        layout.addWidget(title)

        self.status_label = QLabel("Initializing…")
        self.status_label.setFont(QFont("Courier New", 12))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #E0E0E0;")
        layout.addWidget(self.status_label)
        
        response_title = QLabel("AI RESPONSE")
        response_title.setFont(QFont("Courier New", 12, QFont.Bold))
        response_title.setStyleSheet("color: #00BFFF;")
        layout.addWidget(response_title)

        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        self.response_display.setFont(QFont("Courier New", 11))
        self.response_display.setStyleSheet("""
            background-color: rgba(0, 0, 0, 180);
            color: #00BFFF;
            border: 1px solid #00BFFF;
            border-radius: 5px;
            padding: 10px;
        """)
        self.response_display.setFixedHeight(120)
        layout.addWidget(self.response_display)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #555;")
        layout.addWidget(line)

        log_title = QLabel("SYSTEM LOG")
        log_title.setFont(QFont("Courier New", 12, QFont.Bold))
        log_title.setStyleSheet("color: #00FF7F;")
        layout.addWidget(log_title)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Courier New", 9))
        self.log_display.setStyleSheet("""
            background-color: rgba(0, 0, 0, 180);
            color: #00FF7F;
            border: 1px solid #00FF7F;
            border-radius: 5px;
            padding: 10px;
        """)
        self.log_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.log_display)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 20, 230);
                border: 1px solid #00FF7F;
                border-radius: 10px;
            }
        """)
    
    def redirect_stdout(self):
        sys.stdout = Stream(newText=self.append_log)
        sys.stderr = Stream(newText=self.append_log)
        print("[LOG] Console output redirected to log viewer.")

    def append_log(self, text):
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.log_display.ensureCursorVisible()

    def clear_response_display(self):
        print("[LOG_VIEWER] Clearing AI response display.")
        self.response_display.clear()

    def append_response_chunk(self, chunk):
        # This can be very noisy, so it's commented out by default.
        # print(f"[LOG_VIEWER] Appending chunk: '{chunk}'")
        cursor = self.response_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(chunk)
        self.response_display.ensureCursorVisible()

    def start_loading(self):
        print("[LOG_VIEWER] Starting initialization worker.")
        self.worker = InitializationWorker(self.speech_engine)
        self.worker.signals.status_update.connect(self.update_status)
        self.worker.signals.loading_complete.connect(self.on_complete)
        self.worker.signals.loading_error.connect(self.on_error)
        self._worker_ref = self.worker 
        self.worker.run()
    
    def update_status(self, status):
        self.status_label.setText(f"Status: {status}")
    
    def on_complete(self):
        print("[LOG_VIEWER] Loading complete.")
        print("[JARVIS] System is online.")
        self.status_label.setText("Status: ONLINE")
        self.loading_complete.emit()
    
    def on_error(self, error):
        print(f"[LOG_VIEWER] CRITICAL ERROR received: {error}")
        print(f"[JARVIS] CRITICAL ERROR: {error}")
        self.status_label.setText("Status: DEGRADED MODE")
        self.status_label.setStyleSheet("color: #FF6B6B;")

    def closeEvent(self, event):
        print("[LOG_VIEWER] Close event. Restoring stdout/stderr.")
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        super().closeEvent(event)
