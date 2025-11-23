# Treasure Hunt Generator API

API reference for the treasure hunt generation module.

## Overview

The treasure hunt generator creates filesystem-based puzzles with configurable difficulty and structure.

## Module: `treasure_hunt_generator.py`

### Main Function

#### `generate_treasure_hunt()`

Generate a complete treasure hunt with specified parameters.

```python
def generate_treasure_hunt(
    base_path: str = "./treasure_hunt",
    depth: int = 6,
    branching_factor: int = 3,
    file_density: float = 0.3,
    seed: Optional[int] = None,
    difficulty: Optional[str] = None
) -> dict:
    """
    Generate a treasure hunt filesystem puzzle.

    Args:
        base_path: Root directory for the treasure hunt
        depth: Maximum depth of directory tree
        branching_factor: Average number of subdirectories per directory
        file_density: Probability (0-1) of creating clue files
        seed: Random seed for reproducible generation
        difficulty: Preset difficulty ('easy', 'medium', 'hard')

    Returns:
        dict: Configuration dictionary with hunt metadata

    Raises:
        ValueError: If parameters are invalid
        OSError: If directory creation fails
    """
```

**Example:**

```python
from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt

# Generate with default settings
config = generate_treasure_hunt()

# Generate with custom parameters
config = generate_treasure_hunt(
    base_path="./my_hunt",
    depth=8,
    branching_factor=4,
    seed=42
)

# Use difficulty preset
config = generate_treasure_hunt(
    difficulty="hard",
    seed=12345
)
```

### Helper Functions

#### `create_directory_tree()`

Create the directory structure for the hunt.

```python
def create_directory_tree(
    root: Path,
    depth: int,
    branching_factor: int,
    rng: random.Random
) -> List[Path]:
    """
    Create a tree of directories.

    Args:
        root: Root directory path
        depth: Maximum depth
        branching_factor: Average subdirectories per level
        rng: Random number generator

    Returns:
        List of all created directory paths
    """
```

#### `create_golden_path()`

Generate the solution path through the hunt.

```python
def create_golden_path(
    directories: List[Path],
    depth: int,
    rng: random.Random
) -> List[Path]:
    """
    Create a path from root to treasure location.

    Args:
        directories: All available directories
        depth: Target path depth
        rng: Random number generator

    Returns:
        Ordered list of directories forming the path
    """
```

#### `place_clues()`

Place clue files along the golden path.

```python
def place_clues(
    golden_path: List[Path],
    file_density: float,
    rng: random.Random
) -> List[Path]:
    """
    Place clue files with navigation hints.

    Args:
        golden_path: Path directories
        file_density: Probability of additional clue files
        rng: Random number generator

    Returns:
        List of created clue file paths
    """
```

#### `generate_treasure_key()`

Generate a unique treasure verification key.

```python
def generate_treasure_key(length: int = 16) -> str:
    """
    Generate a random treasure key.

    Args:
        length: Length of the key

    Returns:
        Random alphanumeric string
    """
```

## Configuration Schema

### Hunt Configuration

The generated configuration follows this schema:

```python
{
    "treasure_key": str,        # Unique verification key
    "start_file": str,          # Starting clue filename
    "treasure_file": str,       # Relative path to treasure
    "path_length": int,         # Steps in golden path
    "golden_path": List[str],   # Directory names in order
    "depth": int,               # Maximum tree depth
    "branching_factor": int,    # Average subdirectories
    "file_density": float,      # Clue file probability
    "seed": Optional[int],      # Random seed
    "generated_at": str         # ISO timestamp
}
```

## Difficulty Presets

### Preset Definitions

```python
DIFFICULTY_PRESETS = {
    "easy": {
        "depth": 4,
        "branching_factor": 2,
        "file_density": 0.2
    },
    "medium": {
        "depth": 6,
        "branching_factor": 3,
        "file_density": 0.3
    },
    "hard": {
        "depth": 8,
        "branching_factor": 4,
        "file_density": 0.4
    }
}
```

## Word Dictionary

### Random Naming

The generator uses a dictionary of common English words for naming:

```python
def get_random_word(rng: random.Random) -> str:
    """
    Get a random word from the dictionary.

    Args:
        rng: Random number generator

    Returns:
        Random word string
    """
```

Words are selected to:
- Avoid patterns agents could exploit
- Ensure unique naming
- Provide realistic filenames

## File Formats

### Clue File Format

```
Next clue: ./relative/path/to/next_clue.txt
```

### Treasure File Format

```
TREASURE FOUND! Key: [treasure_key]
```

### Configuration File Format

JSON format with hunt metadata (see Configuration Schema above).

## Error Handling

### Common Exceptions

```python
# Invalid parameters
if depth < 1:
    raise ValueError("Depth must be at least 1")

# Path already exists
if base_path.exists():
    raise OSError(f"Path {base_path} already exists")

# Invalid difficulty
if difficulty not in DIFFICULTY_PRESETS:
    raise ValueError(f"Unknown difficulty: {difficulty}")
```

## Usage Examples

### Basic Generation

```python
# Simple generation
config = generate_treasure_hunt()
print(f"Treasure hunt created at: {config['base_path']}")
print(f"Start file: {config['start_file']}")
```

### Reproducible Tests

```python
# Use seed for reproducible tests
config1 = generate_treasure_hunt(seed=42)
config2 = generate_treasure_hunt(seed=42)
assert config1['golden_path'] == config2['golden_path']
```

### Custom Difficulty

```python
# Create very challenging hunt
config = generate_treasure_hunt(
    depth=10,
    branching_factor=5,
    file_density=0.5,
    seed=12345
)
```

## Testing

The generator includes comprehensive tests:

```bash
pytest tests/test_treasure_hunt_generator.py -v
```

Test coverage includes:
- Parameter validation
- Reproducible generation
- Difficulty presets
- Path creation
- File generation

## Next Steps

- Explore [Game Tools API](game-tools.md)
- Learn about [Agent API](agents.md)
- Review [testing strategies](../development/testing.md)
