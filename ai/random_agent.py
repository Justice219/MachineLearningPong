import random

class RandomAgent:
    def __init__(self, settings):
        self.settings = settings
        self.epsilon = 1.0
        self.memory = []

    def get_action(self, state):
        return random.choice([0, 1, 2])

    def update(self, state, action, reward, next_state):
        self.memory.append((state, action, reward, next_state))
        if len(self.memory) > 1000:
            self.memory.pop(0)

    def get_network_activations(self, state):
        return None  # Random agent doesn't have a neural network
