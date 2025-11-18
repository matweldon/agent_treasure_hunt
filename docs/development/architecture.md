# Architecture

Overview of Treasure Hunt Agent's architecture, design decisions, and implementation details.

## System Overview

Treasure Hunt Agent consists of three main components that work together to create and solve filesystem-based puzzles.

```
┌─────────────────────────────────────────────────────────────┐
│                     Treasure Hunt System                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Generator  │─────▶│  Game Loop   │◀────▶│   Agent   │ │
│  │              │      │              │      │           │ │
│  │ Creates hunt │      │ Manages game │      │ Solves    │ │
│  │ filesystem   │      │ executes     │      │ using LLM │ │
│  │              │      │ tools        │      │           │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│                              │                               │
│                              ▼                               │
│                        ┌──────────┐                          │
│                        │   Tools  │                          │
│                        │          │                          │
│                        │ pwd, cd, │                          │
│                        │ ls, cat  │                          │
│                        └──────────┘                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Treasure Hunt Generator

**Purpose**: Create parametrized filesystem puzzles

**Location**: `src/treasure_hunt_agent/treasure_hunt_generator.py`

**Key Responsibilities**:
- Generate directory tree structures
- Create golden path (solution route)
- Place clue files with navigation hints
- Add red herrings (dead ends)
- Generate configuration file

**Design Decisions**:

- **Random word naming**: Uses dictionary words to prevent pattern exploitation
- **Seeded generation**: Reproducible for testing and benchmarking
- **Parametrized difficulty**: Configurable depth, branching, file density
- **JSON configuration**: Stores metadata for validation

**Data Flow**:

```python
Parameters → Directory Tree → Golden Path → Clue Files → Config
    ↓             ↓              ↓             ↓           ↓
  depth,      create dirs    select path   place hints   metadata
branching,      random        through        relative      JSON
density       naming          tree           paths
```

### 2. Game Loop

**Purpose**: Manage agent execution and tool calls

**Location**: `src/treasure_hunt_agent/treasure_hunt_game.py`

**Key Responsibilities**:
- Initialize game state
- Process agent responses
- Execute tool calls
- Validate paths and permissions
- Track statistics (turns, time, tokens)
- Determine win/loss conditions

**Design Decisions**:

- **Turn-based execution**: One agent action per turn
- **Path validation**: Ensures agent stays within boundaries
- **Timeout support**: Prevents infinite loops
- **Detailed logging**: Tracks all actions for debugging
- **Statistics collection**: Metrics for performance analysis

**Game Loop Flow**:

```python
Initialize
    ↓
┌─────────────────┐
│  Start Turn     │
│   ├─ Get agent  │
│   │   response  │
│   ├─ Parse      │
│   │   tools     │
│   ├─ Execute    │
│   │   tools     │
│   ├─ Check      │
│   │   treasure  │
│   └─ Update     │
│       state     │
└─────────────────┘
    ↓
  Done? ─No─┐
    │       │
   Yes      │
    ↓       │
 Results  ──┘
```

### 3. Agent

**Purpose**: Use LLM to navigate and solve treasure hunts

**Location**: `src/treasure_hunt_agent/gemini_agent.py`

**Key Responsibilities**:
- Manage conversation history
- Generate responses with tool calls
- Track token usage
- Interact with LLM API

**Design Decisions**:

- **Conversation context**: Maintains full history for coherent decisions
- **Tool-calling pattern**: Uses structured function calling
- **Token tracking**: Monitors API usage
- **Abstracted interface**: Easy to implement other LLM backends

**Agent Decision Flow**:

```python
Receive game state
    ↓
Update conversation history
    ↓
Generate prompt
    ↓
Call LLM API
    ↓
Parse response
    ↓
Extract tool calls
    ↓
Return to game loop
```

### 4. Game Tools

**Purpose**: Provide filesystem navigation capabilities

**Location**: `src/treasure_hunt_agent/game_tools.py`

**Available Tools**:

| Tool | Purpose | Security |
|------|---------|----------|
| `pwd` | Get current directory | Read-only |
| `cd` | Change directory | Path validation |
| `ls` | List contents | Read-only |
| `cat` | Read file | Path validation |
| `check_treasure` | Verify win | Key validation |

**Design Decisions**:

- **Path sandboxing**: Prevents directory traversal attacks
- **Relative paths**: All paths relative to hunt root
- **Clear errors**: Helpful messages for debugging
- **Stateless tools**: No side effects except `cd`

## Data Models

### Hunt Configuration

```python
{
    "treasure_key": str,       # Unique verification key
    "start_file": str,         # Starting clue filename
    "treasure_file": str,      # Path to treasure
    "path_length": int,        # Solution depth
    "golden_path": List[str],  # Solution directories
    "depth": int,              # Max tree depth
    "branching_factor": int,   # Avg subdirs
    "file_density": float,     # Clue probability
    "seed": Optional[int],     # Random seed
    "generated_at": str        # ISO timestamp
}
```

### Tool Call Format

```python
{
    "tool": str,          # Tool name
    **kwargs             # Tool-specific parameters
}
```

### Tool Result Format

```python
{
    "success": bool,      # Success status
    "output": str,        # Tool output
    "error": Optional[str] # Error message if failed
}
```

### Game Results

```python
{
    "success": bool,           # Treasure found?
    "turns": int,             # Number of turns
    "time": float,            # Total time (seconds)
    "tool_calls": dict,       # Tool usage counts
    "token_usage": dict,      # Token statistics
    "final_state": str        # End condition
}
```

## Security Considerations

### Path Traversal Prevention

```python
def is_path_safe(hunt_root: Path, target: Path) -> bool:
    """Ensure path stays within hunt boundaries."""
    abs_target = target.resolve()
    abs_root = hunt_root.resolve()
    return abs_target.is_relative_to(abs_root)
```

### Validation Layers

1. **Input validation**: Check tool parameters
2. **Path resolution**: Resolve symlinks and relative paths
3. **Boundary check**: Ensure path within hunt
4. **File existence**: Verify file/directory exists
5. **Permission check**: Ensure read access

### No Code Execution

- Tools are limited to filesystem operations
- No shell command execution
- No arbitrary file writes
- No network access

## Extensibility Points

### Adding New Tools

```python
def tool_new_command(
    current_dir: Path,
    hunt_root: Path,
    **kwargs
) -> dict:
    """
    New tool implementation.

    Args:
        current_dir: Current directory
        hunt_root: Hunt root
        **kwargs: Tool-specific parameters

    Returns:
        Tool result dictionary
    """
    # Validate inputs
    # Execute tool logic
    # Return result
```

Register in tool registry:

```python
TOOLS = {
    "pwd": tool_pwd,
    "cd": tool_cd,
    "ls": tool_ls,
    "cat": tool_cat,
    "check_treasure": tool_check_treasure,
    "new_command": tool_new_command,  # Add here
}
```

### Adding New Agents

Implement the agent interface:

```python
class NewAgent:
    def generate_response(self, messages: List[dict]) -> dict:
        """Generate response with tool calls."""
        pass

    def add_to_history(self, role: str, content: str) -> None:
        """Add to conversation history."""
        pass

    def get_token_usage(self) -> dict:
        """Return token statistics."""
        pass

    def get_tool_stats(self) -> dict:
        """Return tool usage statistics."""
        pass
```

### Custom Difficulty Presets

```python
DIFFICULTY_PRESETS = {
    "easy": {"depth": 4, "branching_factor": 2, "file_density": 0.2},
    "medium": {"depth": 6, "branching_factor": 3, "file_density": 0.3},
    "hard": {"depth": 8, "branching_factor": 4, "file_density": 0.4},
    "expert": {"depth": 10, "branching_factor": 5, "file_density": 0.5},  # New
}
```

## Performance Considerations

### Generator Performance

- **Time complexity**: O(b^d) where b=branching factor, d=depth
- **Space complexity**: O(b^d) for directory storage
- **Optimization**: Early termination for golden path

### Game Loop Performance

- **Per turn**: O(1) for tool execution
- **Total**: O(n) where n=number of turns
- **Bottleneck**: LLM API latency

### Agent Performance

- **Token usage**: Grows with conversation history
- **Optimization strategies**:
  - Summarize old messages
  - Limit context window
  - Use efficient prompts

## Testing Strategy

### Unit Tests

- Individual functions in isolation
- Mock external dependencies
- Fast execution (<100ms per test)

### Integration Tests

- Components working together
- Real filesystem operations
- Full hunt generation and solving

### End-to-End Tests

- Complete system workflow
- Real LLM API calls (optional)
- Performance benchmarking

## Future Enhancements

### Planned Features

- **Docker sandboxing**: Isolated agent execution
- **Multi-agent support**: Compare agent strategies
- **Web interface**: Browser-based visualization
- **Metrics dashboard**: Performance analytics

### Architectural Improvements

- **Plugin system**: Dynamic tool loading
- **Event system**: Hooks for monitoring
- **Async support**: Concurrent agent execution
- **Streaming responses**: Real-time output

## Dependency Management

### Core Dependencies

- `google-generativeai`: Gemini API client
- `pathlib`: Filesystem operations
- `json`: Configuration serialization

### Development Dependencies

- `pytest`: Testing framework
- `black`: Code formatting
- `mypy`: Type checking
- `mkdocs`: Documentation

### Dependency Principles

- Minimal core dependencies
- Optional extras for specific features
- Regular updates for security
- Version pinning for reproducibility

## Next Steps

- Review [API reference](../api/generator.md)
- Explore [testing strategies](testing.md)
- Check [contributing guidelines](contributing.md)
