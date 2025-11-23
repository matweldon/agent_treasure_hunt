# Quick Start

This guide will walk you through generating and running your first treasure hunt.

## Generate Your First Treasure Hunt

The simplest way to generate a treasure hunt is with default settings:

```bash
python src/treasure_hunt_agent/treasure_hunt_generator.py
```

This creates a `treasure_hunt/` directory with medium difficulty settings.

### Custom Parameters

You can customize the treasure hunt generation:

```bash
python src/treasure_hunt_agent/treasure_hunt_generator.py \
  --depth 6 \
  --branching-factor 3 \
  --difficulty hard \
  --seed 42 \
  --base-path ./my_hunt
```

### Available Parameters

- `--depth`: Maximum depth of directory tree
- `--branching-factor`: Average subdirectories per directory
- `--file-density`: Probability of creating clue files (0-1)
- `--seed`: Random seed for reproducibility
- `--difficulty`: Preset difficulty (easy/medium/hard)
- `--base-path`: Output directory

## Understanding the Structure

A generated treasure hunt looks like this:

```
treasure_hunt/
├── .treasure_hunt_config.json  # Configuration and metadata
├── start_word.txt              # Starting point with first clue
├── directory1/
│   ├── clue1.txt              # Points to next location
│   ├── directory2/
│   │   ├── clue2.txt
│   │   └── treasure.txt       # Final treasure with key
│   └── red_herring/           # Dead end
└── another_dir/               # More red herrings
```

### The Configuration File

The `.treasure_hunt_config.json` contains important metadata:

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

## Run the Example Agent

Once you have a treasure hunt generated, you can run the example agent:

```bash
python src/treasure_hunt_agent/example_agent.py --hunt-path ./treasure_hunt
```

This will demonstrate how an agent can navigate the filesystem to find the treasure.

## Run with Gemini Agent

For a full integration test with a real LLM:

```bash
# Set your API key
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

## Difficulty Presets

Choose from three difficulty levels:

| Difficulty | Depth | Branching | File Density | Description |
|-----------|-------|-----------|--------------|-------------|
| Easy      | 4     | 2         | 0.2          | Shallow, fewer options |
| Medium    | 6     | 3         | 0.3          | Balanced challenge |
| Hard      | 8     | 4         | 0.4          | Deep, many branches |

## Next Steps

- Learn more about [generating treasure hunts](../user-guide/generating-hunts.md)
- Understand [agent tools and capabilities](../user-guide/running-agents.md)
- Explore [configuration options](../user-guide/configuration.md)
