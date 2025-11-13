"""
Text Overlay - Displays typing animation of Jarvis responses
"""

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QRect, pyqtSignal, QPropertyAnimation, QPoint
from PyQt5.QtGui import QFont, QColor


class TextOverlay(QWidget):
    """Typing animation overlay for Jarvis responses"""
    
    def __init__(self):
        super().__init__()
        self.current_text = ""
        self.full_text = ""
        self.char_index = 0
        self.init_ui()
        self.fade_out_timer = None
    
    def init_ui(self):
        """Setup text overlay UI"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Position on left side of screen
        self.setGeometry(20, 100, 400, 300)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Text label with typing effect
        self.text_label = QLabel("")
        font = QFont("Courier New", 11)
        self.text_label.setFont(font)
        self.text_label.setStyleSheet("color: #00FF7F;")
        self.text_label.setWordWrap(True)
        layout.addWidget(self.text_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Typing timer
        self.type_timer = QTimer()
        self.type_timer.timeout.connect(self._type_char)
        
        # Fade out effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
    
    def show_typing_animation(self, text):
        """Start typing animation"""
        self.full_text = text
        self.current_text = ""
        self.char_index = 0
        self.text_label.setText("")
        
        # Show window and fade in
        self.show()
        fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_in.setDuration(300)
        fade_in.setStartValue(0)
        fade_in.setEndValue(1)
        fade_in.start()
        
        # Start typing
        self.type_timer.start(30)  # 30ms per character
    
    def _type_char(self):
        """Type one character"""
        if self.char_index < len(self.full_text):
            self.current_text += self.full_text[self.char_index]
            self.text_label.setText(self.current_text + "▊")
            self.char_index += 1
        else:
            self.type_timer.stop()
            self.text_label.setText(self.current_text)
            
            # Schedule fade out
            if self.fade_out_timer:
                self.fade_out_timer.stop()
            self.fade_out_timer = QTimer()
            self.fade_out_timer.setSingleShot(True)
            self.fade_out_timer.timeout.connect(self._fade_out)
            self.fade_out_timer.start(3000)  # Fade after 3 seconds
    
    def _fade_out(self):
        """Fade out and slide up animation"""
        fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out.setDuration(500)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        fade_out.start()
        
        # Slide up
        slide_up = QPropertyAnimation(self, b"pos")
        slide_up.setDuration(500)
        slide_up.setStartValue(self.pos())
        slide_up.setEndValue(QPoint(self.pos().x(), self.pos().y() - 30))
        slide_up.start()
