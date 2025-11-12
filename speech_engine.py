"""
Speech Engine - Handles speech recognition (Vosk) and text-to-speech
"""

import os
import json
import wave
import threading
import sounddevice as sd
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from vosk import Model, KaldiRecognizer
import pyttsx3


class SpeechEngine(QObject):
    speech_recognized = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # TTS engine
        self.tts_engine = None
        self.init_tts()
        
        # Speech recognition
        self.vosk_model = None
        self.recognizer = None
        self.recognition_thread = None
        self.is_listening = False
        
        # Audio settings
        self.sample_rate = 16000
        self.block_size = 4000
        
        self.init_vosk()
        
    def init_tts(self):
        """Initialize text-to-speech engine"""
        try:
            self.tts_engine = pyttsx3.init()
            
            # Configure voice (try to find a suitable voice)
            voices = self.tts_engine.getProperty('voices')
            # Try to find a male voice for Jarvis-like effect
            for voice in voices:
                if 'male' in voice.name.lower() and 'female' not in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            
            # Set speech rate
            self.tts_engine.setProperty('rate', 175)  # Slightly slower for clarity
            self.tts_engine.setProperty('volume', 0.9)
            
            print("🔊 TTS engine initialized")
        except Exception as e:
            print(f"❌ TTS initialization failed: {e}")
            
    def init_vosk(self):
        """Initialize Vosk speech recognition"""
        try:
            # Check for Vosk model
            model_path = "model"  # Default path, user should download model
            
            if not os.path.exists(model_path):
                print("⚠️  Vosk model not found!")
                print("Please download a model from https://alphacephei.com/vosk/models")
                print("Extract it and name the folder 'model' in the project directory")
                print("For English, download 'vosk-model-small-en-us-0.15'")
                return
                
            self.vosk_model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.vosk_model, self.sample_rate)
            self.recognizer.SetWords(True)
            
            print("🧠 Vosk speech recognition initialized")
        except Exception as e:
            print(f"❌ Vosk initialization failed: {e}")
            
    def start_listening(self):
        """Start speech recognition in background thread"""
        if not self.vosk_model:
            print("⚠️  Speech recognition not available (model not loaded)")
            return
            
        if self.is_listening:
            return
            
        self.is_listening = True
        self.recognition_thread = threading.Thread(target=self._recognition_loop, daemon=True)
        self.recognition_thread.start()
        
    def stop_listening(self):
        """Stop speech recognition"""
        self.is_listening = False
        
    def _recognition_loop(self):
        """Main recognition loop (runs in separate thread)"""
        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                dtype='int16',
                channels=1
            ) as stream:
                print("🎤 Listening for speech...")
                
                while self.is_listening:
                    data = stream.read(self.block_size)[0]
                    
                    if self.recognizer.AcceptWaveform(bytes(data)):
                        result = json.loads(self.recognizer.Result())
                        text = result.get('text', '')
                        
                        if text:
                            self.speech_recognized.emit(text)
                            
                # Final result
                result = json.loads(self.recognizer.FinalResult())
                text = result.get('text', '')
                if text:
                    self.speech_recognized.emit(text)
                    
        except Exception as e:
            print(f"❌ Recognition error: {e}")
            self.is_listening = False
            
    def speak(self, text):
        """Speak text using TTS"""
        if not self.tts_engine:
            print(f"TTS not available. Would say: {text}")
            return
            
        try:
            # Run TTS in separate thread to avoid blocking
            def _speak():
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                
            thread = threading.Thread(target=_speak, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"❌ TTS error: {e}")
            
    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass