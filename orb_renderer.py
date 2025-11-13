"""
Enhanced 3D Neural Orb Renderer with smooth animations and state management
"""

import numpy as np
from vispy import scene
import math


class OrbRenderer:
    def __init__(self, canvas, num_particles=150):
        self.canvas = canvas
        self.num_particles = num_particles
        self.reactivity = 0.0
        self.rotation_angle = 0.0
        self.scale = 1.0
        self.action_mode = False
        self.pulse_strength = 0.0
        self.base_color = np.array([1.0, 0.48, 0.11])  # Orange/gold #FF7A18
        
        # Create view
        self.view = canvas.central_widget.add_view()
        self.view.camera = 'turntable'
        self.view.camera.fov = 45
        
        self.particles = self._create_particles()
        
        # Create scatter plot
        self.scatter = scene.visuals.Markers()
        self.scatter.set_data(
            self.particles['positions'],
            size=5,
            edge_color=(1, 0.48, 0.11, 0.8),
            face_color=(1, 0.48, 0.11, 0.6)
        )
        self.view.add(self.scatter)
        
        # Create neural network lines
        self.line_visual = scene.visuals.Line(
            pos=np.zeros((0, 3)),
            color=(1, 0.7, 0.3, 0.4),
            width=1.0
        )
        self.view.add(self.line_visual)
        
        self.halo_visual = scene.visuals.Markers()
        self.update_connections()
    
    def _create_particles(self, radius=1.2):
        """Create particle positions using Fibonacci sphere algorithm"""
        positions = []
        golden_angle = np.pi * (3.0 - np.sqrt(5.0))
        
        for i in range(self.num_particles):
            y = 1 - (i / float(self.num_particles - 1)) * 2
            radius_at_y = np.sqrt(1 - y * y)
            theta = golden_angle * i
            
            x = np.cos(theta) * radius_at_y
            z = np.sin(theta) * radius_at_y
            
            positions.append([x, y, z])
        
        return {'positions': np.array(positions) * radius}
    
    def update_connections(self):
        """Update neural network connections"""
        connection_distance = 0.9
        lines = []
        
        for i, pos1 in enumerate(self.particles['positions']):
            for j, pos2 in enumerate(self.particles['positions']):
                if i < j:
                    dist = np.linalg.norm(pos1 - pos2)
                    if dist < connection_distance:
                        lines.append(pos1)
                        lines.append(pos2)
        
        if lines:
            self.line_visual.set_data(np.array(lines))
    
    def set_reactivity(self, value):
        """Set audio reactivity (0-1) with smooth easing"""
        self.reactivity = max(0.0, min(1.0, value))
    
    def set_scale(self, scale):
        """Set orb scale for animation"""
        self.scale = max(0.3, min(2.0, scale))
    
    def set_action_mode(self, active):
        """Enter/exit action mode with color changes"""
        self.action_mode = active
    
    def trigger_pulse(self):
        """Trigger energy pulse when speaking"""
        self.pulse_strength = 1.0
    
    def update(self):
        """Update animation frame with smooth transitions"""
        # Rotate orb
        self.rotation_angle += 0.8
        angle_rad = np.radians(self.rotation_angle)
        
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        
        rotated = []
        for pos in self.particles['positions']:
            x, y, z = pos
            # Rotate around Y axis
            new_x = x * cos_a - z * sin_a
            new_z = x * sin_a + z * cos_a
            rotated.append([new_x, y, new_z])
        
        rotated = np.array(rotated)
        
        # Apply scale
        rotated = rotated * self.scale
        
        # Apply reactivity and pulse
        color_boost = self.reactivity + self.pulse_strength * 0.3
        expansion = 1.0 + self.reactivity * 0.25 + self.pulse_strength * 0.15
        
        if self.action_mode:
            face_color = (0.2, 0.8, 1.0, 0.6 + color_boost * 0.2)
            edge_color = (0.4, 1.0, 1.0, 0.8)
        else:
            # Normal mode: orange/gold
            face_color = (1.0, 0.48 + color_boost * 0.3, 0.11, 0.6 + color_boost * 0.2)
            edge_color = (1.0, 0.7 + color_boost * 0.2, 0.3, 0.8)
        
        # Update scatter plot
        self.scatter.set_data(
            rotated * expansion,
            size=5 + self.reactivity * 3 + self.pulse_strength * 2,
            edge_color=edge_color,
            face_color=face_color
        )
        
        self.reactivity *= 0.92
        self.pulse_strength *= 0.94
