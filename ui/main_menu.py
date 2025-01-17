import pygame
import pygame_gui
import math
import random
import os

class DemoGame:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.paddle1_y = height // 2
        self.paddle2_y = height // 2
        self.paddle_height = height // 6
        self.paddle_width = width // 40
        self.ball_x = width // 2
        self.ball_y = height // 2
        self.ball_dx = width // 100
        self.ball_dy = height // 150
        self.ball_size = width // 60
        
        # Add perfect prediction for paddles
        self.target_y1 = self.paddle1_y
        self.target_y2 = self.paddle2_y

    def predict_ball_y(self, paddle_x):
        # Calculate time until ball reaches paddle
        time_to_paddle = (paddle_x - self.ball_x) / self.ball_dx
        # Predict y position
        future_y = self.ball_y + self.ball_dy * time_to_paddle
        
        # Account for bounces
        while future_y < 0 or future_y > self.height:
            if future_y < 0:
                future_y = -future_y
            if future_y > self.height:
                future_y = 2 * self.height - future_y
        
        return future_y

    def update(self):
        # Move ball
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        # Perfect AI prediction
        if self.ball_dx < 0:  # Ball moving left
            self.target_y1 = self.predict_ball_y(self.paddle_width * 2)
        else:  # Ball moving right
            self.target_y2 = self.predict_ball_y(self.width - self.paddle_width * 2)

        # Smooth paddle movement
        self.paddle1_y += (self.target_y1 - self.paddle_height/2 - self.paddle1_y) * 0.2
        self.paddle2_y += (self.target_y2 - self.paddle_height/2 - self.paddle2_y) * 0.2

        # Ball collisions
        if self.ball_y <= 0 or self.ball_y >= self.height:
            self.ball_dy = -self.ball_dy

        # Paddle collisions with slight angle variation
        if (self.ball_x <= self.paddle_width * 2 and 
            self.paddle1_y <= self.ball_y <= self.paddle1_y + self.paddle_height):
            self.ball_dx = abs(self.ball_dx)
            # Add slight random angle variation for visual interest
            self.ball_dy += (random.random() - 0.5) * self.height * 0.01
        elif (self.ball_x >= self.width - self.paddle_width * 2 and 
              self.paddle2_y <= self.ball_y <= self.paddle2_y + self.paddle_height):
            self.ball_dx = -abs(self.ball_dx)
            # Add slight random angle variation for visual interest
            self.ball_dy += (random.random() - 0.5) * self.height * 0.01

        # Reset ball if it somehow goes out (shouldn't happen with perfect AI)
        if self.ball_x < 0 or self.ball_x > self.width:
            self.ball_x = self.width // 2
            self.ball_y = self.height // 2

    def draw(self, screen, alpha=64):
        # Create a transparent surface
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw center line
        center_line_width = 4
        dash_length = 20
        gap_length = 15
        for y in range(0, self.height, dash_length + gap_length):
            pygame.draw.rect(surface, (128, 128, 128, alpha),
                           (self.width // 2 - center_line_width // 2, y,
                            center_line_width, dash_length))

        # Draw paddles with a glowing effect
        glow_size = 10
        glow_alpha = alpha // 2
        
        # Left paddle glow
        pygame.draw.rect(surface, (255, 255, 255, glow_alpha),
                        (self.paddle_width - glow_size, self.paddle1_y - glow_size,
                         self.paddle_width + 2*glow_size, self.paddle_height + 2*glow_size))
        
        # Right paddle glow
        pygame.draw.rect(surface, (255, 255, 255, glow_alpha),
                        (self.width - self.paddle_width * 2 - glow_size, self.paddle2_y - glow_size,
                         self.paddle_width + 2*glow_size, self.paddle_height + 2*glow_size))
        
        # Draw actual paddles
        pygame.draw.rect(surface, (255, 255, 255, alpha), 
                        (self.paddle_width, self.paddle1_y,
                         self.paddle_width, self.paddle_height))
        pygame.draw.rect(surface, (255, 255, 255, alpha), 
                        (self.width - self.paddle_width * 2, self.paddle2_y,
                         self.paddle_width, self.paddle_height))
        
        # Draw ball with a glowing effect
        pygame.draw.circle(surface, (255, 255, 255, glow_alpha),
                         (int(self.ball_x), int(self.ball_y)),
                         self.ball_size + glow_size)
        pygame.draw.circle(surface, (255, 255, 255, alpha),
                         (int(self.ball_x), int(self.ball_y)),
                         self.ball_size)
        
        # Draw to screen with a subtle background
        pygame.draw.rect(screen, (20, 20, 30), (0, 0, self.width, self.height))
        screen.blit(surface, (0, 0))

class MainMenu:
    def __init__(self, screen, settings):
        self.screen = screen
        self.settings = settings
        
        # Load theme
        theme_path = os.path.join('data', 'themes', 'menu_theme.json')
        self.manager = pygame_gui.UIManager(screen.get_size(), theme_path)
        
        # Initialize demo game with settings
        self.demo_game = DemoGame(screen.get_width(), screen.get_height())
        self.settings.apply_settings_to_demo(self.demo_game)
        
        self.create_ui_elements()

    def process_event(self, event):
        self.manager.process_events(event)

    def create_ui_elements(self):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Create title label with adjusted height
        title_height = int(screen_height * 0.12)  # Reduced from 0.15
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (0, int(screen_height * 0.15)),  # Moved down slightly from 0.1
                (screen_width, title_height)
            ),
            text="PONG AI",
            manager=self.manager,
            object_id="#title_label",
        )

        # Create subtitle label with reduced spacing
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (0, int(screen_height * 0.15) + title_height - int(screen_height * 0.02)),  # Reduced gap
                (screen_width, int(title_height * 0.4))  # Reduced from 0.5
            ),
            text="SIMULATION",
            manager=self.manager,
            object_id="#subtitle_label"
        )
        
        # Adjust button positioning to account for new title spacing
        button_width = min(int(screen_width * 0.25), 400)
        button_height = int(screen_height * 0.08)
        spacing = int(screen_height * 0.02)
        
        # Move buttons up slightly to account for new title position
        start_y = int(screen_height * 0.45)  # Changed from 0.5

        buttons = [
            ("New Game", "new_game"),
            ("Load Game", "load_game"),
            ("Settings", "settings"),
        ]

        self.buttons = {}
        for i, (text, key) in enumerate(buttons):
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (screen_width // 2 - button_width // 2,
                     start_y + i * (button_height + spacing)),
                    (button_width, button_height)
                ),
                text=text,
                manager=self.manager
            )
            self.buttons[key] = button

    def update(self, time_delta):
        # Update states
        self.manager.update(time_delta)
        self.demo_game.update()
        
        # Draw in correct order:
        # 1. Clear screen with dark background
        self.screen.fill((20, 20, 30))
        
        # 2. Draw demo game with increased visibility
        self.demo_game.draw(self.screen, alpha=180)
        
        # 3. Draw UI elements on top
        self.manager.draw_ui(self.screen)

        return self.check_buttons()

    def check_buttons(self):
        for key, button in self.buttons.items():
            if button.check_pressed():
                return key
        return None
