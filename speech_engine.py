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
        self.gpt4all_model = None
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

    def init_gpt4all(self):
        print("[SPEECH_ENGINE] init_gpt4all started.")
        try:
            from gpt4all import GPT4All
            import shutil
            import pathlib

            # Create local model directory in user home
            model_dir = pathlib.Path.home() / ".local" / "share" / "jarvis" / "models"
            model_dir.mkdir(parents=True, exist_ok=True)

            local_model_path = model_dir / "Phi-3-mini-4k-instruct-q4.gguf"

            # Check external drive path (original location)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            external_model_path = os.path.join(base_dir, "models", "Phi-3-mini-4k-instruct-q4.gguf")

            model_found = False

            # Try local path first (fast)
            if local_model_path.exists():
                model_path = str(local_model_path)
                print(f"[SPEECH_ENGINE] Using local model from: {model_path}")
                model_found = True
            # Try external path (slow)
            elif os.path.exists(external_model_path):
                model_path = external_model_path
                print(f"[SPEECH_ENGINE] Using external model from: {model_path}")
                print(f"[SPEECH_ENGINE] WARNING: External drive detected. Copying to local storage for better performance...")
                try:
                    shutil.copy2(external_model_path, local_model_path)
                    model_path = str(local_model_path)
                    print(f"[SPEECH_ENGINE] Model copied to local storage: {model_path}")
                    model_found = True
                except Exception as copy_error:
                    print(f"[SPEECH_ENGINE WARNING] Failed to copy model: {copy_error}. Using external path.")
                    model_found = True
            else:
                print(f"[SPEECH_ENGINE WARNING] GPT4All model not found at any location.")
                print(f"[SPEECH_ENGINE] Searched paths:")
                print(f"  - Local: {local_model_path}")
                print(f"  - External: {external_model_path}")
                self.gpt4all_model = None
                return

            # Load model with optimized settings
            print(f"[SPEECH_ENGINE] Attempting to load GPT4All model from: {model_path}")

            # Validate model file size (should be ~2.5GB for Phi-3-mini-4k-instruct-q4)
            model_size = os.path.getsize(model_path) / (1024**3)  # GB
            if model_size < 1.0:  # Less than 1GB is likely wrong model
                print(f"[SPEECH_ENGINE WARNING] Model file seems too small: {model_size:.2f}GB")

            self.gpt4all_model = GPT4All(model_path, allow_download=False)
            print("[SPEECH_ENGINE] GPT4All AI brain loaded successfully.")
        except Exception as e:
            print(f"[SPEECH_ENGINE WARNING] GPT4All init failed: {e}. Using fallback responses.")
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

    def generate_response(self, prompt: str) -> str:
        print(f"[SPEECH_ENGINE] generate_response called with prompt: '{prompt}'")
        self.generation_started.emit()
        generation_start_time = time.time()

        if self.gpt4all_model:
            print("[SPEECH_ENGINE] GPT4All model found, proceeding with generation.")
            try:
                full_response = ""
                print("[SPEECH_ENGINE] Calling gpt4all_model.generate with streaming...")
                response_generator = self.gpt4all_model.generate(
                    prompt=f"User: {prompt}\nJarvis:",
                    max_tokens=150, temp=0.7, streaming=True
                )
                
                token_count = 0
                last_token_time = time.time()
                first_token_time = None

                for token in response_generator:
                    if first_token_time is None:
                        first_token_time = time.time()
                        print(f"[PERF] Time to first token: {first_token_time - generation_start_time:.2f} seconds.")

                    current_time = time.time()
                    time_since_last_token = current_time - last_token_time
                    print(f"[PERF] Time since last token: {time_since_last_token:.2f} seconds.")
                    last_token_time = current_time

                    token_count += 1
                    full_response += token
                    self.response_chunk_ready.emit(token)
                
                if token_count == 0:
                    print("[SPEECH_ENGINE WARNING] Streaming finished but received 0 tokens.")
                else:
                    total_generation_time = time.time() - generation_start_time
                    print(f"[PERF] Streaming finished. Total tokens: {token_count}, Total time: {total_generation_time:.2f} seconds.")

                print(f"[SPEECH_ENGINE] Full response after streaming: '{full_response.strip()}'")
                return full_response.strip()
            except Exception as e:
                print(f"[SPEECH_ENGINE ERROR] GPT4All generation failed: {e}")
        else:
            print("[SPEECH_ENGINE] No GPT4All model. Using fallback response.")
        
        # Fallback response with simulated streaming
        import random
        fallback_response = random.choice(["Acknowledged.", "At once, sir.", "As you wish."])
        print(f"[SPEECH_ENGINE] Fallback response: '{fallback_response}'")
        for char in fallback_response:
            self.response_chunk_ready.emit(char)
            time.sleep(0.05)
        return fallback_response
