"""
Animation utilities with easing functions
"""

import math


class AnimationManager:
    @staticmethod
    def lerp(start, end, t):
        """Linear interpolation"""
        return start + (end - start) * t
    
    @staticmethod
    def ease_out_quad(t):
        """Quadratic ease-out easing function"""
        return 1 - (1 - t) ** 2
    
    @staticmethod
    def ease_in_out_quad(t):
        """Quadratic ease-in-out easing function"""
        if t < 0.5:
            return 2 * t * t
        else:
            return -1 + (4 - 2 * t) * t
    
    @staticmethod
    def ease_out_cubic(t):
        """Cubic ease-out easing function"""
        return 1 - (1 - t) ** 3
    
    @staticmethod
    def sine_wave(t, amplitude=1.0):
        """Sine wave oscillation for idle pulsing"""
        return amplitude * math.sin(t)
    
    @staticmethod
    def smooth_step(t):
        """Smooth step function (Hermite interpolation)"""
        return t * t * (3 - 2 * t)
