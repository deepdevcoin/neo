"""
Jarvis Neural Core - Enhanced Desktop Overlay Application with text input
A floating, always-on-top 3D neural orb with speech recognition, TTS, and text input
"""

import sys
import os
import subprocess
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRect, QPoint
from PyQt5.QtGui import QSurfaceFormat
import numpy as np

from orb_renderer import OrbRenderer
from audio_listener import AudioListener
from speech_engine import SpeechEngine
from hotkey_manager import HotkeyManager
from text_overlay import TextOverlay
from text_input_handler import TextInputHandler
from animation_manager import AnimationManager


class JarvisWindow(QMainWindow):
    audio_update = pyqtSignal(float)
    speech_detected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Window configuration - frameless, transparent, always on top, click-through
        self.setWindowTitle("Jarvis Neural Core")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Window geometry (center-screen)
        screen_geo = QApplication.desktop().screenGeometry()
        self.screen_width = screen_geo.width()
        self.screen_height = screen_geo.height()
        
        orb_size = 300
        self.center_x = (self.screen_width - orb_size) // 2
        self.center_y = (self.screen_height - orb_size) // 2
        
        self.setGeometry(self.center_x, self.center_y, orb_size, orb_size)
        
        # Setup VisPy canvas with transparent background
        from vispy import scene
        self.canvas = scene.SceneCanvas(
            keys='interactive',
            show=True,
            bgcolor=(0, 0, 0, 0)  # Fully transparent
        )
        self.canvas.measure_fps()
        self.canvas.native.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        
        # Create central widget
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas.native)
        self.setCentralWidget(central_widget)
        
        # Initialize animation manager for smooth easing
        self.animation_manager = AnimationManager()
        
        # Initialize components
        self.orb_renderer = OrbRenderer(self.canvas, num_particles=150)
        self.audio_listener = AudioListener()
        self.speech_engine = SpeechEngine()
        self.hotkey_manager = HotkeyManager()
        self.text_overlay = TextOverlay()
        self.text_input = TextInputHandler()  # Add text input handler
        
        # Connect signals
        self.audio_listener.amplitude_updated.connect(self.on_amplitude_update)
        self.speech_engine.speech_recognized.connect(self.on_speech_recognized)
        self.speech_engine.tts_started.connect(self.on_tts_started)
        self.hotkey_manager.hotkey_pressed.connect(self.toggle_listening)
        self.text_input.text_submitted.connect(self.on_text_submitted)  # Connect text input signal
        
        # State management
        self.is_listening = False
        self.is_speaking = False
        self.action_mode = False
        self.action_timer = None
        
        self.orb_target_pos = QPoint(self.center_x, self.center_y)
        self.orb_target_scale = 1.0
        self.orb_current_scale = 1.0
        
        # Start threads
        self.audio_thread = QThread()
        self.audio_listener.moveToThread(self.audio_thread)
        self.audio_thread.started.connect(self.audio_listener.start)
        self.audio_thread.start()
        
        self.speech_thread = QThread()
        self.speech_engine.moveToThread(self.speech_thread)
        self.speech_thread.started.connect(self.speech_engine.start)
        self.speech_thread.start()
        
        # Start hotkey listener
        self.hotkey_manager.start()
        
        # Show text input box
        self.text_input.show()
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # 60 FPS
        
        print("Jarvis Neural Core initialized. Press Ctrl+Space to activate or type commands below.")
    
    def on_amplitude_update(self, amplitude):
        """Update orb glow based on mic amplitude"""
        normalized = min(amplitude / 0.15, 1.0)
        self.orb_renderer.set_reactivity(normalized)
    
    def on_tts_started(self, text):
        """Called when TTS begins - show typing animation overlay"""
        self.is_speaking = True
        self.text_overlay.show_typing_animation(text)
        self.orb_renderer.trigger_pulse()
    
    def on_speech_recognized(self, text):
        """Handle recognized speech"""
        print(f"[JARVIS] Heard: {text}")
        self.process_command(text)
    
    def on_text_submitted(self, text):
        """Handle text input from the input box"""
        print(f"[JARVIS] Command: {text}")
        self.process_command(text)
    
    def process_command(self, text):
        """Process a command from either speech or text input"""
        # Check if it's an action command
        if self.is_action_command(text):
            self.enter_action_mode(text)
        else:
            # Generate and speak response
            response = self.generate_response(text)
            self.speech_engine.speak(response)
    
    def is_action_command(self, text):
        """Check if text is an action command"""
        text_lower = text.lower()
        action_keywords = ['open', 'show', 'launch', 'start', 'run', 'execute', 'time', 'date']
        return any(keyword in text_lower for keyword in action_keywords)
    
    def enter_action_mode(self, command):
        """Enter action mode: move orb to right, execute command, return to center"""
        self.action_mode = True
        
        target_x = self.screen_width - 200
        target_y = self.screen_height // 2 - 100
        self.orb_target_pos = QPoint(target_x, target_y)
        self.orb_target_scale = 0.6
        
        # Add color pulse to indicate action mode
        self.orb_renderer.set_action_mode(True)
        
        # Execute the command after a brief delay
        self.action_timer = QTimer()
        self.action_timer.setSingleShot(True)
        self.action_timer.timeout.connect(lambda: self.execute_action(command))
        self.action_timer.start(500)
    
    def execute_action(self, command):
        """Execute an action command"""
        try:
            print(f"[JARVIS] Executing: {command}")
            
            # Simple action mappings
            if 'browser' in command.lower() or 'chrome' in command.lower():
                subprocess.Popen(['xdg-open', 'https://www.google.com'], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif 'terminal' in command.lower():
                subprocess.Popen(['gnome-terminal'], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif 'time' in command.lower():
                import datetime
                current_time = datetime.datetime.now().strftime("%H:%M")
                self.speech_engine.speak(f"The time is {current_time}")
            else:
                self.speech_engine.speak("Executing action, sir.")
            
            # Return to center after action
            QTimer.singleShot(2000, self.exit_action_mode)
        except Exception as e:
            print(f"Action error: {e}")
            self.exit_action_mode()
    
    def exit_action_mode(self):
        """Exit action mode and return orb to center"""
        self.action_mode = False
        self.orb_target_pos = QPoint(self.center_x, self.center_y)
        self.orb_target_scale = 1.0
        self.orb_renderer.set_action_mode(False)
    
    def toggle_listening(self):
        """Toggle listening mode with hotkey"""
        self.is_listening = not self.is_listening
        
        if self.is_listening:
            print("[JARVIS] Listening activated...")
            self.audio_listener.start_listening()
            self.speech_engine.start_recognition()
        else:
            print("[JARVIS] Listening deactivated.")
            self.audio_listener.stop_listening()
            self.speech_engine.stop_recognition()
    
    def update_animation(self):
        """Update animation frame with smooth easing"""
        if self.geometry().topLeft() != self.orb_target_pos:
            current_pos = self.geometry().topLeft()
            new_x = self.animation_manager.lerp(current_pos.x(), self.orb_target_pos.x(), 0.08)
            new_y = self.animation_manager.lerp(current_pos.y(), self.orb_target_pos.y(), 0.08)
            self.move(int(new_x), int(new_y))
        
        if abs(self.orb_current_scale - self.orb_target_scale) > 0.01:
            self.orb_current_scale = self.animation_manager.lerp(
                self.orb_current_scale, 
                self.orb_target_scale, 
                0.08
            )
            self.orb_renderer.set_scale(self.orb_current_scale)
        
        # Update orb renderer
        self.orb_renderer.update()
        self.canvas.update()
    
    def generate_response(self, text):
        """Generate a Jarvis-like response"""
        return self.speech_engine.generate_response(text)
    
    def closeEvent(self, event):
        """Cleanup on close"""
        self.audio_thread.quit()
        self.audio_thread.wait()
        self.speech_thread.quit()
        self.speech_thread.wait()
        self.hotkey_manager.stop()
        self.text_overlay.close()
        self.text_input.close()  # Close text input handler
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = JarvisWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
