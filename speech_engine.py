"""
Enhanced Speech Recognition & TTS Engine
"""

import json
import os
import threading
import numpy as np
import sounddevice as sd
import vosk
import torch
from PyQt5.QtCore import QObject, pyqtSignal

class SpeechEngine(QObject):
    speech_recognized = pyqtSignal(str)
    tts_started = pyqtSignal(str)
    tts_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = False
        self.recognizer = None
        self.tts_engine = None
        self.gpt4all_model = None
        self._thread = None
        self.recognition_active = False

    def init_recognition(self):
        try:
            vosk.SetLogLevel(-1)
            model_path = "models/vosk-model-en-us-0.22"
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Vosk model not found at {model_path}")
            model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(model, 16000)
            print("[JARVIS] Speech recognition ready.")
        except Exception as e:
            print(f"[ERROR] Vosk init failed: {e}")

    def init_tts(self):
        try:
            from TTS.api import TTS
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[JARVIS] TTS using device: {device}")
            self.tts_engine = TTS("tts_models/en/ljspeech/glow-tts", gpu=(device == "cuda"))
            print("[JARVIS] Coqui TTS initialized.")
        except Exception as e:
            print(f"[WARNING] Coqui TTS failed: {e}. Falling back to pyttsx3.")
            try:
                import pyttsx3
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty("rate", 150)
                print("[JARVIS] pyttsx3 fallback enabled.")
            except Exception as e2:
                print(f"[ERROR] pyttsx3 init failed: {e2}")

    def init_gpt4all(self):
        try:
            from gpt4all import GPT4All
            # Get absolute path relative to this file's directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(base_dir, "models", "Phi-3-mini-4k-instruct-q4.gguf")
            if not os.path.exists(model_path):
                print(f"[WARNING] GPT4All model not found at {model_path}. Using fallback responses.")
                self.gpt4all_model = None
                return
            self.gpt4all_model = GPT4All(model_path, allow_download=False)  # Prevent online fetches
            print("[JARVIS] GPT4All AI brain loaded.")
        except Exception as e:
            print(f"[WARNING] GPT4All init failed: {e}. Using fallback responses.")
            self.gpt4all_model = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

    def _listen_loop(self):
        if not self.recognizer:
            return
        print("[JARVIS] Audio stream started.")
        try:
            with sd.RawInputStream(samplerate=16000, blocksize=8000, channels=1, dtype="int16") as stream:
                while self.running:
                    if not self.recognition_active:
                        stream.read(stream.read_available)
                        threading.Event().wait(0.1)
                        continue

                    data, overflowed = stream.read(4000)
                    if self.recognizer.AcceptWaveform(bytes(data)):
                        result = json.loads(self.recognizer.Result())
                        if result.get("text"):
                            self.speech_recognized.emit(result["text"])
        except Exception as e:
            print(f"[ERROR] Audio stream failed: {e}")

    def start_recognition(self):
        self.recognition_active = True
        print("[JARVIS] Listening...")

    def stop_recognition(self):
        self.recognition_active = False
        print("[JARVIS] No longer listening.")

    def speak(self, text: str):
        if not self.tts_engine:
            return
        self.tts_started.emit(text)
        threading.Thread(target=self._tts_task, args=(text,), daemon=True).start()

    def _tts_task(self, text):
        try:
            if hasattr(self.tts_engine, "tts_to_file"):
                import subprocess
                path = "/tmp/jarvis_tts.wav"
                self.tts_engine.tts_to_file(text=text, file_path=path)
                subprocess.run(["ffplay", "-nodisp", "-autoexit", path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
        except Exception as e:
            print(f"[ERROR] TTS execution failed: {e}")
        finally:
            self.tts_finished.emit()

    def generate_response(self, prompt: str) -> str:
        if self.gpt4all_model:
            try:
                return self.gpt4all_model.generate(
                    prompt=f"User: {prompt}\nJarvis:",
                    max_tokens=100, temp=0.7
                ).strip()
            except Exception as e:
                print(f"[ERROR] GPT4All generation failed: {e}")
        import random
        return random.choice(["Acknowledged.", "At once, sir.", "As you wish."])
