import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
from collections import deque

class DQN(nn.Module):
    def __init__(self, input_size, output_size, hidden_size):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, output_size)
        self.activations = None

    def forward(self, x):
        self.activations = []
        x = torch.relu(self.fc1(x))
        self.activations.append(x.detach())
        x = torch.relu(self.fc2(x))
        self.activations.append(x.detach())
        x = self.fc3(x)
        self.activations.append(x.detach())
        return x

class Agent:
    def __init__(self, settings):
        self.settings = settings
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        hidden_size = int(min(settings.width, settings.height) * 0.1)
        
        # Change the input size from 8 to 11
        self.input_size = 11
        self.policy_net = DQN(self.input_size, 3, hidden_size).to(self.device)
        self.target_net = DQN(self.input_size, 3, hidden_size).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=0.001)
        self.memory = PrioritizedReplayBuffer(capacity=100000000, alpha=0.6)
        self.batch_size = 64
        self.gamma = 0.99
        self.initial_epsilon = 1.0
        self.epsilon = self.initial_epsilon
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995  # We'll keep this as a base decay rate
        self.performance_window = deque(maxlen=100)  # Store recent performance
        self.target_performance = 0.6  # Target win rate (adjust as needed)
        self.epsilon_adjust_rate = 0.01  # Rate at which to adjust epsilon
        self.confidence = 0.0
        self.confidence_gain = 0.001  # Adjust this value to control how quickly confidence increases
        self.rebounds = 0
        self.max_rebounds = 100  # Maximum rebounds for 100% confidence
        self.beta = 0.4
        self.beta_increment = 0.001
        self.last_reward = None
        self.n_step = 3  # Number of steps for multi-step learning
        self.n_step_buffer = deque(maxlen=self.n_step)

    def get_action(self, state):
        if random.random() < self.epsilon:
            return random.choice([0, 1, 2])  # 0: stay, 1: up, 2: down
        else:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = self.policy_net(state_tensor)
                return q_values.max(1)[1].item()

    def update(self, state, action, reward, next_state):
        # Calculate the TD error for prioritization
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
        
        current_q = self.policy_net(state_tensor).gather(1, torch.tensor([[action]]).to(self.device)).item()
        next_q = self.target_net(next_state_tensor).max(1)[0].item()
        expected_q = reward + self.gamma * next_q
        
        td_error = abs(current_q - expected_q)
        
        self.last_reward = reward
        self.memory.add(td_error, (state, action, reward, next_state))

        if len(self.memory) < self.batch_size:
            return

        # Sample a batch of experiences based on their priorities
        batch, indices, weights = self.memory.sample(self.batch_size, self.beta)
        states, actions, rewards, next_states = zip(*batch)

        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        weights = torch.FloatTensor(weights).to(self.device)

        # Calculate current Q values
        current_q_values = self.policy_net(states).gather(1, actions.unsqueeze(1))

        # Double DQN
        next_actions = self.policy_net(next_states).max(1)[1].unsqueeze(1)
        next_q_values = self.target_net(next_states).gather(1, next_actions).squeeze(1)
        expected_q_values = rewards + (self.gamma * next_q_values)

        # Calculate loss with importance sampling weights
        loss = (weights * nn.functional.smooth_l1_loss(current_q_values, expected_q_values.unsqueeze(1), reduction='none')).mean()

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Update priorities in the replay buffer
        td_errors = abs(current_q_values - expected_q_values.unsqueeze(1)).detach().cpu().numpy()
        for i, td_error in zip(indices, td_errors):
            self.memory.update(i, td_error[0])

        self.dynamic_epsilon_decay(reward)

        # Increase beta for importance sampling
        self.beta = min(1.0, self.beta + self.beta_increment)

        self.n_step_buffer.append((state, action, reward))
        
        if len(self.n_step_buffer) >= self.n_step:
            n_step_return = self.calculate_n_step_return()
            self.memory.add(td_error, (self.n_step_buffer[0][0], self.n_step_buffer[0][1], n_step_return, next_state))
            self.n_step_buffer.popleft()

    def dynamic_epsilon_decay(self, reward):
        # Add the latest performance (1 for positive reward, 0 for negative)
        self.performance_window.append(1 if reward > 0 else 0)
        
        if len(self.performance_window) == self.performance_window.maxlen:
            current_performance = sum(self.performance_window) / len(self.performance_window)
            
            if current_performance < self.target_performance:
                # Increase epsilon (more exploration) if performance is below target
                self.epsilon = min(self.initial_epsilon, self.epsilon / (1 - self.epsilon_adjust_rate))
            else:
                # Decrease epsilon (more exploitation) if performance is above target
                self.epsilon = max(self.epsilon_min, self.epsilon * (1 - self.epsilon_adjust_rate))

    def update_target_network(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def get_network_activations(self, state):
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            self.policy_net(state_tensor)
            return self.policy_net.activations

    def get_learning_progress(self):
        # Calculate progress based on epsilon value
        progress = (self.initial_epsilon - self.epsilon) / (self.initial_epsilon - self.epsilon_min)
        return min(max(progress, 0), 1)  # Ensure progress is between 0 and 1

    def get_confidence(self):
        return min(self.rebounds / self.max_rebounds, 1.0)

    def add_rebound(self):
        self.rebounds += 1

    def reset_rebounds(self):
        self.rebounds = 0

    def calculate_n_step_return(self):
        return sum([self.gamma**i * transition[2] for i, transition in enumerate(self.n_step_buffer)])

    def train(self, state, action, next_state, reward, done):
        # Implement the training logic here
        # For now, we'll just pass to avoid the AttributeError
        pass

class PrioritizedReplayBuffer:
    def __init__(self, capacity, alpha):
        self.capacity = capacity
        self.alpha = alpha
        self.buffer = []
        self.priorities = np.zeros((capacity,), dtype=np.float32)
        self.position = 0
        self.critical_moment_bonus = 2.0

    def add(self, priority, experience):
        state, action, reward, next_state = experience
        
        # Increase priority for critical moments
        if abs(reward) > 1.0:  # Scoring or conceding a point
            priority *= self.critical_moment_bonus
        
        # Add a small constant to prevent zero priority
        priority = max(priority, 1e-5)
        
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience
        self.priorities[self.position] = priority
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size, beta):
        if len(self.buffer) == self.capacity:
            priorities = self.priorities
        else:
            priorities = self.priorities[:self.position]

        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()

        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities)
        samples = [self.buffer[idx] for idx in indices]

        total = len(self.buffer)
        weights = (total * probabilities[indices]) ** (-beta)
        weights /= weights.max()

        return samples, indices, weights

    def update(self, index, priority):
        self.priorities[index] = priority

    def __len__(self):
        return len(self.buffer)
