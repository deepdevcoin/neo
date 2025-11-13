import vosk
import sounddevice as sd
import json
from PyQt5.QtCore import QObject, pyqtSignal
import threading
import os
import numpy as np
import torch

class SpeechEngine(QObject):
    speech_recognized = pyqtSignal(str)
    tts_started = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.recognizer = None
        self.is_recognizing = False
        self.tts_engine = None
        self.gpt4all_model = None
        self._stop_flag = False
        self._init_recognition()
        self._init_tts()
        self._init_gpt4all()
        self._recognition_thread = None
    
    def _init_recognition(self):
        try:
            vosk.SetLogLevel(-1)
            
            model_path = "models/vosk-model-en-us-0.22"
            if not os.path.exists(model_path):
                print(f"[ERROR] Model not found at {model_path}")
                print("[JARVIS] [INFO] Download from: https://alphacephei.com/vosk/models")
                return
            
            model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(model, 16000)
            print("[JARVIS] Speech recognition ready (using vosk-model-en-us-0.22)")
        except Exception as e:
            print(f"[ERROR] Speech recognition init failed: {e}")
    
    def _init_tts(self):
        try:
            from TTS.api import TTS
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.tts_engine = TTS(model_name="tts_models/en/ljspeech/glow-tts", gpu=(device == "cuda"))
            print("[JARVIS] Coqui TTS initialized successfully")
        except ImportError as e:
            print(f"[WARNING] Coqui TTS not available: {e}")
            print("[JARVIS] [INFO] Trying fallback pyttsx3...")
            self._init_pyttsx3()
        except Exception as e:
            print(f"[WARNING] Coqui TTS init failed: {e}")
            print("[JARVIS] [INFO] Trying fallback pyttsx3...")
            self._init_pyttsx3()
    
    def _init_pyttsx3(self):
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            print("[JARVIS] pyttsx3 TTS initialized (fallback)")
        except Exception as e2:
            print(f"[ERROR] TTS initialization failed: {e2}")
    
    def _init_gpt4all(self):
        try:
            from gpt4all import GPT4All
            print("[JARVIS] Loading GPT4All model... (this may take a moment)")
            self.gpt4all_model = GPT4All("orca-mini-3b")
            print("[JARVIS] GPT4All model loaded successfully")
        except Exception as e:
            print(f"[WARNING] GPT4All init failed: {e}")
            print("[JARVIS] [INFO] Will use fallback responses")
    
    def start(self):
        if not self.recognizer:
            print("[JARVIS] [ERROR] Speech recognizer not initialized")
            return
        
        self._stop_flag = False
        
        def recognition_loop():
            try:
                with sd.RawInputStream(
                    samplerate=16000,
                    blocksize=8000,
                    channels=1,
                    dtype='int16'
                ) as stream:
                    print("[JARVIS] Speech recognition stream started")
                    while not self._stop_flag:
                        data = stream.read(4000)[0]
                        if self.is_recognizing:
                            try:
                                audio_bytes = np.asarray(data, dtype=np.int16).tobytes()
                                if self.recognizer.AcceptWaveform(audio_bytes):
                                    result = json.loads(self.recognizer.Result())
                                    if 'text' in result and result['text']:
                                        text = result['text']
                                        print(f"[JARVIS] Speech recognized: {text}")
                                        self.speech_recognized.emit(text)
                            except Exception as e:
                                print(f"[ERROR] Recognition error: {e}")
            except Exception as e:
                print(f"[ERROR] Audio stream error: {e}")

        self._recognition_thread = threading.Thread(target=recognition_loop, daemon=True)
        self._recognition_thread.start()
    
    def stop(self):
        self.running = False  # flag to stop loops
        self._stop_flag = True
        if self._recognition_thread:
            self._recognition_thread.join()
        if self.tts_engine:
            if hasattr(self.tts_engine, "stop"):
                self.tts_engine.stop()
    
    def start_recognition(self):
        self.is_recognizing = True
        print("[JARVIS] Recognition enabled")
    
    def stop_recognition(self):
        self.is_recognizing = False
        print("[JARVIS] Recognition disabled")
    
    def speak(self, text):
        if not self.tts_engine:
            print("[JARVIS] [ERROR] TTS engine not initialized")
            return
        
        try:
            self.tts_started.emit(text)
            
            def run_tts():
                try:
                    if hasattr(self.tts_engine, 'tts_to_file'):
                        self.tts_engine.tts_to_file(text=text, file_path="/tmp/jarvis_tts.wav")
                        import subprocess
                        subprocess.run(['ffplay', '-nodisp', '-autoexit', '/tmp/jarvis_tts.wav'],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        self.tts_engine.say(text)
                        self.tts_engine.runAndWait()
                except Exception as e:
                    print(f"[ERROR] TTS execution error: {e}")
            
            thread = threading.Thread(target=run_tts, daemon=True)
            thread.start()
        except Exception as e:
            print(f"[ERROR] TTS error: {e}")
    
    def generate_response(self, text):
        if self.gpt4all_model:
            try:
                print(f"[JARVIS] Generating response for: {text}")
                response = self.gpt4all_model.generate(
                    prompt=f"You are Jarvis, an AI assistant. Respond briefly (1-2 sentences) to: {text}",
                    max_tokens=100,
                    temp=0.7
                )
                print(f"[JARVIS] Generated response: {response}")
                return response.strip()
            except Exception as e:
                print(f"[ERROR] GPT4All generation error: {e}")
                return "I apologize, sir. I encountered an error processing your request."
        else:
            import random
            responses = [
                "Very good, sir. Processing your request.",
                "Right away, sir.",
                "Certainly, sir. I shall attend to that.",
                "As you wish, sir.",
                "I am at your service.",
                "Acknowledged, sir.",
                "I shall see to it at once, sir.",
            ]
            return random.choice(responses)
