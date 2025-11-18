# Game Tools API

API reference for the game tools that agents use to navigate treasure hunts.

## Overview

The game tools module provides filesystem navigation and validation capabilities for agents exploring treasure hunts.

## Module: `game_tools.py`

### Tool Execution

#### `execute_tool()`

Execute a tool call and return the result.

```python
def execute_tool(
    tool_call: dict,
    current_dir: Path,
    hunt_root: Path,
    config: dict
) -> dict:
    """
    Execute an agent's tool call.

    Args:
        tool_call: Tool specification with name and parameters
        current_dir: Agent's current working directory
        hunt_root: Root of the treasure hunt
        config: Hunt configuration

    Returns:
        dict: Result with 'success', 'output', and optional 'error'

    Example:
        >>> execute_tool(
        ...     {"tool": "ls"},
        ...     Path("/hunt/dir"),
        ...     Path("/hunt"),
        ...     config
        ... )
        {'success': True, 'output': 'file1.txt\nsubdir/'}
    """
```

### Navigation Tools

#### `pwd`

Get the current working directory.

```python
def tool_pwd(current_dir: Path, hunt_root: Path) -> dict:
    """
    Return current working directory relative to hunt root.

    Args:
        current_dir: Current directory
        hunt_root: Hunt root directory

    Returns:
        dict: {'success': True, 'output': relative_path}

    Example:
        >>> tool_pwd(Path("/hunt/dir/subdir"), Path("/hunt"))
        {'success': True, 'output': '/dir/subdir'}
    """
```

**Tool Call Format:**
```json
{
    "tool": "pwd"
}
```

#### `cd`

Change the current working directory.

```python
def tool_cd(
    current_dir: Path,
    hunt_root: Path,
    path: str
) -> Tuple[dict, Path]:
    """
    Change directory to specified path.

    Args:
        current_dir: Current directory
        hunt_root: Hunt root directory
        path: Target path (relative or absolute)

    Returns:
        Tuple of (result_dict, new_directory)
        result_dict: {'success': bool, 'output': str, 'error': Optional[str]}

    Example:
        >>> tool_cd(
        ...     Path("/hunt"),
        ...     Path("/hunt"),
        ...     "./subdir"
        ... )
        ({'success': True, 'output': 'Changed to /subdir'}, Path("/hunt/subdir"))
    """
```

**Tool Call Format:**
```json
{
    "tool": "cd",
    "path": "./subdirectory"
}
```

**Path Types:**
- Relative: `./subdir`, `../parent`, `subdir/nested`
- Absolute (from hunt root): `/directory/subdirectory`

#### `ls`

List directory contents.

```python
def tool_ls(
    current_dir: Path,
    hunt_root: Path,
    path: Optional[str] = None
) -> dict:
    """
    List contents of current or specified directory.

    Args:
        current_dir: Current directory
        hunt_root: Hunt root directory
        path: Optional path to list (default: current directory)

    Returns:
        dict: {'success': bool, 'output': str, 'error': Optional[str]}
        Output format: one item per line, directories end with '/'

    Example:
        >>> tool_ls(Path("/hunt/dir"), Path("/hunt"))
        {
            'success': True,
            'output': 'clue.txt\nsubdir1/\nsubdir2/'
        }
    """
```

**Tool Call Format:**
```json
{
    "tool": "ls"
}
```

Or with path:
```json
{
    "tool": "ls",
    "path": "./subdirectory"
}
```

### Reading Tools

#### `cat`

Read file contents.

```python
def tool_cat(
    current_dir: Path,
    hunt_root: Path,
    file: str
) -> dict:
    """
    Read and return file contents.

    Args:
        current_dir: Current directory
        hunt_root: Hunt root directory
        file: File path (relative or absolute)

    Returns:
        dict: {'success': bool, 'output': str, 'error': Optional[str]}

    Example:
        >>> tool_cat(Path("/hunt"), Path("/hunt"), "clue.txt")
        {
            'success': True,
            'output': 'Next clue: ./subdir/next.txt'
        }
    """
```

**Tool Call Format:**
```json
{
    "tool": "cat",
    "file": "clue.txt"
}
```

### Completion Tools

#### `check_treasure`

Verify treasure discovery.

```python
def tool_check_treasure(
    current_dir: Path,
    hunt_root: Path,
    config: dict,
    key: str
) -> dict:
    """
    Check if agent has found the treasure.

    Args:
        current_dir: Current directory
        hunt_root: Hunt root directory
        config: Hunt configuration
        key: Treasure key provided by agent

    Returns:
        dict: {'success': bool, 'output': str, 'error': Optional[str]}
        success=True only if:
        - Agent is in correct directory
        - Treasure file exists
        - Key matches treasure_key from config

    Example:
        >>> tool_check_treasure(
        ...     Path("/hunt/final"),
        ...     Path("/hunt"),
        ...     config,
        ...     "correct_key_123"
        ... )
        {
            'success': True,
            'output': 'TREASURE FOUND! You win!'
        }
    """
```

**Tool Call Format:**
```json
{
    "tool": "check_treasure",
    "key": "treasure_key_from_file"
}
```

## Path Validation

### Security Functions

#### `is_path_safe()`

Validate that a path stays within hunt boundaries.

```python
def is_path_safe(
    base_path: Path,
    target_path: Path
) -> bool:
    """
    Check if target path is within base path.

    Args:
        base_path: Root directory boundary
        target_path: Path to validate

    Returns:
        bool: True if path is safe, False otherwise

    Example:
        >>> is_path_safe(Path("/hunt"), Path("/hunt/subdir"))
        True
        >>> is_path_safe(Path("/hunt"), Path("/etc/passwd"))
        False
    """
```

#### `resolve_path()`

Resolve a path relative to current directory.

```python
def resolve_path(
    current_dir: Path,
    hunt_root: Path,
    path: str
) -> Optional[Path]:
    """
    Resolve and validate a path.

    Args:
        current_dir: Current working directory
        hunt_root: Hunt root directory
        path: Path string to resolve

    Returns:
        Resolved Path object if valid, None if invalid

    Example:
        >>> resolve_path(
        ...     Path("/hunt/dir"),
        ...     Path("/hunt"),
        ...     "../other/file.txt"
        ... )
        Path("/hunt/other/file.txt")
    """
```

## Error Handling

### Common Error Messages

```python
# Path outside hunt boundaries
{
    'success': False,
    'error': 'Path outside treasure hunt boundaries'
}

# File not found
{
    'success': False,
    'error': 'File not found: clue.txt'
}

# Directory not found
{
    'success': False,
    'error': 'Directory not found: ./subdir'
}

# Incorrect treasure key
{
    'success': False,
    'error': 'Incorrect treasure key'
}

# Invalid tool
{
    'success': False,
    'error': 'Unknown tool: invalid_tool'
}
```

## Tool Call Format

### Standard Format

All tool calls follow this structure:

```json
{
    "tool": "tool_name",
    "param1": "value1",
    "param2": "value2"
}
```

### Tool Registry

Available tools and their parameters:

| Tool | Parameters | Description |
|------|-----------|-------------|
| `pwd` | None | Get current directory |
| `cd` | `path: str` | Change directory |
| `ls` | `path?: str` | List directory |
| `cat` | `file: str` | Read file |
| `check_treasure` | `key: str` | Verify treasure |

## Usage Examples

### Basic Navigation

```python
# Start at hunt root
result = execute_tool(
    {"tool": "pwd"},
    hunt_root,
    hunt_root,
    config
)
print(result['output'])  # "/"

# List files
result = execute_tool(
    {"tool": "ls"},
    hunt_root,
    hunt_root,
    config
)
print(result['output'])  # "start.txt\ndir1/\ndir2/"

# Read start file
result = execute_tool(
    {"tool": "cat", "file": "start.txt"},
    hunt_root,
    hunt_root,
    config
)
print(result['output'])  # "Next clue: ./dir1/clue.txt"
```

### Complete Navigation Sequence

```python
# Change to directory
result, new_dir = execute_tool(
    {"tool": "cd", "path": "./dir1"},
    hunt_root,
    hunt_root,
    config
)

# Read clue in new directory
result = execute_tool(
    {"tool": "cat", "file": "clue.txt"},
    new_dir,
    hunt_root,
    config
)

# Continue following clues...

# Finally check treasure
result = execute_tool(
    {"tool": "check_treasure", "key": "treasure_key_123"},
    final_dir,
    hunt_root,
    config
)
```

## Testing

Test the game tools:

```bash
pytest tests/test_game_tools.py -v
```

Test coverage includes:
- All tool functions
- Path validation
- Error handling
- Security boundaries

## Next Steps

- Review [Generator API](generator.md)
- Explore [Agent API](agents.md)
- Learn about [testing](../development/testing.md)
