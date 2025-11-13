"""
Terminal Log Panel - Displays live Jarvis activity
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QScrollArea
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor


class TerminalPanel(QWidget):
    """Floating terminal overlay showing Jarvis logs"""
    
    def __init__(self):
        super().__init__()
        self.log_entries = []
        self.init_ui()
        self.is_visible = False
    
    def init_ui(self):
        """Setup terminal panel UI"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(10, 10, 400, 200)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("JARVIS LOG")
        title_font = QFont("Consolas", 10, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #00FF7F;")
        layout.addWidget(title)
        
        # Log text area
        self.log_text = QTextEdit()
        log_font = QFont("Courier New", 9)
        self.log_text.setFont(log_font)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(10, 10, 20, 200);
                color: #00FF7F;
                border: 1px solid #FFD580;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Status indicator
        self.status_label = QLabel("STATE: IDLE")
        self.status_label.setFont(title_font)
        self.status_label.setStyleSheet("color: #00FF7F;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 20, 200);
                border: 2px solid #00FF7F;
                border-radius: 5px;
            }
        """)
    
    def add_log(self, message, level="INFO"):
        """Add message to log"""
        colors = {
            "INFO": "#00FF7F",
            "WARNING": "#FFD580",
            "ERROR": "#FF6B6B",
            "ACTION": "#00C8FF"
        }
        color = colors.get(level, "#00FF7F")
        
        timestamp = __import__('datetime').datetime.now().strftime("%H:%M:%S")
        log_line = f"<span style='color: {color}'>[{timestamp}] {message}</span>"
        
        self.log_entries.append(log_line)
        
        # Keep only last 10 entries
        if len(self.log_entries) > 10:
            self.log_entries.pop(0)
        
        self.log_text.setHtml("<br>".join(self.log_entries))
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def set_state(self, state):
        """Update state indicator"""
        states = {
            "idle": ("#00FF7F", "IDLE"),
            "listening": ("#00C8FF", "LISTENING"),
            "speaking": ("#FFD580", "SPEAKING"),
            "executing": ("#FF7A18", "EXECUTING")
        }
        
        if state in states:
            color, label = states[state]
            self.status_label.setText(f"STATE: {label}")
            self.status_label.setStyleSheet(f"color: {color};")
    
    def toggle_visibility(self):
        """Toggle panel visibility"""
        self.is_visible = not self.is_visible
        if self.is_visible:
            self.show()
        else:
            self.hide()
