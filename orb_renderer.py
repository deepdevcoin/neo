"""
Neural Orb Renderer - Handles 3D particle system and OpenGL rendering
"""

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective
import math


class NeuralOrbRenderer:
    def __init__(self, parent):
        self.parent = parent
        self.rotation_angle = 0.0
        self.particles = []
        self.connections = []
        self.num_particles = 400
        self.max_connection_distance = 0.3
        
    def initialize(self):
        """Initialize OpenGL settings and generate particle system"""
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_POINT_SMOOTH)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        
        self.generate_particles()
        
    def generate_particles(self):
        """Generate particles in a spherical distribution"""
        self.particles = []
        for i in range(self.num_particles):
            # Spherical coordinates for even distribution
            phi = np.random.uniform(0, 2 * np.pi)
            theta = np.arccos(np.random.uniform(-1, 1))
            r = np.random.uniform(0.3, 0.8)
            
            x = r * np.sin(theta) * np.cos(phi)
            y = r * np.sin(theta) * np.sin(phi)
            z = r * np.cos(theta)
            
            # Add slight random drift velocity
            vx = np.random.uniform(-0.001, 0.001)
            vy = np.random.uniform(-0.001, 0.001)
            vz = np.random.uniform(-0.001, 0.001)
            
            self.particles.append({
                'pos': np.array([x, y, z]),
                'vel': np.array([vx, vy, vz]),
                'phase': np.random.uniform(0, 2 * np.pi)
            })
            
        self.update_connections()
        
    def update_connections(self):
        """Calculate which particles should be connected"""
        self.connections = []
        for i in range(len(self.particles)):
            for j in range(i + 1, len(self.particles)):
                dist = np.linalg.norm(
                    self.particles[i]['pos'] - self.particles[j]['pos']
                )
                if dist < self.max_connection_distance:
                    self.connections.append((i, j, dist))
                    
    def resize(self, w, h):
        """Handle window resize"""
        if h == 0:
            h = 1
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, w / h, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        
    def render(self, amplitude, listening_active):
        """Main render function"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Camera position
        glTranslatef(0.0, 0.0, -3.0)
        
        # Rotation animation
        self.rotation_angle += 0.2
        glRotatef(self.rotation_angle * 0.3, 0, 1, 0)
        glRotatef(self.rotation_angle * 0.2, 1, 0, 0)
        
        # Update particles with ambient drift
        for particle in self.particles:
            particle['pos'] += particle['vel']
            
            # Keep particles bounded in sphere
            dist = np.linalg.norm(particle['pos'])
            if dist > 1.0:
                particle['pos'] *= 0.98
                
        # Periodically update connections
        if int(self.rotation_angle) % 20 == 0:
            self.update_connections()
            
        # Calculate glow intensity
        base_intensity = 0.6
        pulse_intensity = base_intensity + amplitude * 0.8
        if listening_active:
            pulse_intensity = max(pulse_intensity, 0.8)
            
        # Render connections (neural links)
        self.render_connections(pulse_intensity)
        
        # Render particles (nodes)
        self.render_particles(pulse_intensity, amplitude)
        
        # Render glow aura
        self.render_aura(pulse_intensity, amplitude)
        
    def render_connections(self, intensity):
        """Render lines between connected particles"""
        glBegin(GL_LINES)
        for i, j, dist in self.connections:
            alpha = (1.0 - dist / self.max_connection_distance) * intensity
            
            # Orange filament color #FFB347
            glColor4f(1.0, 0.7, 0.28, alpha * 0.4)
            
            pos1 = self.particles[i]['pos']
            pos2 = self.particles[j]['pos']
            
            glVertex3f(pos1[0], pos1[1], pos1[2])
            glVertex3f(pos2[0], pos2[1], pos2[2])
        glEnd()
        
    def render_particles(self, intensity, amplitude):
        """Render particle nodes"""
        glPointSize(3.0 + amplitude * 2.0)
        glBegin(GL_POINTS)
        
        for i, particle in enumerate(self.particles):
            pos = particle['pos']
            phase = particle['phase'] + self.rotation_angle * 0.05
            
            # Pulsing effect
            pulse = 0.5 + 0.5 * math.sin(phase)
            
            # Inner glow color #FF7A18
            r = 1.0
            g = 0.48 + pulse * 0.2
            b = 0.09
            alpha = intensity * (0.6 + pulse * 0.4)
            
            # Brighter core particles
            dist_from_center = np.linalg.norm(pos)
            if dist_from_center < 0.5:
                alpha *= 1.3
                
            glColor4f(r, g, b, alpha)
            glVertex3f(pos[0], pos[1], pos[2])
            
        glEnd()
        
    def render_aura(self, intensity, amplitude):
        """Render outer glow aura"""
        glDisable(GL_DEPTH_TEST)
        
        num_layers = 3
        for layer in range(num_layers):
            radius = 1.0 + layer * 0.2 + amplitude * 0.3
            alpha = intensity * 0.1 * (1.0 - layer / num_layers)
            
            glColor4f(1.0, 0.48, 0.09, alpha)
            self.draw_sphere_outline(radius, 16, 16)
            
        glEnable(GL_DEPTH_TEST)
        
    def draw_sphere_outline(self, radius, slices, stacks):
        """Draw a wireframe sphere for aura effect"""
        for i in range(stacks):
            lat0 = np.pi * (-0.5 + float(i) / stacks)
            lat1 = np.pi * (-0.5 + float(i + 1) / stacks)
            
            glBegin(GL_LINE_STRIP)
            for j in range(slices + 1):
                lng = 2 * np.pi * float(j) / slices
                x = radius * np.cos(lat1) * np.cos(lng)
                y = radius * np.sin(lat1)
                z = radius * np.cos(lat1) * np.sin(lng)
                glVertex3f(x, y, z)
            glEnd()