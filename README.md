# Treasure Hunt Agent

A parametrized treasure hunt generator for testing AI agents. Creates complex filesystem trees with navigable paths from start to treasure, including red herrings and configurable difficulty.

## Features

- **Parametrized Generation**: Control depth, branching factor, and file density
- **Difficulty Presets**: Easy, medium, and hard modes
- **Random Word Names**: Uses dictionary words for files/directories to prevent cheating
- **Reproducible**: Seeded random generation for testing
- **Navigable Paths**: Each clue contains relative path to next file
- **Configuration Files**: JSON config saves hunt metadata

## Installation

```bash
# Project uses uv for dependency management
cd treasure_hunt_agent
uv sync
```

## Usage

### Generate a Treasure Hunt

```bash
# Generate with default settings (medium difficulty)
python src/treasure_hunt_generator.py

# Generate with custom parameters
python src/treasure_hunt_generator.py --depth 6 --difficulty hard --seed 42

# See all options
python src/treasure_hunt_generator.py --help
```

### Run the Example Agent

```bash
# Navigate a generated treasure hunt
python src/example_agent.py --hunt-path ./treasure_hunt
```

### Run Tests

```bash
pytest tests/test_treasure_hunt_generator.py -v
```

## Treasure Hunt Structure

A generated hunt creates:

```
treasure_hunt/
├── .treasure_hunt_config.json  # Configuration and metadata
├── [start_file].txt             # Starting point
├── [dir1]/
│   ├── [clue1].txt             # Points to next location
│   ├── [dir2]/
│   │   ├── [clue2].txt
│   │   └── [treasure].txt      # Final treasure with key
│   └── [red_herring_dir]/      # Dead ends
└── [red_herring_dir]/
```

### Configuration File

The `.treasure_hunt_config.json` file contains:

```json
{
  "treasure_key": "randomkey123",
  "start_file": "start_word.txt",
  "treasure_file": "path/to/treasure.txt",
  "path_length": 5,
  "golden_path": ["dir1", "dir2", "dir3"],
  "depth": 6,
  "branching_factor": 3,
  "seed": 42
}
```

## Parameters

- `--depth`: Maximum depth of directory tree (default: from difficulty)
- `--branching-factor`: Average subdirectories per directory (default: from difficulty)
- `--file-density`: Probability of creating clue files (0-1, default: from difficulty)
- `--seed`: Random seed for reproducibility
- `--difficulty`: Preset difficulty (easy/medium/hard)
- `--base-path`: Output directory (default: ./treasure_hunt)

## Difficulty Presets

| Difficulty | Depth | Branching | File Density |
|-----------|-------|-----------|--------------|
| Easy      | 4     | 2         | 0.2          |
| Medium    | 6     | 3         | 0.3          |
| Hard      | 8     | 4         | 0.4          |

## Development

Tests are written using pytest with TDD methodology:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_treasure_hunt_generator.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Running the Complete System

### Integration Test with Gemini API

Run a complete treasure hunt with a real Gemini agent:

```bash
# Set your Gemini API key
export GOOGLE_API_KEY='your-api-key-here'

# Run with default settings (easy difficulty)
python examples/run_treasure_hunt.py

# Run with custom settings
python examples/run_treasure_hunt.py --difficulty medium --seed 123 --max-turns 30

# Keep the treasure hunt directory after completion
python examples/run_treasure_hunt.py --keep-hunt
```

The integration test will:
1. Generate a treasure hunt
2. Create a Gemini agent
3. Run the game loop
4. Show detailed results including tool calls and token usage

### Architecture

The system consists of three main components:

1. **Treasure Hunt Generator** (`src/treasure_hunt_generator.py`)
   - Creates parametrized filesystem puzzles
   - Random word-based names to prevent cheating

2. **Agent** (`src/gemini_agent.py`)
   - LLM client using Gemini API
   - Manages conversation and tool calling
   - Tracks token usage

3. **Game Loop** (`src/treasure_hunt_game.py`)
   - Runs agent in loop
   - Executes tools (ls, cd, cat, pwd, check_treasure, etc.)
   - Validates paths stay within hunt boundaries
   - Tracks turns, tokens, time

## Next Steps

- [ ] Add Docker sandboxing for secure agent execution
- [ ] Create multiple agent implementations (langchain, llm, ADK)
- [ ] Add difficulty scaling and performance metrics
- [ ] Implement docs/help system
- [ ] Add cost tracking and optimization
