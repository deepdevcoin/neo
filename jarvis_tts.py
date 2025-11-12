"""
jarvis_tts.py
=============
Coqui TTS Handler for JARVIS Voice

REQUIREMENTS:
pip install TTS soundfile sounddevice numpy

Features:
- Coqui TTS with natural male voice
- Offline voice synthesis
- Clear, calm tone for JARVIS-style responses
"""

import os
import threading
import tempfile
from pathlib import Path

try:
    from TTS.api import TTS
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️  Coqui TTS not available. Install: pip install TTS soundfile sounddevice numpy")


class JarvisTTS:
    """
    JARVIS-style voice synthesis using Coqui TTS.
    
    Uses a clear, calm male voice optimized for AI assistant responses.
    """
    
    def __init__(self, use_gpu=False):
        self.tts = None
        self.use_gpu = use_gpu
        self.is_speaking = False
        
        # Callbacks
        self.on_start = None
        self.on_end = None
        
        if TTS_AVAILABLE:
            self.initialize()
    
    def initialize(self):
        """Initialize Coqui TTS with optimal model for JARVIS voice."""
        try:
            print("🔊 Initializing JARVIS Voice System...")
            
            # Use VCTK multi-speaker model with male speaker
            # This gives us a clear, professional male voice
            model_name = "tts_models/en/vctk/vits"
            
            self.tts = TTS(model_name=model_name, progress_bar=False, gpu=self.use_gpu)
            
            # Set speaker - p270 is a clear male voice
            self.speaker = "p270"
            
            print(f"✅ JARVIS Voice Online: {model_name}")
            print(f"   Speaker: {self.speaker} (Male, Clear)")
            
        except Exception as e:
            print(f"❌ Voice system initialization failed: {e}")
            print("   Attempting fallback model...")
            
            try:
                # Fallback to fast_pitch model
                model_name = "tts_models/en/ljspeech/fast_pitch"
                self.tts = TTS(model_name=model_name, progress_bar=False, gpu=self.use_gpu)
                self.speaker = None
                print(f"✅ JARVIS Voice Online (Fallback): {model_name}")
            except:
                print("❌ All voice models failed")
                self.tts = None
    
    def speak(self, text, blocking=False):
        """
        Generate and play JARVIS-style speech.
        
        Args:
            text: Text to speak
            blocking: If True, wait for speech to finish
        """
        if not self.tts:
            print(f"Voice system offline: {text}")
            return
        
        if blocking:
            self._generate_and_play(text)
        else:
            thread = threading.Thread(target=self._generate_and_play, args=(text,))
            thread.daemon = True
            thread.start()
    
    def _generate_and_play(self, text):
        """Generate audio and play it."""
        try:
            self.is_speaking = True
            if self.on_start:
                self.on_start()
            
            # Generate audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            print(f"🎙️  JARVIS: {text[:60]}...")
            
            # Generate with speaker if available
            if self.speaker:
                self.tts.tts_to_file(text=text, file_path=tmp_path, speaker=self.speaker)
            else:
                self.tts.tts_to_file(text=text, file_path=tmp_path)
            
            # Play audio
            self._play_audio(tmp_path)
            
            # Cleanup
            try:
                os.unlink(tmp_path)
            except:
                pass
            
        except Exception as e:
            print(f"❌ Voice synthesis error: {e}")
        finally:
            self.is_speaking = False
            if self.on_end:
                self.on_end()
    
    def _play_audio(self, audio_path):
        """Play audio file using sounddevice."""
        try:
            # Load audio
            data, samplerate = sf.read(audio_path)
            
            # Normalize audio
            if np.max(np.abs(data)) > 0:
                data = data / np.max(np.abs(data)) * 0.8
            
            # Play
            sd.play(data, samplerate)
            sd.wait()
            
        except Exception as e:
            print(f"❌ Audio playback error: {e}")
    
    def stop(self):
        """Stop current speech."""
        try:
            sd.stop()
            self.is_speaking = False
            if self.on_end:
                self.on_end()
        except:
            pass
    
    def is_available(self):
        """Check if TTS is available."""
        return self.tts is not None


def speak_coqui(text):
    """
    Quick test function for Coqui TTS.
    
    Args:
        text: Text to speak
    """
    tts = JarvisTTS(use_gpu=False)
    if tts.is_available():
        tts.speak(text, blocking=True)
    else:
        print("Coqui TTS not available")


def create_tts(use_gpu=False):
    """
    Create JARVIS TTS instance.
    
    Args:
        use_gpu: Use GPU acceleration
    
    Returns:
        JarvisTTS instance
    """
    return JarvisTTS(use_gpu=use_gpu)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🎙️  JARVIS Voice System Test")
    print("=" * 70)
    
    # Create TTS
    tts = create_tts(use_gpu=False)
    
    if not tts.is_available():
        print("\n❌ Coqui TTS not available")
        print("   Install: pip install TTS soundfile sounddevice numpy")
        exit(1)
    
    # Test messages
    messages = [
        "Systems online. Welcome back, sir.",
        "JARVIS interface initialized. All systems operational.",
        "How may I assist you today?",
        "Voice synthesis test complete. Standing by."
    ]
    
    for msg in messages:
        print(f"\n▶️  {msg}")
        tts.speak(msg, blocking=True)
    
    print("\n✅ Voice system test complete!")