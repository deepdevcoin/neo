"""
Audio Listener - Captures microphone input and calculates amplitude
"""

import sounddevice as sd
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import queue


class AudioListener(QObject):
    amplitude_changed = pyqtSignal(float)
    
    def __init__(self, sample_rate=44100, block_size=1024):
        super().__init__()
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.audio_queue = queue.Queue()
        self.running = True
        self.stream = None
        
        # Smoothing parameters
        self.smoothed_amplitude = 0.0
        self.smoothing_factor = 0.3
        
        self.start()
        
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            print(f"Audio status: {status}")
        
        # Calculate RMS amplitude
        amplitude = np.sqrt(np.mean(indata**2))
        
        # Smooth the amplitude
        self.smoothed_amplitude = (
            self.smoothing_factor * amplitude + 
            (1 - self.smoothing_factor) * self.smoothed_amplitude
        )
        
        # Normalize to 0-1 range (assuming typical speech is < 0.1 RMS)
        normalized = min(self.smoothed_amplitude * 10, 1.0)
        
        # Emit signal
        self.amplitude_changed.emit(normalized)
        
    def start(self):
        """Start capturing audio"""
        try:
            self.stream = sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                callback=self.audio_callback
            )
            self.stream.start()
            print("🎤 Audio listener started")
        except Exception as e:
            print(f"❌ Failed to start audio listener: {e}")
            print("Make sure your microphone is connected and accessible")
            
    def stop(self):
        """Stop capturing audio"""
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        print("🔇 Audio listener stopped")
        
    def get_amplitude(self):
        """Get current smoothed amplitude"""
        return self.smoothed_amplitude