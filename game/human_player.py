import pygame

class HumanPlayer:
    def __init__(self, settings):
        self.settings = settings
        self.paddle_speed = settings.paddle_speed
        self.move_up = False
        self.move_down = False
        self.last_reward = 0  # Add this line

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.move_up = True
            elif event.key == pygame.K_DOWN:
                self.move_down = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                self.move_up = False
            elif event.key == pygame.K_DOWN:
                self.move_down = False

    def get_action(self, state):
        if self.move_up:
            return 1
        elif self.move_down:
            return 2
        else:
            return 0

    def update(self, state, action, reward, next_state):
        self.last_reward = reward  # Update this method to store the last reward
        pass  # Human player doesn't need to learn

    def get_network_activations(self, state):
        return None  # Human player doesn't have a neural network
