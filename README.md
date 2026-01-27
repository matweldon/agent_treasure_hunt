# Treasure Hunt Agent

A parametrized treasure hunt generator for testing AI agents. Creates complex filesystem trees with navigable paths from start to treasure, including red herrings and configurable difficulty.

## Features

- **Parametrized Generation**: Control depth, branching factor, and file density
- **Difficulty Presets**: Easy, medium, and hard modes
- **Interactive CLI**: Beautiful terminal UI with typer and rich
- **Two Running Modes**: Batch mode (automated) or interactive mode (step-by-step)
- **Random Word Names**: Uses dictionary words for files/directories to prevent cheating
- **Reproducible**: Seeded random generation for testing
- **Navigable Paths**: Each clue contains relative path to next file
- **Human Input Support**: Agent can ask questions during gameplay

## Installation

### Local Installation with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager. Install it first:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then set up the project:

```bash
# Clone and enter the project
git clone <repo-url>
cd agent_treasure_hunt

# Install dependencies (creates virtual environment automatically)
uv sync

# Set your Gemini API key
export GOOGLE_API_KEY='your-api-key-here'
```

### Running with uv

All commands should be prefixed with `uv run` to use the project's virtual environment:

```bash
# Run the CLI
uv run treasure-hunt --help

# Quick start: generate and run a treasure hunt
uv run treasure-hunt quick --difficulty easy --interactive

# Generate a hunt
uv run treasure-hunt generate ./my_hunt --difficulty medium

# Run an existing hunt
uv run treasure-hunt run ./my_hunt --interactive

# Run the example script
uv run python examples/run_treasure_hunt.py --interactive
```

### Running Tests

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test file
uv run python -m pytest tests/test_treasure_hunt_game.py -v
```

---

## Container Installation (Docker / GitHub Codespaces)

The project includes a secure Docker container setup with sandboxing and network restrictions.

### Using GitHub Codespaces

1. Fork or clone this repository to GitHub
2. Click "Code" → "Codespaces" → "Create codespace on main"
3. The devcontainer will automatically set up the environment
4. Set your API key: `export GOOGLE_API_KEY='your-api-key'`

### Using Docker Locally

```bash
# Build and start the container
docker-compose -f .devcontainer/docker-compose.yml up -d

# Enter the container
docker-compose -f .devcontainer/docker-compose.yml exec agent bash

# Set your API key
export GOOGLE_API_KEY='your-api-key-here'

# Run the treasure hunt
uv run treasure-hunt quick --interactive
```

### Security Features

The Docker container includes:
- **Non-root user execution** (UID 1000)
- **Dropped capabilities** (minimal permissions)
- **Network restrictions** (access only to trusted domains)
- **Resource limits** (CPU and memory constraints)
- **Isolated filesystem** (sandboxed environment)

See [.devcontainer/SECURITY.md](.devcontainer/SECURITY.md) for detailed security documentation.

---

## CLI Usage

The `treasure-hunt` CLI provides three commands:

### Quick Start (Generate + Run)

```bash
# Interactive mode with real-time turn display
uv run treasure-hunt quick --difficulty easy --interactive

# Batch mode (runs to completion)
uv run treasure-hunt quick --difficulty medium --batch

# With custom options
uv run treasure-hunt quick --difficulty hard --seed 42 --max-turns 30 --keep
```

### Generate a Treasure Hunt

```bash
# Generate with default settings
uv run treasure-hunt generate ./my_hunt

# Generate with options
uv run treasure-hunt generate ./my_hunt --difficulty hard --seed 42

# Overwrite existing
uv run treasure-hunt generate ./my_hunt --force
```

### Run an Existing Hunt

```bash
# Interactive mode (see each turn as it happens)
uv run treasure-hunt run ./my_hunt --interactive

# Batch mode (show results at end)
uv run treasure-hunt run ./my_hunt --batch

# With custom model and limits
uv run treasure-hunt run ./my_hunt --model gemini-2.0-flash --max-turns 100
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--difficulty`, `-d` | easy, medium, or hard |
| `--seed`, `-s` | Random seed for reproducibility |
| `--model`, `-m` | Gemini model name |
| `--max-turns`, `-t` | Maximum turns allowed |
| `--interactive/-i`, `--batch/-b` | Show turns live or run to completion |
| `--keep`, `-k` | Keep generated hunt directory after completion |
| `--api-key` | Google API key (or use GOOGLE_API_KEY env var) |

---

## Programmatic Usage

### Batch Mode (Simple)

```python
from treasure_hunt_agent import TreasureHuntGame
from treasure_hunt_agent.gemini_agent import GeminiAgent
from treasure_hunt_agent.game_tools import TOOL_DEFINITIONS

# Create agent
agent = GeminiAgent(
    model_name="gemini-2.5-flash",
    system_instructions="You are a treasure hunter...",
    tools=TOOL_DEFINITIONS,
)

# Create and run game
game = TreasureHuntGame("./my_hunt", agent)
result = game.run()

print(f"Success: {result.success}")
print(f"Turns: {result.turns_taken}")
print(f"Tokens: {result.total_tokens}")
```

### Interactive Mode (Step-by-Step)

```python
from treasure_hunt_agent import TreasureHuntGame

game = TreasureHuntGame("./my_hunt", agent)

while True:
    turn = game.take_turn()

    # Display turn info
    print(f"Turn {turn.turn_number}")
    for tc in turn.tool_calls:
        print(f"  {tc['name']}({tc['arguments']}) -> {tc['result'][:50]}...")

    # Handle human input if agent asks a question
    if turn.needs_human_input:
        response = input(f"Agent asks: {turn.pending_question}\nYour response: ")
        turn = game.take_turn(human_input=response)

    if turn.game_over:
        print(f"Game over! Success: {turn.game_result.success}")
        break
```

### Custom Input Providers

```python
from treasure_hunt_agent import AutoInputProvider, CallbackInputProvider

# For testing: provide canned responses
provider = AutoInputProvider(["look in the basement", "check the safe"])

# For integration: custom callback
def my_callback(question: str) -> str:
    # Could call an API, show a UI dialog, etc.
    return fetch_response_from_somewhere(question)

provider = CallbackInputProvider(my_callback)
```

---

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

## Difficulty Presets

| Difficulty | Depth | Branching | File Density |
|-----------|-------|-----------|--------------|
| Easy      | 4     | 2         | 0.2          |
| Medium    | 6     | 3         | 0.3          |
| Hard      | 8     | 4         | 0.4          |

---

## Architecture

The system consists of these main components:

1. **Treasure Hunt Generator** (`treasure_hunt_generator.py`)
   - Creates parametrized filesystem puzzles
   - Random word-based names to prevent cheating

2. **Agent** (`gemini_agent.py`)
   - LLM client using Gemini API
   - Manages conversation and tool calling
   - Tracks token usage

3. **Game Loop** (`treasure_hunt_game.py`)
   - `run()`: Batch mode - runs to completion
   - `take_turn()`: Interactive mode - one turn at a time
   - Executes tools (ls, cd, cat, pwd, check_treasure, give_up, ask_human)
   - Validates paths stay within hunt boundaries
   - Tracks turns, tokens, time

4. **CLI** (`cli.py`)
   - Beautiful terminal interface using typer and rich
   - Interactive and batch modes
   - Real-time turn display

5. **Input Providers** (`input_providers.py`)
   - Protocol for pluggable human input
   - CLI, automatic (for testing), and callback implementations

## Available Tools

The agent has access to these tools:

| Tool | Description |
|------|-------------|
| `ls(path)` | List files and directories |
| `cd(path)` | Change working directory |
| `cat(file_path)` | Read file contents |
| `pwd()` | Print current directory |
| `check_treasure(key)` | Check if key is correct (ends game if correct) |
| `give_up()` | Give up (ends game as failure) |
| `ask_human(question)` | Ask the human for help |

---

## Development

### Running Tests

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test file
uv run python -m pytest tests/test_treasure_hunt_game.py -v

# Run with coverage
uv run python -m pytest tests/ --cov=src --cov-report=html
```

### Project Structure

```
agent_treasure_hunt/
├── src/treasure_hunt_agent/
│   ├── __init__.py           # Package exports
│   ├── cli.py                # Typer CLI with rich output
│   ├── game_tools.py         # Tool implementations
│   ├── gemini_agent.py       # Gemini LLM client
│   ├── input_providers.py    # Human input protocols
│   ├── treasure_hunt_game.py # Game loop (run/take_turn)
│   └── treasure_hunt_generator.py
├── examples/
│   └── run_treasure_hunt.py  # Example script
├── tests/
│   └── test_*.py             # Test files
├── pyproject.toml            # Dependencies and config
└── uv.lock                   # Lock file for reproducibility
```

## Next Steps

- [x] Add Docker sandboxing for secure agent execution
- [x] Add interactive mode with step-by-step control
- [x] Add rich CLI with typer
- [ ] Create multiple agent implementations (langchain, llm, ADK)
- [ ] Add difficulty scaling and performance metrics
- [ ] Implement docs/help system
- [ ] Add cost tracking and optimization
