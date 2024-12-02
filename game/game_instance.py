import pygame
from game.paddle import Paddle
from game.ball import Ball
from ai.agent import Agent
import pickle
import os
import math
import random

class GameInstance:
    def __init__(self, agent1, agent2, settings):
        self.agent1 = agent1
        self.agent2 = agent2
        self.settings = settings
        self.paddle1 = Paddle(settings, side="left")
        self.paddle2 = Paddle(settings, side="right")
        self.ball = Ball(settings)
        self.reset_ball()  # Call reset_ball in the constructor
        self.score1 = 0
        self.score2 = 0
        self.events = []  # Store significant events for UI to display
        self.last_hit = None  # Track which paddle last hit the ball
        self.total_reward1 = 0
        self.total_reward2 = 0
        self.ball_hits1 = 0
        self.ball_hits2 = 0
        self.performance_score1 = 0
        self.performance_score2 = 0
        self.last_distance1 = self._get_paddle_ball_distance(self.paddle1)
        self.last_distance2 = self._get_paddle_ball_distance(self.paddle2)
        self.total_hits1 = 0
        self.total_hits2 = 0
        self.time_since_last_hit = 0
        self.difficulty = 1.0
        self.max_difficulty = 2.0
        self.difficulty_increase_rate = 0.001
        self.difficulty_decrease_rate = 0.0005
        self.consecutive_hits = 0
        self.max_consecutive_hits = 10
        self.consecutive_misses = 0
        self.max_consecutive_misses = 5
        self.max_speed_increase = 2.0  # Maximum speed multiplier
        self.speed_increase_rate = 0.1  # Speed increase per consecutive hit

        # Apply settings
        self.settings = settings
        self.apply_settings()

    def apply_settings(self):
        """Apply current settings to the game"""
        self.ball_speed = self.settings.ball_speed
        self.paddle_speed = self.settings.paddle_speed
        self.glow_intensity = self.settings.glow_intensity
        self.show_trails = self.settings.show_trails
        self.trail_length = self.settings.trail_length

    def reset_ball(self):
        self.ball.reset()
        angle = random.uniform(-math.pi/4, math.pi/4)  # Angle between -45 and 45 degrees
        self.ball.dx = math.cos(angle) * self.ball.speed
        self.ball.dy = math.sin(angle) * self.ball.speed
        if random.choice([True, False]):
            self.ball.dx = -self.ball.dx  # Randomly choose initial direction
        
        # Ensure the ball is not stuck with zero velocity
        while abs(self.ball.dx) < 0.1 or abs(self.ball.dy) < 0.1:
            angle = random.uniform(-math.pi/4, math.pi/4)
            self.ball.dx = math.cos(angle) * self.ball.speed
            self.ball.dy = math.sin(angle) * self.ball.speed

    def update(self):
        state1 = self.get_state(self.paddle1, self.paddle2)
        state2 = self.get_state(self.paddle2, self.paddle1)

        action1 = self.agent1.get_action(state1)
        action2 = self.agent2.get_action(state2)

        self.paddle1.move(action1)
        self.paddle2.move(action2)
        self.ball.move()
        
        # Add ball collision with top and bottom walls
        if self.ball.y <= 0 or self.ball.y >= self.settings.height:
            self.ball.dy = -self.ball.dy

        reward1 = self._calculate_reward(self.paddle1, action1, 1)
        reward2 = self._calculate_reward(self.paddle2, action2, 2)

        # Check for collisions and update rewards
        hit_occurred = False
        if self.paddle1.collides_with(self.ball):
            self.ball.bounce()
            self.consecutive_hits += 1
            self.consecutive_misses = 0
            self.update_ball_speed()
            reward1 += 0.5  # Reduced reward for hitting the ball
            self.last_hit = self.paddle1
            self.events.append("Agent 1 hit the ball")
            if isinstance(self.agent1, Agent):
                self.agent1.add_rebound()
            self.ball_hits1 += 1
            self.total_hits1 += 1
            hit_occurred = True
        elif self.paddle2.collides_with(self.ball):
            self.ball.bounce()
            self.consecutive_hits += 1
            self.consecutive_misses = 0
            self.update_ball_speed()
            reward2 += 0.5  # Reduced reward for hitting the ball
            self.last_hit = self.paddle2
            self.events.append("Agent 2 hit the ball")
            if isinstance(self.agent2, Agent):
                self.agent2.add_rebound()
            self.ball_hits2 += 1
            self.total_hits2 += 1
            hit_occurred = True
        else:
            self.consecutive_hits = 0  # Reset consecutive hits if ball wasn't hit
            self.consecutive_misses += 1

        self.time_since_last_hit += 1
        if self.paddle1.collides_with(self.ball) or self.paddle2.collides_with(self.ball):
            self.time_since_last_hit = 0

        if self.ball.is_out():
            if self.ball.x < self.settings.width / 2:
                self.score2 += 1
                reward1 -= 2.0  # Increased penalty for losing a point
                reward2 += 2.0  # Increased reward for scoring a point
                self.events.append("Agent 2 scores!")
                if isinstance(self.agent1, Agent):
                    self.agent1.reset_rebounds()
            else:
                self.score1 += 1
                reward1 += 2.0  # Increased reward for scoring a point
                reward2 -= 2.0  # Increased penalty for losing a point
                self.events.append("Agent 1 scores!")
                if isinstance(self.agent2, Agent):
                    self.agent2.reset_rebounds()
            self.reset_ball()  # Make sure this line is here

        new_state1 = self.get_state(self.paddle1, self.paddle2)
        new_state2 = self.get_state(self.paddle2, self.paddle1)

        self.agent1.update(state1, action1, reward1, new_state1)
        self.agent2.update(state2, action2, reward2, new_state2)

        self.total_reward1 += reward1
        self.total_reward2 += reward2

        # Only add reward events if there's a significant change
        if abs(reward1) >= 0.1:
            self.events.append(f"Agent 1 reward: {reward1:.2f}")
        if abs(reward2) >= 0.1:
            self.events.append(f"Agent 2 reward: {reward2:.2f}")

        # Update performance scores
        self.update_performance_scores()

        # Update last distances for the next iteration
        self.last_distance1 = self._get_paddle_ball_distance(self.paddle1)
        self.last_distance2 = self._get_paddle_ball_distance(self.paddle2)

        # Update difficulty based on whether a hit occurred
        self.update_difficulty(hit_occurred)

    def reward_energy_conservation(self, paddle):
        # Calculate the energy conservation reward
        current_distance = self._get_paddle_ball_distance(paddle)
        last_distance = self.last_distance1 if paddle == self.paddle1 else self.last_distance2
        distance_change = last_distance - current_distance
        reward = distance_change * 0.05  # Small reward for conserving energy
        return reward

    def reward_defensive_positioning(self, paddle):
        # Calculate the defensive positioning reward
        middle_y = self.settings.height / 2
        distance_to_middle = abs(paddle.y + paddle.height/2 - middle_y)
        middle_reward = 1 - (distance_to_middle / (self.settings.height/2))
        reward = middle_reward * 0.05  # Small reward for being in the middle
        return reward

    def _calculate_reward(self, paddle, action, player_number):
        reward = 0

        # Reward for moving towards the ball
        current_distance = self._get_paddle_ball_distance(paddle)
        last_distance = self.last_distance1 if player_number == 1 else self.last_distance2
        distance_reward = (last_distance - current_distance) * 0.05  # Reduced distance reward
        reward += distance_reward

        # Penalty for unnecessary movement
        if action != 0 and abs(paddle.y + paddle.height/2 - self.ball.y) < paddle.height/4:
            reward -= 0.02  # Reduced penalty

        # Reward for staying in the middle when the ball is far
        if abs(self.ball.x - paddle.x) > self.settings.width / 2:
            middle_y = self.settings.height / 2
            distance_to_middle = abs(paddle.y + paddle.height/2 - middle_y)
            middle_reward = 1 - (distance_to_middle / (self.settings.height/2))
            reward += middle_reward * 0.05  # Reduced middle reward

        # Penalty for keeping the paddle out of play area
        if paddle.y < 0 or paddle.y + paddle.height > self.settings.height:
            reward -= 0.05  # Reduced out-of-bounds penalty

        # Reward for keeping the paddle aligned with the ball
        if paddle.y + paddle.height/2 < self.ball.y:
            reward += 0.05  # Reward for being above the ball
        elif paddle.y + paddle.height/2 > self.ball.y:
            reward -= 0.05  # Penalty for being below the ball

        # Reward for anticipating the ball
        if self.ball.dx == 0:
            predicted_y = self.ball.y
        else:
            predicted_y = self.ball.y + self.ball.dy * (self.paddle1.x - self.ball.x) / self.ball.dx

        if paddle.y + paddle.height/2 < predicted_y:
            reward += 0.05  # Reward for being above the predicted ball position
        elif paddle.y + paddle.height/2 > predicted_y:
            reward -= 0.05  # Penalty for being below the predicted ball position

        # Reward energy conservation
        reward += self.reward_energy_conservation(paddle)

        # Defensive positioning reward
        reward += self.reward_defensive_positioning(paddle)

        # Reward for defensive hits


        return reward

    def _get_paddle_ball_distance(self, paddle):
        return math.sqrt((paddle.x - self.ball.x)**2 + (paddle.y + paddle.height/2 - self.ball.y)**2)

    def get_state(self, paddle, opponent_paddle):
        predicted_x, predicted_y = self.predict_ball_position()
        return [
            paddle.y / self.settings.height,
            opponent_paddle.y / self.settings.height,
            self.ball.x / self.settings.width,
            self.ball.y / self.settings.height,
            self.ball.dx / self.settings.width,
            self.ball.dy / self.settings.height,
            predicted_x / self.settings.width,
            predicted_y / self.settings.height,
            self.time_since_last_hit / 100,  # Normalize to a reasonable range
            self.difficulty,
            1 if self.last_hit == paddle else 0  # Indicate if this paddle last hit the ball
        ]

    def predict_ball_position(self):
        # Simple linear prediction
        time_to_reach = (self.paddle1.x - self.ball.x) / self.ball.dx if self.ball.dx != 0 else 0
        predicted_x = self.ball.x + self.ball.dx * time_to_reach
        predicted_y = self.ball.y + self.ball.dy * time_to_reach
        return predicted_x, predicted_y

    def save(self, filename):
        save_data = {
            'agent1': self.agent1,
            'agent2': self.agent2,
            'score1': self.score1,
            'score2': self.score2,
            'settings': self.settings,
            'total_reward1': self.total_reward1,
            'total_reward2': self.total_reward2
        }
        with open(filename, 'wb') as f:
            pickle.dump(save_data, f)

    @classmethod
    def load(cls, filename):
        with open(filename, 'rb') as f:
            save_data = pickle.load(f)
        
        instance = cls(save_data['agent1'], save_data['agent2'], save_data['settings'])
        instance.score1 = save_data['score1']
        instance.score2 = save_data['score2']
        instance.total_reward1 = save_data.get('total_reward1', 0)
        instance.total_reward2 = save_data.get('total_reward2', 0)
        return instance

    def get_learning_progress(self):
        if isinstance(self.agent1, Agent):
            progress1 = self.agent1.get_learning_progress()
        else:
            progress1 = 1.0  # Assume non-learning agents are always at 100%

        if isinstance(self.agent2, Agent):
            progress2 = self.agent2.get_learning_progress()
        else:
            progress2 = 1.0

        return (progress1 + progress2) / 2  # Average progress of both agents

    def get_confidence(self):
        confidence1 = self.agent1.get_confidence() if isinstance(self.agent1, Agent) else 1.0
        confidence2 = self.agent2.get_confidence() if isinstance(self.agent2, Agent) else 1.0
        return confidence1, confidence2

    def update_performance_scores(self):
        # Calculate performance scores based on various factors
        score_weight = 1
        hits_weight = 0.1

        self.performance_score1 = (
            self.score1 * score_weight +
            self.total_hits1 * hits_weight
        )
        self.performance_score2 = (
            self.score2 * score_weight +
            self.total_hits2 * hits_weight
        )

    def get_performance_ratio(self):
        total_score = self.performance_score1 + self.performance_score2
        if total_score == 0:
            return 0.5  # If no score, return a neutral value
        return self.performance_score1 / total_score

    def update_difficulty(self, success):
        if success:
            if self.consecutive_hits >= self.max_consecutive_hits:
                self.difficulty = min(self.difficulty + self.difficulty_increase_rate, self.max_difficulty)
        else:
            if self.consecutive_misses >= self.max_consecutive_misses:
                self.difficulty = max(1.0, self.difficulty - self.difficulty_decrease_rate)
        
        self.ball.speed = self.settings.ball_speed * self.difficulty

    def reward_alignment(self, paddle):
        vertical_distance = abs(paddle.y + paddle.height/2 - self.ball.y)
        max_distance = self.settings.height / 2
        alignment_factor = 1 - (vertical_distance / max_distance)
        return alignment_factor * 0.1

    def reward_offensive_hit(self):
        if self.ball.dx > 0:  # Ball moving towards opponent
            return 0.2  # Reduced offensive hit reward
        return 0

    def update_ball_speed(self):
        speed_multiplier = min(1 + (self.consecutive_hits * self.speed_increase_rate), self.max_speed_increase)
        self.ball.speed = self.settings.ball_speed * speed_multiplier

