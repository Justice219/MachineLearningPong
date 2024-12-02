# AI Pong Simulator

A Python-based Pong game simulator that allows AI agents to learn and play against each other, featuring real-time neural network visualization.

## Features

- Multiple AI agent types support
- Real-time neural network visualization
- Training mode with adjustable speed
- Save and load game states
- Interactive console for game feedback
- Dynamic screen scaling

## Requirements

- Python 3.x
- PyGame
- PyTorch
- NumPy

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-pong-simulator.git
   cd ai-pong-simulator
   ```

2. Install the required dependencies:
   ```bash
   pip install pygame torch numpy
   ```

## Usage

Run the main script to start the simulator:
```bash
python main.py
```

### Creating a New Game

1. Select "New Game" from the menu
2. Choose AI types for both players
3. Set the training mode and speed
4. Start the simulation

### Features

- **Neural Network Visualization**: Watch the AI's decision-making process in real-time through the network visualizer
- **Training Mode**: Toggle training mode to allow AI agents to learn and improve
- **Save/Load**: Save your progress and load previous game states
- **Multiple AI Types**: Choose from different AI implementations for each player

## Project Structure

- `main.py` - Main game loop and simulation controller
- `ui/` - User interface components
  - `network_visualizer.py` - Neural network visualization
  - `new_game_menu.py` - Game creation interface
  - `game_ui.py` - Main game interface
  - `main_menu.py` - Main menu interface
- `game/` - Core game components
  - `game_instance.py` - Game instance management
  - `paddle.py` - Paddle mechanics
  - `ball.py` - Ball mechanics
- `ai/` - AI implementations
  - `agent.py` - DQN agent implementation
  - `random_agent.py` - Random agent implementation
  - `ai_factory.py` - Factory for creating AI agents
- `utils/` - Utility functions
  - `settings.py` - Game settings management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)

## Acknowledgments

- Built with PyGame and PyTorch
- Neural network visualization inspired by deep learning visualization techniques
