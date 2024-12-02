import pygame

class Paddle:
    def __init__(self, settings, side):
        self.settings = settings
        self.side = side
        self.width = int(settings.width * 0.02)
        self.height = int(settings.height * 0.2)
        self.speed = settings.paddle_speed
        self.y = (settings.height - self.height) / 2
        if side == "left":
            self.x = self.width
        else:
            self.x = settings.width - self.width * 2
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def move(self, action):
        if action == 1:  # Move up
            self.y = max(0, self.y - self.speed)
        elif action == 2:  # Move down
            self.y = min(self.settings.height - self.height, self.y + self.speed)
        self.rect.y = self.y

    def update_settings(self, settings):
        self.settings = settings
        self.width = int(settings.width * 0.02)
        self.height = int(settings.height * 0.2)
        self.speed = settings.paddle_speed
        if self.side == "left":
            self.x = self.width
        else:
            self.x = settings.width - self.width * 2
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def collides_with(self, ball):
        return self.rect.colliderect(ball.rect)

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), self.rect)
