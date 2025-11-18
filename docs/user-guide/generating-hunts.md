# Generating Treasure Hunts

This guide covers everything you need to know about generating treasure hunts with custom parameters and difficulty settings.

## Basic Generation

Generate a treasure hunt with default medium difficulty:

```bash
python src/treasure_hunt_agent/treasure_hunt_generator.py
```

## Advanced Parameters

### Depth

Controls how deep the directory tree can go:

```bash
python src/treasure_hunt_agent/treasure_hunt_generator.py --depth 8
```

- **Lower depth (4-5)**: Easier navigation, fewer levels to explore
- **Higher depth (8-10)**: More complex, requires careful tracking

### Branching Factor

Controls the average number of subdirectories per directory:

```bash
python src/treasure_hunt_agent/treasure_hunt_generator.py --branching-factor 4
```

- **Lower branching (2)**: Linear paths, fewer choices
- **Higher branching (4-5)**: Many options at each level

### File Density

Probability of creating additional clue files (0.0 to 1.0):

```bash
python src/treasure_hunt_agent/treasure_hunt_generator.py --file-density 0.5
```

- **Lower density (0.1-0.2)**: Sparse clues, minimal hints
- **Higher density (0.4-0.5)**: Many files, more red herrings

### Seed

Use a seed for reproducible generation:

```bash
python src/treasure_hunt_agent/treasure_hunt_generator.py --seed 42
```

Same seed = same treasure hunt structure every time.

### Base Path

Specify where to create the treasure hunt:

```bash
python src/treasure_hunt_agent/treasure_hunt_generator.py --base-path ./custom_hunt
```

## Difficulty Presets

Use presets for quick setup:

```bash
# Easy mode
python src/treasure_hunt_agent/treasure_hunt_generator.py --difficulty easy

# Medium mode (default)
python src/treasure_hunt_agent/treasure_hunt_generator.py --difficulty medium

# Hard mode
python src/treasure_hunt_agent/treasure_hunt_generator.py --difficulty hard
```

### Preset Details

=== "Easy"
    ```
    Depth: 4
    Branching Factor: 2
    File Density: 0.2

    Perfect for initial testing and agent development.
    ```

=== "Medium"
    ```
    Depth: 6
    Branching Factor: 3
    File Density: 0.3

    Balanced difficulty for most testing scenarios.
    ```

=== "Hard"
    ```
    Depth: 8
    Branching Factor: 4
    File Density: 0.4

    Challenging hunts for stress testing agents.
    ```

## Combining Parameters

You can override individual parameters even when using presets:

```bash
# Start with hard preset but use custom seed and depth
python src/treasure_hunt_agent/treasure_hunt_generator.py \
  --difficulty hard \
  --seed 12345 \
  --depth 10
```

## Output Structure

Each generated hunt includes:

### Configuration File

`.treasure_hunt_config.json` contains:

- `treasure_key`: Unique key to verify treasure is found
- `start_file`: Name of the starting file
- `treasure_file`: Path to treasure from root
- `path_length`: Number of steps in golden path
- `golden_path`: List of directories in correct path
- Generation parameters (depth, branching, seed)

### File Naming

All files and directories use random dictionary words to:

- Prevent agents from guessing paths
- Make hunts more realistic
- Avoid patterns that could be exploited

### Clue Format

Each clue file contains a relative path to the next location:

```
Next clue: ./subdirectory/next_clue.txt
```

The final treasure file contains:

```
TREASURE FOUND! Key: [treasure_key]
```

## Best Practices

1. **Testing**: Use seeded generation for reproducible tests
2. **Benchmarking**: Create multiple hunts with same difficulty
3. **Development**: Start with easy mode while building agents
4. **Production**: Use hard mode for final agent validation

## Troubleshooting

### Hunt Generation Fails

- Ensure you have write permissions in the base path
- Check that Python 3.13+ is installed
- Verify uv dependencies are installed

### Hunts Too Easy/Hard

- Adjust individual parameters rather than just using presets
- Increase file density for more red herrings
- Increase depth for longer paths

## Next Steps

- Learn about [running agents](running-agents.md) on generated hunts
- Explore [configuration options](configuration.md) in detail
