import pygame
import torch
import torch.nn as nn
import numpy as np

class NetworkVisualizer:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font

    def draw_network(self, network, activations, game_area):
        # Create a transparent surface for the network visualization
        network_surface = pygame.Surface(game_area.size, pygame.SRCALPHA)
        
        layers = [module for module in network.modules() if isinstance(module, torch.nn.Linear)]
        layer_sizes = [layer.in_features for layer in layers] + [layers[-1].out_features]

        width, height = game_area.size
        vertical_spacing = height / (len(layer_sizes) - 1)
        
        for i, layer_size in enumerate(layer_sizes):
            layer_y = i * vertical_spacing
            horizontal_spacing = width / (layer_size + 1)
            
            for j in range(layer_size):
                node_x = (j + 1) * horizontal_spacing
                node_y = layer_y
                
                # Calculate color based on activation
                if i < len(activations) and j < activations[i].shape[1]:
                    activation = activations[i][0][j].item()
                    color = self.get_color_from_activation(activation)
                else:
                    color = (200, 200, 200, 255)  # Default color
                
                pygame.draw.circle(network_surface, color, (int(node_x), int(node_y)), 5)
                
                if i < len(layer_sizes) - 1:
                    next_layer_y = (i + 1) * vertical_spacing
                    next_layer_size = layer_sizes[i + 1]
                    next_horizontal_spacing = width / (next_layer_size + 1)
                    
                    for k in range(next_layer_size):
                        next_node_x = (k + 1) * next_horizontal_spacing
                        next_node_y = next_layer_y
                        line_color = self.get_line_color(color, (200, 200, 200, 255))
                        pygame.draw.line(network_surface, line_color, 
                                         (int(node_x), int(node_y)), 
                                         (int(next_node_x), int(next_node_y)), 1)

        # Blit the network surface onto the game area
        self.screen.blit(network_surface, game_area.topleft)

    def get_color_from_activation(self, activation):
        # Map activation to color: blue for negative, red for positive
        if activation < 0:
            return (0, 0, min(255, int(-activation * 255)), 255)
        else:
            return (min(255, int(activation * 255)), 0, 0, 255)

    def get_line_color(self, start_color, end_color):
        # Create a gradient color for the line
        return tuple((start + end) // 2 for start, end in zip(start_color, end_color))
