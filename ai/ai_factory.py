from .agent import Agent, PrioritizedReplayBuffer
from .random_agent import RandomAgent

class AIFactory:
    @staticmethod
    def create_agent(agent_type, settings):
        if agent_type == "dqn":
            return Agent(settings)
        elif agent_type == "random":
            return RandomAgent(settings)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
