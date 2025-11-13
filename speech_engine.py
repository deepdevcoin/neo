"""
Enhanced Speech Recognition & TTS Engine
Offline Vosk + Coqui TTS + GPT4All (mistral-7b-openorca.Q4_0.gguf)
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

    def __init__(self):
        super().__init__()
        self.running = False
        self.recognizer = None
        self.tts_engine = None
        self.gpt4all_model = None

        self._init_recognition()
        self._init_tts()
        self._init_gpt4all()

        self._thread = None

    # ---------------------------------------------------
    # Initialization
    # ---------------------------------------------------
    def _init_recognition(self):
        try:
            vosk.SetLogLevel(-1)
            model_path = "models/vosk-model-en-us-0.22"
            if not os.path.exists(model_path):
                print(f"[ERROR] Missing Vosk model at {model_path}")
                return
            model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(model, 16000)
            print("[JARVIS] Speech recognition ready (vosk-model-en-us-0.22)")
        except Exception as e:
            print(f"[ERROR] Vosk init failed: {e}")

    def _init_tts(self):
        try:
            from TTS.api import TTS
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.tts_engine = TTS("tts_models/en/ljspeech/glow-tts", gpu=(device == "cuda"))
            print("[JARVIS] Coqui TTS initialized successfully")
        except Exception as e:
            print(f"[WARNING] Coqui TTS init failed: {e}")
            print("[INFO] Falling back to pyttsx3…")
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty("rate", 150)
                engine.setProperty("volume", 0.9)
                self.tts_engine = engine
                print("[JARVIS] pyttsx3 fallback initialized")
            except Exception as e2:
                print(f"[ERROR] pyttsx3 init failed: {e2}")

    def _init_gpt4all(self):
        try:
            from gpt4all import GPT4All
            model_path = os.path.join("models", "mistral-7b-openorca.Q4_0.gguf")
            print(f"[JARVIS] Loading GPT4All model from {model_path} …")
            if not os.path.exists(model_path):
                print(f"[WARNING] GPT4All model missing at {model_path}")
                self.gpt4all_model = None
                return
            self.gpt4all_model = GPT4All(model_path)
            print("[JARVIS] GPT4All model loaded")
        except Exception as e:
            print(f"[WARNING] GPT4All init failed: {e}")
            self.gpt4all_model = None

    # ---------------------------------------------------
    # Recognition loop management
    # ---------------------------------------------------
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self.running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
            print("[JARVIS] Speech thread stopped")

    def _listen_loop(self):
        if not self.recognizer:
            print("[ERROR] Speech recognizer unavailable")
            return
        print("[JARVIS] Speech recognition stream started")
        try:
            with sd.RawInputStream(
                samplerate=16000, blocksize=8000, channels=1, dtype="int16"
            ) as stream:
                while self.running:
                    data = stream.read(4000)[0]
                    if not self.running:
                        break
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "").strip()
                        if text:
                            print(f"[JARVIS] Heard: {text}")
                            self.speech_recognized.emit(text)
        except Exception as e:
            print(f"[ERROR] Audio stream error: {e}")
        print("[JARVIS] Exiting recognition loop")

    # ---------------------------------------------------
    # Recognition control
    # ---------------------------------------------------
    def start_recognition(self):
        self.running = True
        print("[JARVIS] Recognition enabled")

    def stop_recognition(self):
        self.running = False
        print("[JARVIS] Recognition disabled")

    # ---------------------------------------------------
    # Text-to-Speech
    # ---------------------------------------------------
    def speak(self, text: str):
        if not self.tts_engine:
            print("[ERROR] No TTS engine")
            return

        self.tts_started.emit(text)

        def _tts_task():
            try:
                if hasattr(self.tts_engine, "tts_to_file"):
                    # Coqui
                    path = "/tmp/jarvis_tts.wav"
                    self.tts_engine.tts_to_file(text=text, file_path=path)
                    import subprocess
                    subprocess.run(
                        ["ffplay", "-nodisp", "-autoexit", path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    # pyttsx3 fallback
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
            except Exception as e:
                print(f"[ERROR] TTS error: {e}")

        threading.Thread(target=_tts_task, daemon=True).start()

    # ---------------------------------------------------
    # Response generation
    # ---------------------------------------------------
    def generate_response(self, prompt: str) -> str:
        if self.gpt4all_model:
            try:
                print(f"[JARVIS] Generating response for: {prompt}")
                response = self.gpt4all_model.generate(
                    prompt=f"You are Jarvis, an AI assistant inspired by Iron Man's JARVIS. "
                           f"Keep replies formal and concise.\nUser: {prompt}\nJarvis:",
                    max_tokens=100,
                    temp=0.7,
                )
                return response.strip()
            except Exception as e:
                print(f"[ERROR] GPT4All generation failed: {e}")
        # fallback responses
        import random
        responses = [
            "Acknowledged, sir.",
            "At once, sir.",
            "Right away, sir.",
            "Certainly, sir.",
            "I shall attend to that immediately, sir.",
        ]
        return random.choice(responses)
