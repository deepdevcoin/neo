"""
Enhanced Speech Recognition & TTS Engine
"""

import json
import os
import threading
import time
import numpy as np
import sounddevice as sd
import vosk
import torch
from PyQt5.QtCore import QObject, pyqtSignal
import requests

class SpeechEngine(QObject):
    speech_recognized = pyqtSignal(str)
    tts_started = pyqtSignal(str)
    tts_finished = pyqtSignal()
    generation_started = pyqtSignal()
    response_chunk_ready = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        print("[SPEECH_ENGINE] Initializing...")
        self.running = False
        self.recognizer = None
        self.tts_engine = None
        self._thread = None
        self.recognition_active = False
        print("[SPEECH_ENGINE] Initialization complete.")

    def init_recognition(self):
        print("[SPEECH_ENGINE] init_recognition started.")
        try:
            vosk.SetLogLevel(-1)
            model_path = "models/vosk-model-en-us-0.22"
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Vosk model not found at {model_path}")
            model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(model, 16000)
            print("[SPEECH_ENGINE] init_recognition successful.")
        except Exception as e:
            print(f"[SPEECH_ENGINE ERROR] Vosk init failed: {e}")

    def init_tts(self):
        print("[SPEECH_ENGINE] init_tts started.")
        try:
            from TTS.api import TTS
            device = "cpu"
            print(f"[JARVIS] TTS using device: {device}")
            self.tts_engine = TTS("tts_models/en/ljspeech/glow-tts", gpu=False)
            self.tts_engine.to(device)
            print("[SPEECH_ENGINE] init_tts successful.")
        except Exception as e:
            print(f"[SPEECH_ENGINE WARNING] Coqui TTS failed: {e}. Falling back to pyttsx3.")
            try:
                import pyttsx3
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty("rate", 150)
                print("[JARVIS] pyttsx3 fallback enabled.")
            except Exception as e2:
                print(f"[SPEECH_ENGINE ERROR] pyttsx3 init failed: {e2}")

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
        print(f"[SPEECH_ENGINE] speak called with text: '{text[:30]}...'")
        if not self.tts_engine or not text:
            print("[SPEECH_ENGINE] speak aborted: TTS engine not ready or text is empty.")
            return
        self.tts_started.emit(text)
        threading.Thread(target=self._tts_task, args=(text,), daemon=True).start()

    def _tts_task(self, text):
        print("[SPEECH_ENGINE] _tts_task started.")
        try:
            if hasattr(self.tts_engine, "tts_to_file"):
                import subprocess
                path = "/tmp/jarvis_tts.wav"
                self.tts_engine.tts_to_file(text=text, file_path=path)
                subprocess.run(["ffplay", "-nodisp", "-autoexit", path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            print("[SPEECH_ENGINE] _tts_task finished successfully.")
        except Exception as e:
            print(f"[SPEECH_ENGINE ERROR] TTS execution failed: {e}")
        finally:
            self.tts_finished.emit()

    def ask_ollama(self, prompt):
        payload = {
            "model": "gemma:2b",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": True
        }

        response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            stream=True
        )

        final_text = ""

        for line in response.iter_lines():
            if not line:
                continue

            data = json.loads(line.decode("utf-8"))

            if "message" in data and "content" in data["message"]:
                token = data["message"]["content"]
                self.response_chunk_ready.emit(token)
                final_text += token

            if data.get("done"):
                break

        return final_text

    def generate_response(self, prompt: str) -> str:
        print(f"[SPEECH_ENGINE] generate_response called with prompt: '{prompt}'")
        self.generation_started.emit()
        try:
            return self.ask_ollama(prompt)
        except Exception as e:
            print(f"[SPEECH_ENGINE ERROR] Ollama generation failed: {e}")
            # Fallback response with simulated streaming
            import random
            fallback_response = random.choice(["Acknowledged.", "At once, sir.", "As you wish."])
            print(f"[SPEECH_ENGINE] Fallback response: '{fallback_response}'")
            for char in fallback_response:
                self.response_chunk_ready.emit(char)
                time.sleep(0.05)
            return fallback_response
