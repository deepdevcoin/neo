"""
Text input handler for Neo - allows typing commands at the bottom of screen
"""

from PyQt5.QtWidgets import QWidget, QLineEdit, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QFont, QColor


class TextInputHandler(QWidget):
    text_submitted = pyqtSignal(str)  # Emitted when user presses Enter
    
    def __init__(self):
        super().__init__()
        
        # Window properties - always on top, transparent for mouse events only on input
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a command... (or use Ctrl+Space for speech)")
        
        # Style the input field
        font = QFont("Courier New", 12)
        self.input_field.setFont(font)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(20, 20, 30, 0.9);
                color: #00FF7F;
                border: 2px solid #00FF7F;
                border-radius: 5px;
                padding: 8px;
            }
            QLineEdit:focus {
                background-color: rgba(30, 30, 40, 0.95);
                border: 2px solid #00FFFF;
            }
            QLineEdit::placeholder {
                color: #007744;
            }
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.input_field)
        self.setLayout(layout)
        
        # Connect signals
        self.input_field.returnPressed.connect(self.on_submit)
        
        # Position at bottom of screen
        self.reposition()
    
    def reposition(self):
        """Position input box at bottom of screen, centered"""
        screen_geo = self.screen().geometry()
        width = 600
        height = 60
        x = (screen_geo.width() - width) // 2
        y = screen_geo.height() - height - 30  # 30px from bottom
        
        self.setGeometry(QRect(x, y, width, height))
    
    def on_submit(self):
        """Handle text submission"""
        text = self.input_field.text().strip()
        if text:
            self.text_submitted.emit(text)
            self.input_field.clear()
    
    def clear_input(self):
        """Clear the input field"""
        self.input_field.clear()
    
    def set_focus(self):
        """Set focus to input field"""
        self.input_field.setFocus()
    
    def show_with_focus(self):
        """Show and focus the input field"""
        self.show()
        self.set_focus()
