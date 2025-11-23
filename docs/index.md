# Treasure Hunt Agent

Welcome to the Treasure Hunt Agent documentation! This project provides a parametrized treasure hunt generator for testing AI agents. It creates complex filesystem trees with navigable paths from start to treasure, including red herrings and configurable difficulty.

## Overview

Treasure Hunt Agent is designed to test and benchmark AI agents by creating filesystem-based puzzles. The agent must navigate through directories, read clues, and find the treasure using a set of tools like `ls`, `cd`, `cat`, and `pwd`.

## Key Features

- **Parametrized Generation**: Control depth, branching factor, and file density
- **Difficulty Presets**: Easy, medium, and hard modes
- **Random Word Names**: Uses dictionary words for files/directories to prevent cheating
- **Reproducible**: Seeded random generation for testing
- **Navigable Paths**: Each clue contains relative path to next file
- **Configuration Files**: JSON config saves hunt metadata

## Quick Example

```bash
# Install dependencies
uv sync

# Generate a treasure hunt
python src/treasure_hunt_agent/treasure_hunt_generator.py

# Run the example agent
python examples/run_treasure_hunt.py
```

## Use Cases

- **Testing AI Agents**: Benchmark agent performance on filesystem navigation tasks
- **Educational**: Learn about agent architectures and tool-calling patterns
- **Research**: Study agent behavior with parametrized difficulty levels
- **Integration Testing**: Validate LLM APIs with structured challenges

## Getting Started

Check out the [Installation](getting-started/installation.md) guide to get up and running, then head to the [Quick Start](getting-started/quickstart.md) for your first treasure hunt!

## Architecture

The system consists of three main components:

1. **Treasure Hunt Generator**: Creates parametrized filesystem puzzles
2. **Agent**: LLM client using Gemini API with tool-calling support
3. **Game Loop**: Runs agent in loop, executes tools, validates paths

For more details, see the [Architecture](development/architecture.md) page.
