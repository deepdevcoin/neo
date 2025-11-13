import numpy as np
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient
import math

class OrbRenderer(QWidget):
    """3D-style orb with particle network and audio reactivity"""
    action_requested = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.particles = self.generate_particles(150)
        self.audio_level = 0.0
        self.target_audio = 0.0
        self.state = "idle"  # idle, listening, speaking, executing
        self.rotation = 0.0
        self.scale = 1.0
        self.target_scale = 1.0
        self.position_x = 0.5  # 0 = left, 1 = right
        self.target_position_x = 0.5
        self.glow_intensity = 0.3
        self.color_cycle = 0.0
        
        self.init_ui()
        self.setup_animation()
    
    def init_ui(self):
        """Setup window properties"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Set size
        self.orb_size = 300
        self.setGeometry(0, 0, self.orb_size, self.orb_size)
        self.center_on_screen()
    
    def center_on_screen(self):
        """Center window on screen"""
        screen = self.screen()
        x = (screen.geometry().width() - self.orb_size) // 2
        y = (screen.geometry().height() - self.orb_size) // 2
        self.move(x, y)
    
    def generate_particles(self, count=150):
        """Generate particles in fibonacci sphere distribution"""
        particles = []
        phi = np.pi * (3.0 - np.sqrt(5.0))  # Fibonacci angle
        
        for i in range(count):
            y = 1 - (i / float(count - 1)) * 2
            radius = np.sqrt(1 - y * y)
            theta = phi * i
            
            x = np.cos(theta) * radius
            z = np.sin(theta) * radius
            
            particles.append({
                'x': x, 'y': y, 'z': z,
                'vx': 0, 'vy': 0, 'vz': 0,
                'size': np.random.rand() * 3 + 1
            })
        
        return particles
    
    def update_animation(self):
        """Update orb state every frame"""
        # Audio level smoothing (lerp)
        self.audio_level += (self.target_audio - self.audio_level) * 0.15
        
        # Scale based on audio
        self.target_scale = 1.0 + self.audio_level * 0.3
        self.scale += (self.target_scale - self.scale) * 0.1
        
        # Position animation for action mode
        self.position_x += (self.target_position_x - self.position_x) * 0.15
        
        # Rotation
        self.rotation += 0.5
        self.color_cycle = (self.color_cycle + 1) % 360
        
        # Update particle positions
        for particle in self.particles:
            # Rotation around Y axis
            angle = np.radians(self.rotation)
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            
            x, z = particle['x'], particle['z']
            particle['x'] = x * cos_a - z * sin_a
            particle['z'] = x * sin_a + z * cos_a
        
        self.update()
    
    def paintEvent(self, event):
        """Render orb with particles and glow"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        center_x = self.orb_size / 2
        center_y = self.orb_size / 2
        base_radius = (self.orb_size / 2 - 20) * self.scale
        
        # Draw glow (outer aura)
        glow_intensity = self.glow_intensity + self.audio_level * 0.7
        for i in range(10, 0, -1):
            glow_radius = base_radius + i * 5
            glow_alpha = int(30 * (1 - i / 10.0) * glow_intensity)
            
            glow_color = QColor(255, 122, 24, glow_alpha)  # Orange
            painter.setBrush(QBrush(glow_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(center_x - glow_radius), int(center_y - glow_radius),
                              int(glow_radius * 2), int(glow_radius * 2))
        
        # Draw core orb with gradient
        gradient = QRadialGradient(center_x, center_y, 0, center_x, center_y, base_radius)
        
        if self.state == "idle":
            gradient.setColorAt(0, QColor(255, 215, 128))  # Gold center
            gradient.setColorAt(1, QColor(255, 122, 24))   # Orange edge
        elif self.state == "listening":
            gradient.setColorAt(0, QColor(0, 255, 127))    # Green center
            gradient.setColorAt(1, QColor(255, 122, 24))   # Orange edge
        elif self.state == "executing":
            gradient.setColorAt(0, QColor(0, 200, 255))    # Cyan center
            gradient.setColorAt(1, QColor(255, 122, 24))   # Orange edge
        else:  # speaking
            gradient.setColorAt(0, QColor(255, 255, 150))  # Yellow center
            gradient.setColorAt(1, QColor(255, 122, 24))   # Orange edge
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(center_x - base_radius), int(center_y - base_radius),
                          int(base_radius * 2), int(base_radius * 2))
        
        # Draw particle network
        self.draw_particles(painter, center_x, center_y, base_radius)
        
        # Draw outer ring pulse
        if self.audio_level > 0.1:
            ring_width = 2 + self.audio_level * 3
            ring_color = QColor(0, 255, 127, int(150 * self.audio_level))
            painter.setPen(QPen(ring_color, ring_width))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(int(center_x - base_radius - 5),
                              int(center_y - base_radius - 5),
                              int(base_radius * 2 + 10),
                              int(base_radius * 2 + 10))
    
    def draw_particles(self, painter, center_x, center_y, radius):
        """Draw particles and connections"""
        projected = []
        
        # Project 3D particles to 2D
        for particle in self.particles:
            perspective = 1.0 / (2.0 + particle['z'])
            proj_x = center_x + particle['x'] * radius * perspective
            proj_y = center_y + particle['y'] * radius * perspective
            depth = particle['z']
            
            projected.append({
                'x': proj_x, 'y': proj_y, 'z': depth,
                'size': particle['size']
            })
        
        # Draw connections between nearby particles
        connection_pen = QPen(QColor(255, 122, 24, 60), 1)
        painter.setPen(connection_pen)
        
        for i, p1 in enumerate(projected):
            for p2 in projected[i+1:]:
                dist_sq = (p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2
                if dist_sq < 100**2:  # Connection threshold
                    painter.drawLine(int(p1['x']), int(p1['y']),
                                   int(p2['x']), int(p2['y']))
        
        # Draw particles
        for particle in projected:
            size = particle['size'] * (1 + particle['z'] * 0.5)
            alpha = int(150 + particle['z'] * 100)
            
            color = QColor(255, 200, 100, alpha)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(particle['x'] - size/2),
                              int(particle['y'] - size/2),
                              int(size), int(size))
    
    def set_audio_level(self, level):
        """Set audio level (0.0 - 1.0)"""
        self.target_audio = min(1.0, max(0.0, level))
    
    def set_state(self, state):
        """Change orb state"""
        self.state = state
        if state == "executing":
            self.target_position_x = 0.7  # Move right
            self.target_scale = 0.6
        else:
            self.target_position_x = 0.5  # Center
            self.target_scale = 1.0
    
    def setup_animation(self):
        """Setup animation timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS
