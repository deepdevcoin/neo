"""
Real-time Audio Listener with improved amplitude detection
"""

import numpy as np
import sounddevice as sd
from PyQt5.QtCore import QObject, pyqtSignal
import queue


class AudioListener(QObject):
    amplitude_updated = pyqtSignal(float)
    
    def __init__(self, sample_rate=44100, chunk_size=2048):
        super().__init__()
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.stream = None
    
    def start(self):
        """Start audio capturing"""
        try:
            self.stream = sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=self._audio_callback
            )
            self.stream.start()
            self._listen_loop()
        except Exception as e:
            print(f"Audio error: {e}")
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(indata.copy())
    
    def _listen_loop(self):
        """Process audio and emit amplitude"""
        while True:
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
                if self.is_listening:
                    rms = np.sqrt(np.mean(audio_data ** 2))
                    self.amplitude_updated.emit(float(rms))
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Listener error: {e}")
                break
    
    def start_listening(self):
        """Activate listening mode"""
        self.is_listening = True
    
    def stop_listening(self):
        """Deactivate listening mode"""
        self.is_listening = False
    
    def stop(self):
        """Stop audio stream"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
