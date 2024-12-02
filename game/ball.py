import pygame
import random
import math

class Ball:
    def __init__(self, settings):
        self.update_settings(settings)
        self.reset()

    def update_settings(self, settings):
        self.settings = settings
        self.size = int(min(settings.width, settings.height) * 0.02)
        self.base_speed = settings.ball_speed
        self.speed = self.base_speed
        self.rect = pygame.Rect(0, 0, self.size, self.size)

    def reset(self):
        self.x = self.settings.width / 2
        self.y = self.settings.height / 2
        self.rect.center = (int(self.x), int(self.y))
        self.dx = 0
        self.dy = 0
        self.speed = self.base_speed  # Reset speed when the ball is reset

    def move(self):
        self.x += self.dx * (self.speed / self.base_speed)
        self.y += self.dy * (self.speed / self.base_speed)
        self.rect.center = (int(self.x), int(self.y))

    def bounce(self):
        self.dx = -self.dx
        self.dy += random.uniform(-0.1, 0.1) * self.speed
        speed = math.sqrt(self.dx**2 + self.dy**2)
        self.dx = self.dx / speed * self.speed
        self.dy = self.dy / speed * self.speed

    def is_out(self):
        return self.x < 0 or self.x > self.settings.width
