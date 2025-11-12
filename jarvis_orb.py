"""
jarvis_orb.py
=============
JARVIS Holographic Orb - Iron Man Style

Features:
- Orange/amber holographic aesthetic
- Concentric expanding rings (hologram effect)
- Gold/white accent bars
- Stronger glow and darker background
- Talk/Act/Idle modes with smooth transitions
"""

import math
import random
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QRadialGradient, QPen, QPainterPath


class JarvisOrb(QWidget):
    """
    JARVIS-style holographic orb with orange/amber theme.
    
    Modes:
    - idle: Gentle breathing with expanding rings
    - talking: Active waveform with intense glow
    - acting: Subdued processing mode
    """
    
    mode_changed = pyqtSignal(str)
    
    def __init__(self, parent=None, size=300):
        super().__init__(parent)
        self.size = size
        self.setFixedSize(size, size)
        
        # Current mode
        self.mode = "idle"
        
        # Animation phases
        self.rotation = 0
        self.breathing_phase = 0
        self.wave_phase = 0
        self.ring_expansion_phase = 0
        
        # Holographic rings (expanding outward)
        self.holo_rings = []
        for i in range(5):
            self.holo_rings.append({
                'phase': i * 0.4,
                'speed': 0.015,
                'thickness': 2,
                'max_radius': 0.5
            })
        
        # Energy bars (gold/white accents)
        self.energy_bars = []
        for i in range(12):
            self.energy_bars.append({
                'angle': i * 30,
                'height': 0.5,
                'target_height': random.uniform(0.4, 1.0),
                'speed': random.uniform(0.12, 0.25)
            })
        
        # Rotating segments
        self.segments = [
            {'radius': 0.36, 'speed': 0.4, 'thickness': 1.5},
            {'radius': 0.43, 'speed': -0.3, 'thickness': 1.2},
            {'radius': 0.49, 'speed': 0.35, 'thickness': 1.0},
        ]
        
        # 60 FPS animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)
    
    def set_mode(self, mode):
        """Set orb mode: idle, talking, or acting."""
        if self.mode != mode:
            self.mode = mode
            self.mode_changed.emit(mode)
    
    def talk(self):
        """Enter talking mode."""
        self.set_mode("talking")
    
    def act(self):
        """Enter acting mode."""
        self.set_mode("acting")
    
    def idle(self):
        """Return to idle mode."""
        self.set_mode("idle")
    
    def update_animation(self):
        """Update animation based on current mode."""
        dt = 0.016
        
        base_speed = 0.5
        
        if self.mode == "idle":
            base_speed = 0.4
            self.breathing_phase += 0.025
            
        elif self.mode == "talking":
            base_speed = 2.2
            self.wave_phase += 0.18
            
            # Update energy bars (audio-like animation)
            for bar in self.energy_bars:
                bar['height'] += (bar['target_height'] - bar['height']) * bar['speed']
                if random.random() < 0.06:
                    bar['target_height'] = random.uniform(0.4, 1.0)
                    
        elif self.mode == "acting":
            base_speed = 0.25
        
        # Update rotation
        self.rotation += 0.6 * base_speed
        
        # Update holographic ring expansion
        self.ring_expansion_phase += 0.012 * base_speed
        for ring in self.holo_rings:
            ring['phase'] = (ring['phase'] + ring['speed'] * base_speed) % 2.0
        
        # Update segments
        for seg in self.segments:
            seg['rotation'] = seg.get('rotation', 0) + seg['speed'] * base_speed
        
        self.update()
    
    def paintEvent(self, event):
        """Paint the holographic orb."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        cx = self.width() / 2
        cy = self.height() / 2
        
        # Get JARVIS orange/amber colors
        core_color, accent_color = self.get_jarvis_colors()
        
        # Draw based on mode
        if self.mode == "idle":
            self.draw_idle_mode(painter, cx, cy, core_color, accent_color)
        elif self.mode == "talking":
            self.draw_talking_mode(painter, cx, cy, core_color, accent_color)
        elif self.mode == "acting":
            self.draw_acting_mode(painter, cx, cy, core_color, accent_color)
    
    def get_jarvis_colors(self):
        """Get JARVIS orange/amber color scheme."""
        if self.mode == "talking":
            return (255, 140, 0), (255, 200, 100)  # Deep orange + gold
        elif self.mode == "acting":
            return (255, 120, 30), (255, 180, 80)  # Orange + amber
        else:  # idle
            return (255, 126, 0), (255, 179, 71)  # Orange + light amber
    
    def draw_idle_mode(self, painter, cx, cy, core_color, accent_color):
        """Idle mode: gentle breathing with expanding rings."""
        base_radius = self.size * 0.26
        
        breath = 1.0 + 0.09 * math.sin(self.breathing_phase)
        orb_radius = base_radius * breath
        
        # Intense outer glow
        self.draw_holographic_glow(painter, cx, cy, orb_radius, core_color, intensity=1.0)
        
        # Expanding holographic rings
        self.draw_expanding_rings(painter, cx, cy, base_radius, core_color, alpha_mult=0.8)
        
        # Rotating segments
        self.draw_rotating_segments(painter, cx, cy, base_radius, accent_color, opacity=0.7)
        
        # Core
        self.draw_holographic_core(painter, cx, cy, orb_radius, core_color, brightness=1.0)
    
    def draw_talking_mode(self, painter, cx, cy, core_color, accent_color):
        """Talking mode: intense glow with energy bars."""
        base_radius = self.size * 0.26
        
        pulse = 1.0 + 0.18 * abs(math.sin(self.wave_phase))
        orb_radius = base_radius * pulse
        
        # Very intense glow
        self.draw_holographic_glow(painter, cx, cy, orb_radius, core_color, intensity=1.5)
        
        # Fast expanding rings
        self.draw_expanding_rings(painter, cx, cy, base_radius, core_color, alpha_mult=1.2)
        
        # Energy bars (gold/white)
        self.draw_energy_bars(painter, cx, cy, base_radius, accent_color)
        
        # Rotating segments
        self.draw_rotating_segments(painter, cx, cy, base_radius, accent_color, opacity=0.9)
        
        # Bright core
        self.draw_holographic_core(painter, cx, cy, orb_radius, core_color, brightness=1.4)
    
    def draw_acting_mode(self, painter, cx, cy, core_color, accent_color):
        """Acting mode: subdued processing."""
        base_radius = self.size * 0.26
        orb_radius = base_radius
        
        # Subtle glow
        self.draw_holographic_glow(painter, cx, cy, orb_radius, core_color, intensity=0.6)
        
        # Slow rings
        self.draw_expanding_rings(painter, cx, cy, base_radius, core_color, alpha_mult=0.5)
        
        # Slow segments
        self.draw_rotating_segments(painter, cx, cy, base_radius, accent_color, opacity=0.5)
        
        # Dimmed core
        self.draw_holographic_core(painter, cx, cy, orb_radius, core_color, brightness=0.7)
    
    def draw_holographic_glow(self, painter, cx, cy, radius, color, intensity=1.0):
        """Draw intense holographic glow."""
        painter.setPen(Qt.NoPen)
        
        glow_layers = [
            (0.7, int(60 * intensity)),
            (0.85, int(40 * intensity)),
            (1.0, int(25 * intensity)),
            (1.2, int(15 * intensity)),
        ]
        
        for scale, alpha in glow_layers:
            r = radius * scale
            gradient = QRadialGradient(cx, cy, r)
            gradient.setColorAt(0, QColor(*color, alpha))
            gradient.setColorAt(0.6, QColor(*color, alpha // 2))
            gradient.setColorAt(1, QColor(*color, 0))
            
            painter.setBrush(gradient)
            painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
    
    def draw_expanding_rings(self, painter, cx, cy, base_radius, color, alpha_mult=1.0):
        """Draw concentric expanding rings (hologram effect)."""
        painter.setPen(Qt.NoPen)
        
        for ring in self.holo_rings:
            # Ring expansion (0 to 1)
            expansion = ring['phase']
            
            if expansion < 1.0:  # Only draw if not fully expanded
                ring_radius = base_radius * (0.3 + expansion * ring['max_radius'])
                
                # Fade out as ring expands
                alpha = int(140 * alpha_mult * (1.0 - expansion))
                
                pen = QPen(QColor(*color, alpha))
                pen.setWidth(ring['thickness'])
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QRectF(cx - ring_radius, cy - ring_radius,
                                           ring_radius * 2, ring_radius * 2))
    
    def draw_energy_bars(self, painter, cx, cy, base_radius, color):
        """Draw energy bars (gold/white accents)."""
        painter.setPen(Qt.NoPen)
        
        for bar in self.energy_bars:
            angle_rad = math.radians(bar['angle'] + self.rotation)
            
            bar_length = base_radius * 0.18 * bar['height']
            bar_width = 5
            
            start_dist = base_radius * 0.58
            end_dist = start_dist + bar_length
            
            start_x = cx + start_dist * math.cos(angle_rad)
            start_y = cy + start_dist * math.sin(angle_rad)
            end_x = cx + end_dist * math.cos(angle_rad)
            end_y = cy + end_dist * math.sin(angle_rad)
            
            # Gold/white bar
            pen = QPen(QColor(255, 215, 100, 220))
            pen.setWidth(bar_width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))
            
            # Glow
            pen.setColor(QColor(*color, 90))
            pen.setWidth(bar_width * 2.5)
            painter.setPen(pen)
            painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))
    
    def draw_rotating_segments(self, painter, cx, cy, base_radius, color, opacity=1.0):
        """Draw rotating segmented rings."""
        painter.setBrush(Qt.NoBrush)
        
        for seg in self.segments:
            radius = base_radius * seg['radius']
            rotation = seg.get('rotation', 0)
            
            num_segments = 50
            segment_angle = 360 / num_segments
            
            for i in range(num_segments):
                angle = (i * segment_angle + rotation) % 360
                
                # Create gaps
                if i % 3 != 0:
                    start_rad = math.radians(angle)
                    end_rad = math.radians(angle + segment_angle * 0.65)
                    
                    x1 = cx + radius * math.cos(start_rad)
                    y1 = cy + radius * math.sin(start_rad)
                    x2 = cx + radius * math.cos(end_rad)
                    y2 = cy + radius * math.sin(end_rad)
                    
                    # Varying opacity
                    seg_opacity = opacity * (0.6 + 0.4 * math.sin(math.radians(angle)))
                    
                    pen = QPen(QColor(*color, int(seg_opacity * 200)))
                    pen.setWidth(seg['thickness'])
                    pen.setCapStyle(Qt.RoundCap)
                    painter.setPen(pen)
                    
                    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    
    def draw_holographic_core(self, painter, cx, cy, radius, color, brightness=1.0):
        """Draw holographic core with intense glow."""
        painter.setPen(Qt.NoPen)
        
        core_radius = radius * 0.2
        
        # Outer glow
        glow_gradient = QRadialGradient(cx, cy, core_radius * 2.8)
        glow_gradient.setColorAt(0, QColor(*color, int(150 * brightness)))
        glow_gradient.setColorAt(0.5, QColor(*color, int(80 * brightness)))
        glow_gradient.setColorAt(1, QColor(*color, 0))
        
        painter.setBrush(glow_gradient)
        painter.drawEllipse(QRectF(cx - core_radius * 2.8, cy - core_radius * 2.8,
                                   core_radius * 5.6, core_radius * 5.6))
        
        # Main core (orange to white gradient)
        core_gradient = QRadialGradient(cx, cy, core_radius)
        core_gradient.setColorAt(0, QColor(255, 255, 255, int(250 * brightness)))
        core_gradient.setColorAt(0.2, QColor(255, 220, 150, int(240 * brightness)))
        core_gradient.setColorAt(0.5, QColor(*color, int(220 * brightness)))
        core_gradient.setColorAt(0.8, QColor(color[0] - 40, color[1] - 40, 
                                             color[2] - 20, int(180 * brightness)))
        core_gradient.setColorAt(1, QColor(color[0] - 60, color[1] - 60, 
                                           color[2] - 40, int(140 * brightness)))
        
        painter.setBrush(core_gradient)
        painter.drawEllipse(QRectF(cx - core_radius, cy - core_radius,
                                   core_radius * 2, core_radius * 2))
        
        # Bright highlight
        highlight_radius = core_radius * 0.45
        highlight_gradient = QRadialGradient(cx - core_radius * 0.25, 
                                            cy - core_radius * 0.25, 
                                            highlight_radius)
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, int(240 * brightness)))
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(highlight_gradient)
        painter.drawEllipse(QRectF(cx - core_radius * 0.7, cy - core_radius * 0.7,
                                   highlight_radius * 2, highlight_radius * 2))


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QVBoxLayout
    import sys
    
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("JARVIS Holographic Orb")
    window.setStyleSheet("background-color: #0a0a0a;")
    window.resize(400, 400)
    
    layout = QVBoxLayout()
    orb = JarvisOrb(window, size=300)
    layout.addWidget(orb, alignment=Qt.AlignCenter)
    window.setLayout(layout)
    window.show()
    
    # Cycle through modes
    states = ["idle", "talking", "acting"]
    current = [0]
    
    def cycle():
        orb.set_mode(states[current[0]])
        print(f"Mode: {states[current[0]]}")
        current[0] = (current[0] + 1) % len(states)
    
    timer = QTimer()
    timer.timeout.connect(cycle)
    timer.start(3000)
    
    sys.exit(app.exec_())