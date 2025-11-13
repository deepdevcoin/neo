
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint, QRunnable, QThreadPool, QObject

from orb_renderer import OrbRenderer
from audio_listener import AudioListener
from speech_engine import SpeechEngine
from hotkey_manager import HotkeyManager
from text_overlay import TextOverlay
from text_input_handler import TextInputHandler
from animation_manager import AnimationManager
from loading_screen import LogViewer

class GenerationSignals(QObject):
    response_ready = pyqtSignal(str)

class GenerationWorker(QRunnable):
    def __init__(self, speech_engine, text, signals):
        super().__init__()
        print("[WORKER] GenerationWorker created.")
        self.speech_engine = speech_engine
        self.text = text
        self.signals = signals

    def run(self):
        print("[WORKER] GenerationWorker started.")
        # This now returns the full response at the end of streaming
        full_response = self.speech_engine.generate_response(self.text)
        print(f"[WORKER] Full response received: '{full_response[:30]}...'")
        self.signals.response_ready.emit(full_response)
        print("[WORKER] GenerationWorker finished.")

class JarvisWindow(QMainWindow):
    def __init__(self, speech_engine: SpeechEngine):
        super().__init__()
        print("[MAIN_WINDOW] Initializing...")
        self.speech_engine = speech_engine
        self.setWindowTitle("Jarvis Neural Core")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        screen_geo = QApplication.desktop().screenGeometry()
        self.screen_width = screen_geo.width()
        self.screen_height = screen_geo.height()
        orb_size = 300
        self.center_x = (self.screen_width - orb_size) // 2
        self.center_y = (self.screen_height - orb_size) // 2
        self.setGeometry(self.center_x, self.center_y, orb_size, orb_size)

        from vispy import scene
        self.canvas = scene.SceneCanvas(keys='interactive', show=True, bgcolor=(0, 0, 0, 0))
        self.canvas.native.setStyleSheet("background-color: rgba(0,0,0,0);")
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas.native)
        self.setCentralWidget(central_widget)

        self.animation_manager = AnimationManager()
        self.orb_renderer = OrbRenderer(self.canvas, num_particles=150)
        self.audio_listener = AudioListener()
        self.hotkey_manager = HotkeyManager()
        self.text_overlay = TextOverlay()
        self.text_input = TextInputHandler()
        self.threadpool = QThreadPool()
        print(f"[MAIN_WINDOW] Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

        self.audio_listener.amplitude_updated.connect(self.on_amplitude_update)
        self.speech_engine.speech_recognized.connect(self.on_speech_recognized)
        self.speech_engine.tts_started.connect(self.on_tts_started)
        self.speech_engine.tts_finished.connect(self.on_tts_finished)
        self.hotkey_manager.hotkey_pressed.connect(self.toggle_listening)
        self.text_input.text_submitted.connect(self.on_text_submitted)

        self.is_listening = False
        self.is_speaking = False
        self.action_mode = False
        self.orb_target_pos = QPoint(self.center_x, self.center_y)
        self.orb_target_scale = 1.0
        self.orb_current_scale = 1.0

        self.audio_thread = QThread()
        self.audio_listener.moveToThread(self.audio_thread)
        self.audio_thread.started.connect(self.audio_listener.start)
        self.audio_thread.start()
        self.speech_engine.start()
        self.hotkey_manager.start()

        self.text_input.show()
        self.timer = QTimer(self, timeout=self.update_animation)
        self.timer.start(16)
        print("[MAIN_WINDOW] Main window loaded. Ready for commands.")

    def on_amplitude_update(self, amplitude):
        normalized = min(amplitude / 0.15, 1.0)
        self.orb_renderer.set_reactivity(normalized)

    def on_tts_started(self, text):
        print("[MAIN_WINDOW] on_tts_started signal received.")
        self.is_speaking = True
        self.speech_engine.stop_recognition()
        self.text_overlay.show_typing_animation(text)
        self.orb_renderer.trigger_pulse()

    def on_tts_finished(self):
        print("[MAIN_WINDOW] on_tts_finished signal received.")
        self.is_speaking = False
        self.text_overlay.hide()
        if self.is_listening:
            self.speech_engine.start_recognition()

    def on_speech_recognized(self, text):
        if self.is_speaking: return
        print(f"[USER via Speech]: {text}")
        self.process_command(text)

    def on_text_submitted(self, text):
        print(f"[USER via Text]: {text}")
        self.process_command(text)

    def on_response_ready(self, full_response):
        print("[MAIN_WINDOW] on_response_ready signal received.")
        print(f"[JARVIS]: {full_response}")
        self.speech_engine.speak(full_response)

    def process_command(self, text):
        print(f"[MAIN_WINDOW] Processing command: '{text}'")
        if self.is_action_command(text):
            self.enter_action_mode(text)
        else:
            print("[MAIN_WINDOW] Command is not an action. Starting generation worker.")
            signals = GenerationSignals()
            signals.response_ready.connect(self.on_response_ready)
            worker = GenerationWorker(self.speech_engine, text, signals)
            self._generation_worker_ref = worker
            self._generation_signals_ref = signals
            self.threadpool.start(worker)

    def is_action_command(self, text):
        text_lower = text.lower()
        action_keywords = ['open', 'show', 'launch', 'start', 'run', 'execute', 'time', 'date']
        is_action = any(keyword in text_lower for keyword in action_keywords)
        print(f"[MAIN_WINDOW] is_action_command check for '{text}': {is_action}")
        return is_action

    def enter_action_mode(self, command):
        print("[MAIN_WINDOW] Entering action mode.")
        self.action_mode = True
        self.orb_target_pos = QPoint(self.screen_width - 200, self.screen_height // 2 - 100)
        self.orb_target_scale = 0.6
        self.orb_renderer.set_action_mode(True)
        QTimer.singleShot(500, lambda: self.execute_action(command))

    def execute_action(self, command):
        print(f"[MAIN_WINDOW] Executing action: '{command}'")
        try:
            import subprocess
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
            print(f"[MAIN_WINDOW ERROR] Action failed: {e}")
            self.exit_action_mode()

    def exit_action_mode(self):
        print("[MAIN_WINDOW] Exiting action mode.")
        self.action_mode = False
        self.orb_target_pos = QPoint(self.center_x, self.center_y)
        self.orb_target_scale = 1.0
        self.orb_renderer.set_action_mode(False)

    def toggle_listening(self):
        self.is_listening = not self.is_listening
        print(f"[MAIN_WINDOW] Toggled listening to: {self.is_listening}")
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
        print("[MAIN_WINDOW] Close event received. Shutting down...")
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
        print("[APPLICATION] Starting main app window.")
        self.main_window = JarvisWindow(self.speech_engine)
        self.main_window.show()

    def run(self):
        self.app.aboutToQuit.connect(self.log_viewer.close)
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    main_app = Application()
    main_app.run()
