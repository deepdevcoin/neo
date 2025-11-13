"""
Text overlay with typing animation for Jarvis responses
"""

from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QColor


class TextOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # Create label for text display
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # Set up font - monospace, bold, green (#00FF7F)
        font = QFont("Courier New", 11, QFont.Bold)
        self.label.setFont(font)
        self.label.setStyleSheet("""
            QLabel {
                color: #00FF7F;
                background-color: rgba(0, 0, 0, 0);
                padding: 10px;
            }
        """)
        
        # Window properties
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Typing animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_typing)
        self.text = ""
        self.displayed_text = ""
        self.char_index = 0
        self.fade_timer = None
        self.y_offset = 0
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.animate_loading)
        self.loading_dots = 0
        
        # Hide by default
        self.hide()
    
    def show_loading_animation(self):
        """Show a loading animation until models are ready"""
        screen_geo = self.screen().geometry()
        self.move(50, (screen_geo.height() - 100) // 2)
        self.show()
        self.loading_timer.start(500) # Update every 500ms

    def animate_loading(self):
        """Animate the loading text with dots"""
        self.loading_dots = (self.loading_dots + 1) % 4
        dots = "." * self.loading_dots
        self.label.setText(f"INITIALIZING MODELS{dots}")

    def show_typing_animation(self, text):
        """Show typing animation for text"""
        self.text = text
        self.displayed_text = ""
        self.char_index = 0
        self.y_offset = 0
        
        # Position on left side of screen
        screen_geo = self.screen().geometry()
        self.move(50, (screen_geo.height() - 100) // 2)
        
        # Start typing animation
        self.show()
        self.loading_timer.stop()
        self.timer.start(40)  # ~25ms per character for smooth typing
    
    def animate_typing(self):
        """Animate typing effect"""
        if self.char_index < len(self.text):
            self.displayed_text += self.text[self.char_index]
            self.char_index += 1
            
            # Update label with fade effect
            self.label.setText(self.displayed_text + "▊")
            
            # Smooth upward slide
            self.y_offset -= 0.5
            self.label.move(0, int(self.y_offset))
        else:
            self.timer.stop()
            self.label.setText(self.displayed_text)
            
            # Schedule fade out
            self.fade_timer = QTimer()
            self.fade_timer.setSingleShot(True)
            self.fade_timer.timeout.connect(self.fade_and_hide)
            self.fade_timer.start(5000)  # 5 second display time
    
    def fade_and_hide(self):
        """Fade out and hide text"""
        # Simple opacity fade - could be enhanced with QPropertyAnimation
        self.hide()
        self.label.setText("")
    
    def close(self):
        """Clean up on close"""
        if self.timer.isActive():
            self.timer.stop()
        if self.fade_timer and self.fade_timer.isActive():
            self.fade_timer.stop()
        if self.loading_timer.isActive():
            self.loading_timer.stop()
        super().close()
