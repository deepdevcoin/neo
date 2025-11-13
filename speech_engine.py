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
import shutil
import pygame

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
        self.audio_player_available = None # 'ffplay', 'pygame', or None
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
        # Health Check: Determine available audio players
        if shutil.which("ffplay"):
            self.audio_player_available = "ffplay"
            print("[HEALTH CHECK] ffplay dependency found. Will be used for audio playback.")
        else:
            try:
                pygame.mixer.init()
                self.audio_player_available = "pygame"
                print("[HEALTH CHECK] ffplay not found. Pygame will be used as fallback for audio.")
            except Exception as e:
                self.audio_player_available = None
                print(f"[HEALTH CHECK ERROR] ffplay not found and Pygame failed to initialize: {e}")

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
            # Section 1: Model Path Optimization
            model_name = "Phi-3-mini-4k-instruct-q4.gguf"
            # GPT4All handles caching in ~/.cache/gpt4all
            print(f"[SPEECH_ENGINE] Attempting to load/download GPT4All model: {model_name}")
            
            # Section 2: GPT4All Generation Optimization
            self.gpt4all_model = GPT4All(
                model_name, 
                allow_download=True, 
                n_threads=4,
                n_ctx=1024, # Context window optimization
                n_batch=8    # Batching optimization
            )
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
        print(f"[SPEECH_ENGINE] speak called with text: '{text[:30]}...'" if text else "[SPEECH_ENGINE] speak called with empty text.")
        if not self.tts_engine or not text or not self.audio_player_available:
            print("[SPEECH_ENGINE] speak aborted: TTS/audio player not ready or text is empty.")
            self.tts_finished.emit()
            return
        self.tts_started.emit(text)
        threading.Thread(target=self._tts_task, args=(text,), daemon=True).start()

    def _tts_task(self, text):
        print("[SPEECH_ENGINE] _tts_task started.")
        path = f"/tmp/jarvis_tts_{int(time.time())}.wav"
        try:
            if hasattr(self.tts_engine, "tts_to_file"):
                self.tts_engine.tts_to_file(text=text, file_path=path)
                print(f"[SPEECH_ENGINE] TTS audio written to {path}")

                # Section 3: TTS Audio Output Fix
                if self.audio_player_available == "ffplay":
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif self.audio_player_available == "pygame":
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                else:
                    print("[SPEECH_ENGINE ERROR] No audio player available for playback.")

            else: # Fallback to pyttsx3
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            print("[SPEECH_ENGINE] _tts_task finished successfully.")
        except Exception as e:
            print(f"[SPEECH_ENGINE ERROR] TTS execution failed: {e}")
        finally:
            # Section 3: Temporary file cleanup
            if os.path.exists(path):
                os.remove(path)
                print(f"[SPEECH_ENGINE] Cleaned up temporary file: {path}")
            self.tts_finished.emit()

    def generate_response(self, prompt: str) -> str:
        print(f"[SPEECH_ENGINE] generate_response called with prompt: '{prompt}'")
        self.generation_started.emit()
        generation_start_time = time.time()

        if self.gpt4all_model:
            try:
                full_response = ""
                print("[SPEECH_ENGINE] Calling gpt4all_model.generate with streaming...")
                
                # Section 2: GPT4All Generation Optimization
                response_generator = self.gpt4all_model.generate(
                    prompt=f"User: {prompt}\nJarvis:",
                    max_tokens=80, # Reduced for faster responses
                    temp=0.7, 
                    streaming=True
                )
                
                token_count = 0
                last_token_time = time.time()
                first_token_time = None

                for token in response_generator:
                    # Section 2: Add generation timeout
                    if time.time() - generation_start_time > 30:
                        print("[SPEECH_ENGINE ERROR] Generation timed out after 30 seconds.")
                        return "My apologies, the generation process took too long to complete."

                    if first_token_time is None:
                        first_token_time = time.time()
                        print(f"[PERF] Time to first token: {first_token_time - generation_start_time:.2f} seconds.")
                    
                    token_count += 1
                    full_response += token
                    self.response_chunk_ready.emit(token)
                    
                    if "<|assistant|>" in token or "<|endoftext|>" in token:
                        print(f"[SPEECH_ENGINE] End token '{token}' detected. Stopping generation.")
                        break
                
                total_generation_time = time.time() - generation_start_time
                print(f"[PERF] Streaming finished. Total tokens: {token_count}, Total time: {total_generation_time:.2f} seconds.")

                final_response = full_response.replace("<|assistant|>", "").replace("<|endoftext|>", "").strip()
                print(f"[SPEECH_ENGINE] Full response after cleanup: '{final_response}'")
                return final_response

            except Exception as e:
                print(f"[SPEECH_ENGINE ERROR] GPT4All generation failed: {e}")
                return "I seem to be having trouble processing that request."
        else:
            # Section 4: Fallback response
            print("[SPEECH_ENGINE] No GPT4All model. Using fallback response.")
            return "My AI core is not currently available."
