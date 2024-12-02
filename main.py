import pygame
import pygame_gui
import torch
import os
import shutil
from game.game_instance import GameInstance
from ai.agent import Agent
from ui.main_menu import MainMenu
from ui.game_ui import GameUI
from utils.settings import Settings
from ai.ai_factory import AIFactory
from game.human_player import HumanPlayer
import glob
import time

class PongAISimulation:
    def __init__(self):
        pygame.init()
        info = pygame.display.Info()
        self.screen_width = int(info.current_w * 0.8)  # Increased from 0.5 to 0.6
        self.screen_height = int(info.current_h * 0.8)  # Increased from 0.5 to 0.6
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Pong AI Simulation")
        self.clock = pygame.time.Clock()
        self.update_font()
        self.instances = []
        self.current_instance = None
        self.settings = Settings(self.screen_width, self.screen_height)
        self.main_menu = MainMenu(self.screen, self.settings)
        self.game_ui = GameUI(self.screen, self.font, self.settings)
        self.paused = False
        self.ai_types = ["dqn", "random"]
        self.current_ai_type = 0
        self.training_mode = False
        self.training_speed = 5
        self.accumulated_events = []
        self.event_update_interval = 60  # Update console every 60 frames (1 second at 60 FPS)
        self.frame_count = 0
        self.autosave_interval = 300  # Autosave every 5 minutes (300 seconds)
        self.last_autosave_time = time.time()
        self.generation = 1  # Add this line to keep track of the current generation
        self.save_directory = "saves"
        os.makedirs(self.save_directory, exist_ok=True)
        self.self_play_update_frequency = 1000  # Update every 1000 steps
        self.steps_since_last_update = 0
        self.human_player = None

    def update_font(self):
        self.font = pygame.font.Font(None, int(self.screen_height * 0.03))

    def run(self):
        running = True
        while running:
            time_delta = self.clock.tick(60) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.current_instance:
                            self.paused = not self.paused
                        else:
                            running = False
                    elif event.key == pygame.K_TAB:
                        self.current_ai_type = (self.current_ai_type + 1) % len(self.ai_types)
                        print(f"Switched to AI type: {self.ai_types[self.current_ai_type]}")
                    elif event.key == pygame.K_t:
                        self.training_mode = not self.training_mode
                        print(f"Training mode: {'ON' if self.training_mode else 'OFF'}")
                
                if self.current_instance is None:
                    self.main_menu.process_event(event)
                else:
                    self.game_ui.process_event(event)
                
                if self.human_player:
                    self.human_player.handle_event(event)

            if self.current_instance:
                self.run_game(time_delta)
            else:
                action = self.run_main_menu(time_delta)
                if action:
                    self.handle_menu_action(action)

            pygame.display.flip()

        pygame.quit()

    def run_main_menu(self, time_delta):
        return self.main_menu.update(time_delta)

    def handle_menu_action(self, action):
        if action == "new_game":
            self.create_new_instance()
        elif action == "load_game":
            self.load_instance()
        elif action == "settings":
            old_settings = self.settings
            self.settings = self.settings.show_settings_menu(self.screen, self.font)
            
            # Apply new settings to current game instance if it exists
            if self.current_instance:
                self.settings.apply_settings_to_game(self.current_instance)
            
            # Apply new settings to demo game in main menu
            self.settings.apply_settings_to_demo(self.main_menu.demo_game)

    def run_game(self, time_delta):
        if not self.paused:
            self.current_instance.update()
        self.frame_count += 1

        # Process accumulated events every second
        if self.frame_count >= self.event_update_interval:
            if self.accumulated_events:
                for event in self.accumulated_events:
                    self.game_ui.add_console_message(event)
                self.accumulated_events.clear()

            self.game_ui.add_console_message(f"Total Agent 1 reward: {self.current_instance.total_reward1:.2f}")
            self.game_ui.add_console_message(f"Total Agent 2 reward: {self.current_instance.total_reward2:.2f}")

            self.frame_count = 0

        # Autosave
        current_time = time.time()
        if current_time - self.last_autosave_time >= self.autosave_interval:
            self.autosave()
            self.last_autosave_time = current_time

        self.game_ui.draw(self.current_instance, self.paused, self.training_mode)

        # Check for UI events
        action = self.game_ui.check_ui_events()
        if action:
            self.handle_game_ui_action(action)

        self.steps_since_last_update += 1
        if self.steps_since_last_update >= self.self_play_update_frequency:
            self.update_opponent_for_self_play()
            self.steps_since_last_update = 0

    def handle_game_ui_action(self, action):
        if action == "save_game":
            self.save_game()
        elif action == "main_menu":
            self.current_instance = None
            self.human_player = None

    def handle_mouse_click(self, pos):
        if self.current_instance:
            if self.game_ui.check_button_click(pos, "Show Agent 1 Network"):
                self.game_ui.toggle_network_view("agent1")
            elif self.game_ui.check_button_click(pos, "Show Agent 2 Network"):
                self.game_ui.toggle_network_view("agent2")
            elif self.game_ui.check_button_click(pos, "Save Game"):
                self.save_game()
            elif self.game_ui.check_button_click(pos, "Main Menu"):
                self.current_instance = None
                self.human_player = None

    def create_new_instance(self):
        # Delete all existing save files
        self.delete_all_saves()
        
        agent1 = AIFactory.create_agent(self.ai_types[self.current_ai_type], self.settings)
        agent2 = AIFactory.create_agent(self.ai_types[self.current_ai_type], self.settings)
        self.current_instance = GameInstance(agent1, agent2, self.settings)
        self.instances.append(self.current_instance)
        self.generation = 1  # Reset generation counter
        self.game_ui.add_console_message("New game created. All previous saves deleted.")

    def load_instance(self):
        saves = glob.glob(os.path.join(self.save_directory, 'generation_*.pkl'))
        if saves:
            latest_save = max(saves, key=os.path.getctime)
            self.current_instance = GameInstance.load(latest_save)
            self.instances.append(self.current_instance)
            self.game_ui.add_console_message(f"Loaded latest save: {os.path.basename(latest_save)}")
            # Extract generation number from filename
            self.generation = int(os.path.basename(latest_save).split('_')[1].split('.')[0]) + 1
        else:
            self.game_ui.add_console_message("No saves found. Starting a new game.")
            self.create_new_instance()

    def autosave(self):
        if self.current_instance:
            filename = f'generation_{self.generation:04d}.pkl'
            filepath = os.path.join(self.save_directory, filename)
            self.current_instance.save(filepath)
            self.game_ui.add_console_message(f"Game autosaved: {filename}")
            self.generation += 1

    def save_game(self):
        if self.current_instance:
            filename = f'generation_{self.generation:04d}.pkl'
            filepath = os.path.join(self.save_directory, filename)
            self.current_instance.save(filepath)
            self.game_ui.add_console_message(f"Game manually saved: {filename}")
            self.generation += 1

    def delete_all_saves(self):
        for file in glob.glob(os.path.join(self.save_directory, 'generation_*.pkl')):
            os.remove(file)
        self.game_ui.add_console_message("All save files deleted.")

    def update_opponent_for_self_play(self):
        if isinstance(self.current_instance.agent2, Agent):
            self.current_instance.agent2.policy_net.load_state_dict(self.current_instance.agent1.policy_net.state_dict())
            self.game_ui.add_console_message("Updated opponent for self-play")

    def create_human_vs_ai_instance(self, agent_number):
        # Load the latest saved model
        latest_save = self.get_latest_save()
        if latest_save:
            loaded_instance = GameInstance.load(latest_save)
            if agent_number == 1:
                ai_agent = loaded_instance.agent1
            else:
                ai_agent = loaded_instance.agent2
            self.game_ui.add_console_message(f"Loaded AI model from: {os.path.basename(latest_save)}")
        else:
            # If no save exists, create a new AI agent
            ai_agent = AIFactory.create_agent(self.ai_types[self.current_ai_type], self.settings)
            self.game_ui.add_console_message("No saved model found. Created a new AI agent.")

        self.human_player = HumanPlayer(self.settings)
        
        if agent_number == 1:
            self.current_instance = GameInstance(ai_agent, self.human_player, self.settings)
        else:
            self.current_instance = GameInstance(self.human_player, ai_agent, self.settings)
        
        self.instances.append(self.current_instance)
        self.game_ui.add_console_message(f"New game created: Human vs AI (Agent {agent_number})")

    def get_latest_save(self):
        saves = glob.glob(os.path.join(self.save_directory, 'generation_*.pkl'))
        if saves:
            return max(saves, key=os.path.getctime)
        return None

if __name__ == "__main__":
    simulation = PongAISimulation()
    simulation.run()
