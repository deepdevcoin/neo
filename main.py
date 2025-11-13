"""
Jarvis Neural Core - Main Application Entry Point
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint

from orb_renderer import OrbRenderer
from audio_listener import AudioListener
from speech_engine import SpeechEngine
from hotkey_manager import HotkeyManager
from text_overlay import TextOverlay
from text_input_handler import TextInputHandler
from animation_manager import AnimationManager
from loading_screen import LogViewer # Renamed from LoadingScreen


class JarvisWindow(QMainWindow):
    def __init__(self, speech_engine: SpeechEngine):
        super().__init__()
        self.speech_engine = speech_engine

        # Basic setup
        self.setWindowTitle("Jarvis Neural Core")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Geometry
        screen_geo = QApplication.desktop().screenGeometry()
        self.screen_width = screen_geo.width()
        self.screen_height = screen_geo.height()
        orb_size = 300
        self.center_x = (self.screen_width - orb_size) // 2
        self.center_y = (self.screen_height - orb_size) // 2
        self.setGeometry(self.center_x, self.center_y, orb_size, orb_size)

        # VisPy Canvas
        from vispy import scene
        self.canvas = scene.SceneCanvas(keys='interactive', show=True, bgcolor=(0, 0, 0, 0))
        self.canvas.native.setStyleSheet("background-color: rgba(0,0,0,0);")
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas.native)
        self.setCentralWidget(central_widget)

        # Components
        self.animation_manager = AnimationManager()
        self.orb_renderer = OrbRenderer(self.canvas, num_particles=150)
        self.audio_listener = AudioListener()
        self.hotkey_manager = HotkeyManager()
        self.text_overlay = TextOverlay()
        self.text_input = TextInputHandler()

        # Signals
        self.audio_listener.amplitude_updated.connect(self.on_amplitude_update)
        self.speech_engine.speech_recognized.connect(self.on_speech_recognized)
        self.speech_engine.tts_started.connect(self.on_tts_started)
        self.speech_engine.tts_finished.connect(self.on_tts_finished)
        self.hotkey_manager.hotkey_pressed.connect(self.toggle_listening)
        self.text_input.text_submitted.connect(self.on_text_submitted)

        # State
        self.is_listening = False
        self.is_speaking = False
        self.action_mode = False
        self.orb_target_pos = QPoint(self.center_x, self.center_y)
        self.orb_target_scale = 1.0
        self.orb_current_scale = 1.0

        # Start background services
        self.audio_thread = QThread()
        self.audio_listener.moveToThread(self.audio_thread)
        self.audio_thread.started.connect(self.audio_listener.start)
        self.audio_thread.start()
        self.speech_engine.start() # Speech recognition loop
        self.hotkey_manager.start()

        # UI Elements
        self.text_input.show()
        self.timer = QTimer(self, timeout=self.update_animation)
        self.timer.start(16) # ~60 FPS

        print("[JARVIS] Main window loaded. Ready for commands.")

    def on_amplitude_update(self, amplitude):
        normalized = min(amplitude / 0.15, 1.0)
        self.orb_renderer.set_reactivity(normalized)

    def on_tts_started(self, text):
        self.is_speaking = True
        self.speech_engine.stop_recognition()
        self.text_overlay.show_typing_animation(text)
        self.orb_renderer.trigger_pulse()
        print(f"[JARVIS]: {text}") # Log AI response

    def on_tts_finished(self):
        self.is_speaking = False
        self.text_overlay.hide()
        if self.is_listening:
            self.speech_engine.start_recognition()

    def on_speech_recognized(self, text):
        if self.is_speaking: return
        print(f"[USER]: {text}")
        self.process_command(text)

    def on_text_submitted(self, text):
        print(f"[USER]: {text}")
        self.process_command(text)

    def process_command(self, text):
        if self.is_action_command(text):
            self.enter_action_mode(text)
        else:
            response = self.speech_engine.generate_response(text)
            self.speech_engine.speak(response)

    def is_action_command(self, text):
        text_lower = text.lower()
        action_keywords = ['open', 'show', 'launch', 'start', 'run', 'execute', 'time', 'date']
        return any(keyword in text_lower for keyword in action_keywords)

    def enter_action_mode(self, command):
        self.action_mode = True
        target_x = self.screen_width - 200
        target_y = self.screen_height // 2 - 100
        self.orb_target_pos = QPoint(target_x, target_y)
        self.orb_target_scale = 0.6
        self.orb_renderer.set_action_mode(True)
        QTimer.singleShot(500, lambda: self.execute_action(command))

    def execute_action(self, command):
        try:
            import subprocess
            print(f"[ACTION]: {command}")
            if 'browser' in command.lower() or 'chrome' in command.lower():
                subprocess.Popen(['xdg-open', 'https://www.google.com'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif 'terminal' in command.lower():
                subprocess.Popen(['gnome-terminal'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif 'time' in command.lower():
                import datetime
                self.speech_engine.speak(f"The time is {datetime.datetime.now().strftime('%H:%M')}")
            else:
                self.speech_engine.speak("Executing action, sir.")
            QTimer.singleShot(2000, self.exit_action_mode)
        except Exception as e:
            print(f"[ERROR] Action failed: {e}")
            self.exit_action_mode()

    def exit_action_mode(self):
        self.action_mode = False
        self.orb_target_pos = QPoint(self.center_x, self.center_y)
        self.orb_target_scale = 1.0
        self.orb_renderer.set_action_mode(False)

    def toggle_listening(self):
        self.is_listening = not self.is_listening
        if self.is_listening:
            self.speech_engine.start_recognition()
        else:
            self.speech_engine.stop_recognition()

    def update_animation(self):
        current_pos = self.geometry().topLeft()
        if current_pos != self.orb_target_pos:
            new_x = self.animation_manager.lerp(current_pos.x(), self.orb_target_pos.x(), 0.08)
            new_y = self.animation_manager.lerp(current_pos.y(), self.orb_target_pos.y(), 0.08)
            self.move(int(new_x), int(new_y))
        
        if abs(self.orb_current_scale - self.orb_target_scale) > 0.01:
            self.orb_current_scale = self.animation_manager.lerp(self.orb_current_scale, self.orb_target_scale, 0.08)
            self.orb_renderer.set_scale(self.orb_current_scale)
        
        self.orb_renderer.update()
        self.canvas.update()

    def closeEvent(self, event):
        self.audio_thread.quit()
        self.audio_thread.wait()
        self.speech_engine.stop()
        self.hotkey_manager.stop()
        self.text_overlay.close()
        self.text_input.close()
        event.accept()

class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.speech_engine = SpeechEngine()
        self.log_viewer = LogViewer(self.speech_engine)
        self.log_viewer.loading_complete.connect(self.start_main_app)
        self.log_viewer.show()

    def start_main_app(self):
        self.main_window = JarvisWindow(self.speech_engine)
        self.main_window.show()

    def run(self):
        # Close the log viewer when the app exits
        self.app.aboutToQuit.connect(self.log_viewer.close)
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    main_app = Application()
    main_app.run()
