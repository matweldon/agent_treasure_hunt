# Configuration

Comprehensive guide to configuring treasure hunts and agents.

## Treasure Hunt Configuration

### Configuration File Format

Each generated hunt includes `.treasure_hunt_config.json`:

```json
{
  "treasure_key": "randomkey123",
  "start_file": "beginning.txt",
  "treasure_file": "mystery/wonder/treasure.txt",
  "path_length": 5,
  "golden_path": [
    "mystery",
    "wonder",
    "secret",
    "hidden",
    "final"
  ],
  "depth": 6,
  "branching_factor": 3,
  "file_density": 0.3,
  "seed": 42,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### Configuration Fields

#### `treasure_key`
Unique identifier for verifying treasure discovery.

- Auto-generated random string
- Required for `check_treasure` tool
- Stored in treasure file

#### `start_file`
Name of the starting clue file.

- Located in hunt root directory
- Contains first clue
- Random word from dictionary

#### `treasure_file`
Relative path to treasure from hunt root.

- Full path through golden path
- Used for validation
- Contains treasure key

#### `path_length`
Number of steps in the golden path.

- Excludes start file
- Minimum: 2
- Affected by depth parameter

#### `golden_path`
Ordered list of directories in correct solution.

- Used for validation
- Can be analyzed for hunt difficulty
- Helps in debugging agent behavior

#### Generation Parameters

- `depth`: Maximum directory depth
- `branching_factor`: Average subdirectories
- `file_density`: Clue file probability
- `seed`: Random seed for reproducibility

## Agent Configuration

### Gemini Agent Settings

Configure the Gemini agent with environment variables:

```bash
# Required
export GOOGLE_API_KEY='your-api-key-here'

# Optional
export GEMINI_MODEL='gemini-1.5-pro'  # Default model
export MAX_TOKENS=8192                 # Max response tokens
export TEMPERATURE=0.7                 # Sampling temperature
```

### Game Loop Settings

Configure via command-line arguments:

```bash
python examples/run_treasure_hunt.py \
  --max-turns 50 \         # Maximum agent turns (default: 50)
  --timeout 300 \          # Timeout per turn in seconds (default: 300)
  --keep-hunt              # Preserve hunt directory
```

## Performance Tuning

### Token Limits

Control token usage:

```python
generation_config = {
    "max_output_tokens": 8192,
    "temperature": 0.7,
    "top_p": 0.95,
}
```

### Turn Limits

Balance between:
- **Too low**: Agent may not complete hard hunts
- **Too high**: Inefficient agents take too long

Recommended limits by difficulty:

| Difficulty | Recommended Max Turns |
|-----------|----------------------|
| Easy      | 20                   |
| Medium    | 30                   |
| Hard      | 50                   |

## Path Validation

### Boundary Enforcement

The game loop enforces:

1. **Path boundaries**: Agents cannot escape hunt directory
2. **File access**: Only files within hunt are accessible
3. **Directory traversal**: Validates all paths

### Security Considerations

Built-in protections:

- Path normalization
- Symlink resolution
- Parent directory limits

Example validation:

```python
def is_valid_path(hunt_root, requested_path):
    abs_path = os.path.abspath(requested_path)
    return abs_path.startswith(hunt_root)
```

## Logging and Debugging

### Enable Detailed Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Log Categories

- `treasure_hunt.generator`: Hunt generation events
- `treasure_hunt.game`: Game loop and tool execution
- `treasure_hunt.agent`: Agent decisions and responses

### Output Verbosity

Control output detail:

```bash
# Quiet mode (only final results)
python examples/run_treasure_hunt.py --quiet

# Verbose mode (all tool calls)
python examples/run_treasure_hunt.py --verbose

# Debug mode (everything)
python examples/run_treasure_hunt.py --debug
```

## Environment Variables Reference

### Required

```bash
GOOGLE_API_KEY=your-api-key-here
```

### Optional

```bash
# Model Configuration
GEMINI_MODEL=gemini-1.5-pro
MAX_TOKENS=8192
TEMPERATURE=0.7

# Logging
LOG_LEVEL=INFO
LOG_FILE=/path/to/logfile.log

# Game Settings
DEFAULT_MAX_TURNS=50
DEFAULT_TIMEOUT=300
```

## Advanced Configuration

### Custom Tool Sets

Define which tools are available to agents:

```python
AVAILABLE_TOOLS = [
    "pwd",
    "cd",
    "ls",
    "cat",
    "check_treasure"
]

# Restrictive mode (no ls)
RESTRICTIVE_TOOLS = [
    "pwd",
    "cd",
    "cat",
    "check_treasure"
]
```

### Hunt Validation Rules

Customize validation:

```python
VALIDATION_CONFIG = {
    "require_golden_path": True,
    "min_path_length": 3,
    "max_path_length": 10,
    "allow_loops": False,
    "require_clue_files": True
}
```

## Best Practices

1. **Reproducibility**: Always use seeds for testing
2. **Resource Limits**: Set appropriate token and turn limits
3. **Logging**: Enable detailed logs for debugging
4. **Validation**: Test configuration changes with easy hunts first
5. **Documentation**: Document custom configurations

## Troubleshooting

### Agent Times Out

- Increase `--timeout` value
- Check network connectivity for API calls
- Review agent logic for infinite loops

### Hunt Generation Fails

- Verify write permissions
- Check parameter combinations are valid
- Ensure sufficient disk space

### Unexpected Agent Behavior

- Review logged tool calls
- Check conversation history
- Validate hunt structure matches config

## Next Steps

- Explore [API reference](../api/generator.md) for programmatic control
- Learn about [testing strategies](../development/testing.md)
- Review [architecture details](../development/architecture.md)
