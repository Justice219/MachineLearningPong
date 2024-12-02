import pygame
import os
import pygame_gui
import json
from ui.main_menu import DemoGame

class Settings:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Load settings from file or use defaults
        self.load_settings()
        
    def load_settings(self):
        settings_path = os.path.join('data', 'settings.json')
        defaults = {
            # Game settings
            'ball_speed': 5,
            'paddle_speed': 5,
            # Demo settings
            'demo_ball_speed': 5,
            'demo_paddle_speed': 5,
            'demo_glow_intensity': 180,
            'demo_trail_length': 5,
            # Visual settings
            'glow_intensity': 180,
            'show_trails': True,
            'trail_length': 5,
            # UI settings
            'ui_scale': 1.0,
        }
        
        try:
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    saved_settings = json.load(f)
                # Update defaults with saved settings
                defaults.update(saved_settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
            
        # Set all attributes
        for key, value in defaults.items():
            setattr(self, key, value)

    def save_settings(self):
        settings_path = os.path.join('data', 'settings.json')
        settings_dict = {
            # Game settings
            'ball_speed': self.ball_speed,
            'paddle_speed': self.paddle_speed,
            # Demo settings
            'demo_ball_speed': self.demo_ball_speed,
            'demo_paddle_speed': self.demo_paddle_speed,
            'demo_glow_intensity': self.demo_glow_intensity,
            'demo_trail_length': self.demo_trail_length,
            # Visual settings
            'glow_intensity': self.glow_intensity,
            'show_trails': self.show_trails,
            'trail_length': self.trail_length,
            # UI settings
            'ui_scale': self.ui_scale,
        }
        
        try:
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            with open(settings_path, 'w') as f:
                json.dump(settings_dict, f, indent=4)
            print("Settings saved successfully")
        except Exception as e:
            print(f"Error saving settings: {e}")

    def apply_settings_to_game(self, game_instance):
        """Apply current settings to a game instance"""
        if game_instance:
            game_instance.ball_speed = self.ball_speed
            game_instance.paddle_speed = self.paddle_speed
            game_instance.glow_intensity = self.glow_intensity
            game_instance.show_trails = self.show_trails
            game_instance.trail_length = self.trail_length
            
    def apply_settings_to_demo(self, demo_game):
        """Apply current settings to a demo game"""
        if demo_game:
            demo_game.ball_dx = demo_game.width // 100 * self.demo_ball_speed / 5
            demo_game.ball_dy = demo_game.height // 150 * self.demo_ball_speed / 5
            # Add other demo settings as needed

    def show_settings_menu(self, screen, font):
        # Create UI manager with same theme as main menu
        theme_path = os.path.join('data', 'themes', 'menu_theme.json')
        manager = pygame_gui.UIManager(screen.get_size(), theme_path)
        
        # Create demo game for background
        demo_game = DemoGame(screen.get_width(), screen.get_height())
        
        # Settings categories
        settings = {
            "Game Settings": [
                ("Ball Speed", "ball_speed", 1, 20),
                ("Paddle Speed", "paddle_speed", 1, 20),
            ],
            "Visual Settings": [
                ("Glow Intensity", "glow_intensity", 0, 255),
                ("Show Trails", "show_trails", False, True),
                ("Trail Length", "trail_length", 1, 20),
            ],
            "Demo Settings": [
                ("Demo Ball Speed", "demo_ball_speed", 1, 20),
                ("Demo Paddle Speed", "demo_paddle_speed", 1, 20),
                ("Demo Glow Intensity", "demo_glow_intensity", 0, 255),
            ],
            "UI Settings": [
                ("UI Scale", "ui_scale", 0.5, 2.0, 0.1),  # Step size of 0.1
            ]
        }

        # Create UI elements
        panel_width = int(screen.get_width() * 0.6)
        panel_height = int(screen.get_height() * 0.8)
        panel_rect = pygame.Rect(
            (screen.get_width() - panel_width) // 2,
            (screen.get_height() - panel_height) // 2,
            panel_width, panel_height
        )

        settings_panel = pygame_gui.elements.UIPanel(
            relative_rect=panel_rect,
            manager=manager
        )

        # Create scrolling container for settings
        container_rect = pygame.Rect(
            0, 0,
            panel_width - 40,  # Leave space for scrollbar
            len(settings) * 60 + sum(len(items) for items in settings.values()) * 50
        )

        scrolling_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=pygame.Rect(
                20, 20,
                panel_width - 40,
                panel_height - 100
            ),
            manager=manager,
            container=settings_panel
        )

        y_pos = 0
        self.ui_elements = {}
        
        # Create settings elements
        for category, items in settings.items():
            # Category label
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(0, y_pos, container_rect.width, 30),
                text=category,
                manager=manager,
                container=scrolling_container,
                object_id="#subtitle_label"
            )
            y_pos += 40

            for name, attr, min_val, max_val, *args in items:
                # Create label
                pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(10, y_pos, container_rect.width // 2 - 20, 30),
                    text=name,
                    manager=manager,
                    container=scrolling_container
                )

                # Create appropriate UI element based on value type
                if isinstance(getattr(self, attr), bool):
                    element = pygame_gui.elements.UIButton(
                        relative_rect=pygame.Rect(
                            container_rect.width // 2, y_pos,
                            container_rect.width // 2 - 20, 30
                        ),
                        text=str(getattr(self, attr)),
                        manager=manager,
                        container=scrolling_container
                    )
                else:
                    element = pygame_gui.elements.UIHorizontalSlider(
                        relative_rect=pygame.Rect(
                            container_rect.width // 2, y_pos,
                            container_rect.width // 2 - 20, 30
                        ),
                        start_value=float(getattr(self, attr)),
                        value_range=(float(min_val), float(max_val)),
                        manager=manager,
                        container=scrolling_container
                    )
                
                self.ui_elements[attr] = element
                y_pos += 50

        # Create Save and Cancel buttons
        button_width = 200
        button_height = 40
        spacing = 20

        save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                panel_width // 2 - button_width - spacing // 2,
                panel_height - button_height - 20,
                button_width, button_height
            ),
            text="Save",
            manager=manager,
            container=settings_panel
        )

        cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                panel_width // 2 + spacing // 2,
                panel_height - button_height - 20,
                button_width, button_height
            ),
            text="Cancel",
            manager=manager,
            container=settings_panel
        )

        running = True
        clock = pygame.time.Clock()
        while running:
            time_delta = clock.tick(60)/1000.0

            # Update demo game
            demo_game.update()

            # Draw
            screen.fill((20, 20, 30))
            demo_game.draw(screen, alpha=64)  # Draw demo game with low opacity

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                if event.type == pygame.USEREVENT:
                    if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                        if event.ui_element == save_button:
                            self.save_settings()
                            running = False
                        elif event.ui_element == cancel_button:
                            running = False
                        else:
                            # Handle boolean toggles
                            for attr, element in self.ui_elements.items():
                                if event.ui_element == element and isinstance(getattr(self, attr), bool):
                                    setattr(self, attr, not getattr(self, attr))
                                    element.set_text(str(getattr(self, attr)))

                # Update settings from sliders
                for attr, element in self.ui_elements.items():
                    if isinstance(element, pygame_gui.elements.UIHorizontalSlider):
                        setattr(self, attr, element.get_current_value())
                
                manager.process_events(event)

            manager.update(time_delta)
            manager.draw_ui(screen)
            pygame.display.flip()

        return self
