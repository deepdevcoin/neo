# 🌌 Jarvis Neural Core

A desktop holographic neural orb with voice interaction, inspired by Tony Stark's Jarvis AI core. Features a 3D animated particle brain that reacts to voice input in real-time.

![Jarvis Neural Core](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey)

## ✨ Features

- 🎨 **3D Neural Network Visualization**: 400+ particles connected by glowing neural links
- 🎤 **Real-time Audio Reactivity**: Orb pulses and glows based on microphone input
- 🗣️ **Offline Speech Recognition**: Uses Vosk for privacy-focused voice recognition
- 🔊 **Text-to-Speech**: Jarvis-like voice responses
- 🪟 **Always-On-Top Overlay**: Transparent, frameless window that stays above all apps
- ⌨️ **Hotkey Control**: Toggle listening with Ctrl+Space
- 🌊 **Smooth Animations**: Rotating orb with ambient particle drift
- 🎭 **Reactive Glow Effects**: Intensity scales with voice amplitude

## 📋 Requirements

- Python 3.8 or higher
- Working microphone
- Audio output device
- OpenGL-capable graphics

## 🚀 Installation

### 1. Clone or Download

```bash
git clone <repository-url>
cd jarvis_neural_core
```

### 2. Install Python Dependencies

```bash
pip install PyQt5 PyOpenGL numpy sounddevice vosk pyttsx3
```

### 3. Download Vosk Speech Model

Download a Vosk model for offline speech recognition:

1. Visit https://alphacephei.com/vosk/models
2. Download `vosk-model-small-en-us-0.15` (or another English model)
3. Extract the downloaded archive
4. Rename the extracted folder to `model`
5. Place it in the project root directory:

```
jarvis_neural_core/
├── model/              # <- Vosk model folder here
│   ├── am/
│   ├── graph/
│   └── ...
├── main.py
├── orb_renderer.py
└── ...
```

### 4. Platform-Specific Setup

#### Linux
```bash
# Install PortAudio (required for sounddevice)
sudo apt-get install portaudio19-dev python3-pyaudio

# Install espeak (for pyttsx3)
sudo apt-get install espeak
```

#### macOS
```bash
# Install PortAudio via Homebrew
brew install portaudio
```

#### Windows
- No additional setup required
- Windows includes built-in TTS voices

## 🎮 Usage

### Starting Jarvis

```bash
python main.py
```

The neural orb will appear as a floating transparent window on your desktop.

### Controls

- **Ctrl+Space**: Toggle listening mode on/off
- **Drag window**: Click and drag to reposition (if window frame is visible)
- **Close**: Close the terminal window or press Ctrl+C

### Interaction

1. Press **Ctrl+Space** to activate listening
2. Speak your command
3. Jarvis will transcribe and respond
4. Press **Ctrl+Space** again to deactivate

### Example Commands

- "Hello Jarvis"
- "What time is it?"
- "Thank you"
- "Goodbye"

## 📁 Project Structure

```
jarvis_neural_core/
├── main.py                 # Main application entry point
├── orb_renderer.py        # 3D OpenGL particle system renderer
├── audio_listener.py      # Real-time microphone input processor
├── speech_engine.py       # Vosk + pyttsx3 integration
├── model/                 # Vosk speech model (download separately)
└── README.md              # This file
```

## 🎨 Customization

### Colors

Edit `orb_renderer.py` to change colors:

```python
# Inner glow (line ~141)
r, g, b = 1.0, 0.48, 0.09  # #FF7A18

# Outer filaments (line ~116)
glColor4f(1.0, 0.7, 0.28, alpha)  # #FFB347
```

### Particle Count

Adjust in `orb_renderer.py`:

```python
self.num_particles = 400  # Increase for denser orb
```

### Window Size

Modify in `main.py`:

```python
self.resize(400, 400)  # Width, height
```

### Response Logic

Enhance `get_jarvis_response()` in `main.py` to add custom responses or integrate with AI APIs.

## 🔧 Troubleshooting

### No Audio Input Detected

- Check microphone permissions
- Verify microphone is set as default input device
- Test with: `python -m sounddevice`

### Vosk Model Not Found

```
⚠️  Vosk model not found!
Please download a model from https://alphacephei.com/vosk/models
```

- Download and extract model as described in Installation step 3
- Ensure folder is named exactly `model` (not `vosk-model-small-en-us-0.15`)

### Window Not Transparent

- Some Linux desktop environments may not support transparent windows
- Try different compositor settings or window managers

### TTS Not Working

- **Linux**: Install `espeak` or `festival`
- **macOS**: Should work out of the box
- **Windows**: Check Windows Speech settings

### Performance Issues

- Reduce particle count in `orb_renderer.py`
- Lower FPS in `main.py` (increase timer interval)
- Close other GPU-intensive applications

## 🧠 Technical Details

### Audio Processing
- Uses `sounddevice` for low-latency microphone capture
- RMS amplitude calculation for intensity
- Smoothing filter for stable visual response

### 3D Rendering
- Pure PyOpenGL (no game engines)
- Particle system with dynamic connections
- Spherical distribution for natural look
- Smooth rotation and ambient drift

### Speech Recognition
- Vosk for fully offline recognition
- No cloud dependencies or API keys needed
- Privacy-focused design

## 🔮 Future Enhancements

- [ ] AI integration (ChatGPT, Claude API)
- [ ] Custom wake word detection
- [ ] Holographic ring layers
- [ ] Data stream animations along neural links
- [ ] Configuration file for easy customization
- [ ] Multiple color themes
- [ ] Gesture controls
- [ ] Multi-language support

## 📄 License

This project is provided as-is for educational and personal use.

## 🙏 Acknowledgments

- Vosk for offline speech recognition
- PyQt5 for cross-platform GUI
- OpenGL for 3D graphics
- Inspired by Marvel's Jarvis AI

## 💡 Tips

- Run on high-performance graphics mode for best visual quality
- Position orb in corner of screen to keep it visible while working
- Customize responses to match your workflow
- Consider integrating with home automation or productivity tools

---

**Made with ❤️ for the future of human-AI interaction**