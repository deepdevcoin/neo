# Neo Neural Core - Enhanced Desktop Application

A sophisticated, always-on-top desktop overlay featuring a smooth-animated 3D neural orb with real-time speech recognition, TTS responses, and intelligent action execution. Fully transparent holographic interface inspired by Tony Stark's Neo.

## Features

- **Transparent Holographic Orb** - Fully transparent 3D neural network with GPU-optimized rendering
- **Smooth Animations** - All transitions use mathematical easing (lerp, quad, cubic) for natural motion
- **Real-Time Audio Reactivity** - Orb expands and brightens based on microphone input
- **Offline Speech Recognition** - Vosk-powered privacy-focused voice commands
- **Text-to-Speech Responses** - pyttsx3 integration with Neo-like voice
- **Typing Animation Overlay** - Green monospace (#00FF7F) text with cinematic typewriter effect (5s fade)
- **Action Mode** - Orb moves right, shrinks, executes commands, returns to center
- **Hotkey Activation** - Global Ctrl+Space for hands-free control
- **Optimized Performance** - 150 particles, 60 FPS, minimal CPU usage
- **Cross-Platform** - Linux, Windows, macOS support

## Installation

### Prerequisites

- Python 3.8+
- pip package manager
- Microphone (for voice input)

### Step 1: Install System Dependencies

**Ubuntu/Debian:**
\`\`\`bash
sudo apt-get install python3-dev python3-pip portaudio19-dev gnome-terminal
\`\`\`

**macOS:**
\`\`\`bash
brew install python portaudio
\`\`\`

**Windows:**
Install Python 3.10+ from https://www.python.org/

### Step 2: Install Python Dependencies

\`\`\`bash
pip install PyQt5 numpy sounddevice vosk pyttsx3 vispy pynput
\`\`\`

### Step 3: Download Vosk Speech Model

\`\`\`bash
# Create models directory
mkdir -p ~/.vosk-models

# Download model
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.42-gigaspeech.zip
unzip vosk-model-en-us-0.42-gigaspeech.zip -d ~/.vosk-models/
mv ~/.vosk-models/vosk-model-en-us-0.42-gigaspeech ~/.vosk-models/model
\`\`\`

## Usage

### Launch the Application

\`\`\`bash
python main.py
\`\`\`

### Controls

- **Ctrl+Space** - Toggle listening mode on/off
- **Speak Naturally** - Neo listens and responds
- **Action Commands** - Say "open browser", "open terminal", "show time"
- Close window normally to exit gracefully

### Operation

1. Press **Ctrl+Space** to activate listening mode
2. Speak clearly into your microphone
3. Neo recognizes speech and displays typing animation
4. The orb reacts with color and size changes
5. For commands (e.g., "open terminal"), orb moves right and executes action
6. Orb returns to center after action completion

## Configuration

### Adjust Orb Colors

Edit `orb_renderer.py` to modify the base color (RGB 0-1 range):

\`\`\`python
self.base_color = np.array([1.0, 0.48, 0.11])  # Orange/gold #FF7A18
\`\`\`

Action mode uses cyan tint. Modify the action_mode color section for different theme.

### Customize Text Overlay

Edit `text_overlay.py`:

\`\`\`python
font = QFont("Courier New", 11, QFont.Bold)  # Change font family/size
self.label.setStyleSheet("color: #00FF7F;")  # Change hacking green hex
self.timer.start(40)  # Adjust typing speed (lower = faster)
self.fade_timer.start(5000)  # Change display duration (milliseconds)
\`\`\`

### Adjust Performance

Edit `main.py`:

\`\`\`python
self.orb_renderer = OrbRenderer(self.canvas, num_particles=150)  # Adjust particle count
self.timer.start(16)  # 60 FPS (increase value for lower FPS, less CPU)
\`\`\`

### Add Custom Action Commands

Edit the `execute_action()` method in `main.py` to add command handlers:

\`\`\`python
elif 'notes' in command.lower():
    subprocess.Popen(['gedit'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
\`\`\`

## Project Structure

\`\`\`
Neo-neural-core/
├── main.py                  # Entry point, window management, state logic
├── orb_renderer.py          # 3D particle network rendering with easing
├── audio_listener.py        # Real-time microphone amplitude detection
├── speech_engine.py         # Vosk speech recognition + pyttsx3 TTS
├── text_overlay.py          # Typing animation overlay with fade effect
├── animation_manager.py     # Easing functions and smooth interpolation
├── hotkey_manager.py        # Global Ctrl+Space hotkey detection
└── README.md                # This file
\`\`\`

## Troubleshooting

**"No module named 'vosk'"**
Ensure vosk model is downloaded to `~/.vosk-models/model/`

**Audio not detected**
Check system audio input levels and microphone permissions. Test with: `python -c "import sounddevice; print(sounddevice.default_device())"`

**Vosk not recognizing speech**
Try a larger model or check microphone quality. Speak clearly and closer to microphone.

**Window not staying on top**
Some Wayland-based window managers have limitations. Try with X11 session.

**High CPU usage**
Reduce `num_particles` to 100-120 or increase timer interval to 32ms (30 FPS).

**Text overlay not appearing**
Ensure text_overlay.py is in the same directory as main.py.

## Performance Tips

- **Linux**: Ensure OpenGL drivers are installed for smooth rendering
- **Windows**: Update GPU drivers for optimal performance
- **macOS**: Works best on Apple Silicon or newer Intel Macs
- Reduce particles and FPS for lower-end systems

## System Requirements

- Python 3.8+
- 4GB RAM minimum
- OpenGL-capable GPU (recommended)
- Modern desktop environment (GNOME, KDE, macOS, Windows 10+)

## Future Enhancements

- [ ] Holographic ring layers around the orb
- [ ] Customizable voice profiles
- [ ] Voice command macros
- [ ] Tray icon for quick access
- [ ] Settings GUI for configuration
- [ ] Cloud sync for commands/responses
- [ ] Multi-language support

## License

MIT License - Feel free to modify and distribute

## Credits

Built with:
- **PyQt5** - GUI framework
- **VisPy** - 3D visualization
- **Vosk** - Offline speech recognition
- **pyttsx3** - Text-to-speech
- **pynput** - Global hotkey detection
- **NumPy** - Numerical calculations
- **sounddevice** - Audio capture

---

**Enjoy your personal Neo AI! Press Ctrl+Space to get started.**
