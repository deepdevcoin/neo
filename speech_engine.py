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
        self.tts_engine = None
        self.tts_method = "none"  # Track which TTS method is being used

        # Check for ffplay dependency
        self.ffplay_available = self._check_ffplay()
        if self.ffplay_available:
            print("[SPEECH_ENGINE] ffplay found - audio playback available")
        else:
            print("[SPEECH_ENGINE WARNING] ffplay not found - checking for pygame fallback")

        # Try pygame for audio playback fallback
        self.pygame_available = self._check_pygame()
        if self.pygame_available:
            print("[SPEECH_ENGINE] pygame found - fallback audio available")

        # Try Coqui TTS first (highest quality)
        try:
            from TTS.api import TTS
            device = "cpu"
            print(f"[JARVIS] TTS using device: {device}")
            self.tts_engine = TTS("tts_models/en/ljspeech/glow-tts", gpu=False)
            self.tts_engine.to(device)
            self.tts_method = "coqui"
            print("[SPEECH_ENGINE] Coqui TTS initialized successfully.")
            return
        except Exception as e:
            print(f"[SPEECH_ENGINE WARNING] Coqui TTS failed: {e}. Trying fallback...")

        # Fallback to pyttsx3 (system TTS)
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty("rate", 150)
            self.tts_engine.setProperty("volume", 0.9)
            self.tts_method = "pyttsx3"
            print("[SPEECH_ENGINE] pyttsx3 fallback enabled.")
            return
        except Exception as e2:
            print(f"[SPEECH_ENGINE ERROR] pyttsx3 init failed: {e2}")

        print("[SPEECH_ENGINE ERROR] No TTS engine available - speech output will not work")

    def _check_ffplay(self) -> bool:
        """Check if ffplay is available for audio playback."""
        try:
            import subprocess
            result = subprocess.run(['ffplay', '-version'],
                                  capture_output=True, text=True, timeout=3)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            return False

    def _check_pygame(self) -> bool:
        """Check if pygame is available for audio playback."""
        try:
            import pygame
            pygame.mixer.init()
            return True
        except Exception:
            return False

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
        print(f"[SPEECH_ENGINE] _tts_task started with method: {self.tts_method}")
        try:
            if self.tts_method == "coqui":
                self._tts_coqui(text)
            elif self.tts_method == "pyttsx3":
                self._tts_pyttsx3(text)
            else:
                print("[SPEECH_ENGINE ERROR] No TTS method available")
                return

            print("[SPEECH_ENGINE] _tts_task finished successfully.")
        except Exception as e:
            print(f"[SPEECH_ENGINE ERROR] TTS execution failed: {e}")
            # Try fallback if primary method fails
            if self.tts_method != "pyttsx3":
                self._try_tts_fallback(text)
        finally:
            self.tts_finished.emit()

    def _tts_coqui(self, text):
        """Handle Coqui TTS with multiple playback options."""
        import subprocess
        import os
        path = "/tmp/jarvis_tts.wav"

        try:
            # Generate audio file
            self.tts_engine.tts_to_file(text=text, file_path=path)
            print(f"[SPEECH_ENGINE] Audio file generated: {path}")

            # Try playback methods in order of preference
            if self.ffplay_available:
                self._play_with_ffplay(path)
            elif self.pygame_available:
                self._play_with_pygame(path)
            else:
                print("[SPEECH_ENGINE WARNING] No audio playback method available")
                self._show_audio_file_info(path)

        except Exception as e:
            print(f"[SPEECH_ENGINE ERROR] Coqui TTS failed: {e}")
            raise

    def _tts_pyttsx3(self, text):
        """Handle pyttsx3 TTS."""
        print("[SPEECH_ENGINE] Using pyttsx3 for speech")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def _play_with_ffplay(self, audio_path):
        """Play audio using ffplay."""
        import subprocess
        try:
            subprocess.run([
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", audio_path
            ], check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[SPEECH_ENGINE] Audio played with ffplay")
        except subprocess.TimeoutExpired:
            print("[SPEECH_ENGINE WARNING] ffplay playback timed out")
        except FileNotFoundError:
            print("[SPEECH_ENGINE ERROR] ffplay not found during playback")
        except Exception as e:
            print(f"[SPEECH_ENGINE ERROR] ffplay playback failed: {e}")
            raise

    def _play_with_pygame(self, audio_path):
        """Play audio using pygame."""
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            print("[SPEECH_ENGINE] Audio playing with pygame")

            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                import time
                time.sleep(0.1)

        except Exception as e:
            print(f"[SPEECH_ENGINE ERROR] pygame playback failed: {e}")
            raise

    def _show_audio_file_info(self, audio_path):
        """Show information about the generated audio file when playback fails."""
        import os
        if os.path.exists(audio_path):
            size = os.path.getsize(audio_path)
            print(f"[SPEECH_ENGINE] Audio file created but cannot be played: {audio_path} ({size} bytes)")
            print("[SPEECH_ENGINE] Install ffmpeg for audio playback: sudo apt install ffmpeg")

    def _try_tts_fallback(self, text):
        """Try fallback TTS method if primary fails."""
        print("[SPEECH_ENGINE] Trying TTS fallback method...")
        try:
            if self.tts_method != "pyttsx3":
                # Try to initialize pyttsx3 as fallback
                import pyttsx3
                fallback_engine = pyttsx3.init()
                fallback_engine.setProperty("rate", 150)
                fallback_engine.say(text)
                fallback_engine.runAndWait()
                print("[SPEECH_ENGINE] Fallback TTS successful")
        except Exception as e:
            print(f"[SPEECH_ENGINE ERROR] Fallback TTS also failed: {e}")

    def generate_response(self, prompt: str) -> str:
        print(f"[SPEECH_ENGINE] generate_response called with prompt: '{prompt}'")
        self.generation_started.emit()
        generation_start_time = time.time()

        # Check available memory
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            print(f"[MEMORY] Available: {available_gb:.1f}GB, Used: {memory.percent}%")
            if available_gb < 2.0:
                print(f"[MEMORY] WARNING: Low memory condition detected - using ultra-fast mode")
        except:
            print("[MEMORY] Could not check memory usage")

        if self.gpt4all_model:
            print("[SPEECH_ENGINE] GPT4All model found, proceeding with generation.")
            try:
                full_response = ""
                print("[SPEECH_ENGINE] Calling gpt4all_model.generate with optimized parameters...")

                # Ultra-minimal parameters for extremely low memory systems
                response_generator = self.gpt4all_model.generate(
                    prompt=f"User: {prompt}\nJarvis:",
                    max_tokens=15,  # Very short responses to save memory
                    temp=0.5,      # Lower temperature for more predictable responses
                    streaming=False  # Disable streaming to save memory
                )

                # Handle non-streaming response (much lower memory usage)
                full_response = response_generator  # For non-streaming, this is already the full response
                token_count = len(full_response.split()) if full_response else 0
                print(f"[MEMORY-EFFICIENT] Generated {token_count} tokens using non-streaming mode")

                # Simulate streaming for UI compatibility
                if full_response:
                    for char in full_response:
                        self.response_chunk_ready.emit(char)
                        time.sleep(0.01)  # Very fast simulation

                if token_count == 0:
                    print("[SPEECH_ENGINE WARNING] Generation finished but received 0 tokens.")
                else:
                    total_generation_time = time.time() - generation_start_time
                    print(f"[PERF] Generation finished. Total tokens: {token_count}, Total time: {total_generation_time:.2f} seconds.")
                    if total_generation_time < 15:
                        print(f"[SPEED] Good performance: {total_generation_time:.1f}s for {token_count} tokens")
                    else:
                        print(f"[SPEED] Generation took {total_generation_time:.2f} seconds - consider closing other applications")

                # Ensure we have a response
                if not full_response.strip():
                    print("[SPEECH_ENGINE WARNING] Empty response, using fallback")
                    return self._get_fallback_response()

                print(f"[SPEECH_ENGINE] Full response after streaming: '{full_response.strip()}'")
                return full_response.strip()
            except Exception as e:
                print(f"[SPEECH_ENGINE ERROR] GPT4All generation failed: {e}")
                print(f"[SPEECH_ENGINE INFO] Trying with minimal parameters...")
                try:
                    # Fallback to ultra-basic non-streaming mode
                    response = self.gpt4all_model.generate(
                        prompt=f"User: {prompt}\nJarvis:",
                        max_tokens=10,  # Extremely short responses
                        temp=0.3,      # Very predictable responses
                        streaming=False  # Non-streaming to save memory
                    )

                    if response and response.strip():
                        token_count = len(response.split())
                        print(f"[MEMORY-EFFICIENT] Fallback mode generated {token_count} tokens")

                        # Simulate streaming for UI
                        for char in response:
                            self.response_chunk_ready.emit(char)
                            time.sleep(0.01)

                        return response.strip()
                except Exception as e2:
                    print(f"[SPEECH_ENGINE ERROR] Minimal generation also failed: {e2}")

                return self._get_fallback_response()
        else:
            print("[SPEECH_ENGINE] No GPT4All model. Using fallback response.")

        return self._get_fallback_response()

    def _get_fallback_response(self) -> str:
        """Get a fallback response with simulated streaming."""
        import random
        fallback_responses = [
            "I'm here to assist you.",
            "How can I help you today?",
            "I understand. What would you like me to do?",
            "Acknowledged. I'm ready to help.",
            "I'm processing your request."
        ]
        fallback_response = random.choice(fallback_responses)
        print(f"[SPEECH_ENGINE] Fallback response: '{fallback_response}'")

        # Simulate streaming for fallbacks
        for char in fallback_response:
            self.response_chunk_ready.emit(char)
            time.sleep(0.02)  # Faster streaming for fallbacks

        return fallback_response
