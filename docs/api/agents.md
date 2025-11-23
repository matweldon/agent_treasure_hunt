# Agents API

API reference for agent implementations that solve treasure hunts.

## Overview

Agents are LLM-powered or scripted entities that navigate treasure hunts using available tools.

## Module: `gemini_agent.py`

### GeminiAgent Class

LLM-powered agent using Google's Gemini API.

```python
class GeminiAgent:
    """
    Agent that uses Gemini API for treasure hunt navigation.

    Attributes:
        model: Gemini model instance
        conversation_history: List of message dictionaries
        tool_calls_made: Counter of tool usage
        token_usage: Dictionary tracking token consumption
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-1.5-pro"
    ):
        """
        Initialize Gemini agent.

        Args:
            api_key: Google AI API key
            model_name: Gemini model identifier

        Example:
            >>> agent = GeminiAgent(api_key="your-key-here")
        """
```

### Methods

#### `generate_response()`

Generate a response with tool calls.

```python
def generate_response(self, messages: List[dict]) -> dict:
    """
    Generate response from conversation history.

    Args:
        messages: List of conversation messages

    Returns:
        dict: Response with text and tool_calls

    Example:
        >>> response = agent.generate_response([
        ...     {"role": "user", "content": "Find the treasure"}
        ... ])
        >>> print(response['tool_calls'])
        [{'tool': 'pwd'}]
    """
```

#### `add_to_history()`

Add a message to conversation history.

```python
def add_to_history(self, role: str, content: str) -> None:
    """
    Append message to conversation history.

    Args:
        role: Message role ('user', 'assistant', 'tool')
        content: Message content

    Example:
        >>> agent.add_to_history("user", "List the current directory")
        >>> agent.add_to_history("assistant", "I'll use ls")
    """
```

#### `get_token_usage()`

Get current token usage statistics.

```python
def get_token_usage(self) -> dict:
    """
    Return token usage statistics.

    Returns:
        dict: Token counts by type

    Example:
        >>> usage = agent.get_token_usage()
        >>> print(usage)
        {
            'prompt_tokens': 1234,
            'response_tokens': 567,
            'total_tokens': 1801
        }
    """
```

#### `get_tool_stats()`

Get tool usage statistics.

```python
def get_tool_stats(self) -> dict:
    """
    Return count of each tool used.

    Returns:
        dict: Tool names to usage counts

    Example:
        >>> stats = agent.get_tool_stats()
        >>> print(stats)
        {
            'pwd': 5,
            'cd': 8,
            'ls': 12,
            'cat': 10,
            'check_treasure': 1
        }
    """
```

## Module: `example_agent.py`

### ExampleAgent Class

Simple scripted agent for demonstration.

```python
class ExampleAgent:
    """
    Basic agent that follows a simple strategy.

    Demonstrates:
    - Reading clues
    - Following paths
    - Basic navigation
    """

    def __init__(self):
        """Initialize example agent."""
```

### Methods

#### `solve()`

Execute the treasure hunt solution strategy.

```python
def solve(self, hunt_path: Path, config: dict) -> bool:
    """
    Attempt to solve the treasure hunt.

    Args:
        hunt_path: Root directory of hunt
        config: Hunt configuration

    Returns:
        bool: True if treasure found, False otherwise

    Example:
        >>> agent = ExampleAgent()
        >>> success = agent.solve(Path("./hunt"), config)
        >>> print(f"Success: {success}")
    """
```

## Module: `treasure_hunt_game.py`

### TreasureHuntGame Class

Game loop that runs agents through treasure hunts.

```python
class TreasureHuntGame:
    """
    Game loop for running agents on treasure hunts.

    Handles:
    - Turn management
    - Tool execution
    - Result tracking
    - Time limits
    """

    def __init__(
        self,
        agent,
        hunt_path: Path,
        config: dict,
        max_turns: int = 50,
        timeout_per_turn: int = 300
    ):
        """
        Initialize game instance.

        Args:
            agent: Agent instance with generate_response method
            hunt_path: Root directory of treasure hunt
            config: Hunt configuration
            max_turns: Maximum agent turns
            timeout_per_turn: Timeout in seconds per turn

        Example:
            >>> game = TreasureHuntGame(
            ...     agent=my_agent,
            ...     hunt_path=Path("./hunt"),
            ...     config=config,
            ...     max_turns=30
            ... )
        """
```

### Methods

#### `run()`

Execute the game loop.

```python
def run(self) -> dict:
    """
    Run the treasure hunt game.

    Returns:
        dict: Game results with statistics

    Example:
        >>> results = game.run()
        >>> print(results)
        {
            'success': True,
            'turns': 15,
            'time': 45.3,
            'tool_calls': {...},
            'token_usage': {...}
        }
    """
```

#### `execute_turn()`

Execute a single agent turn.

```python
def execute_turn(self, turn_number: int) -> Tuple[bool, bool]:
    """
    Execute one turn of agent action.

    Args:
        turn_number: Current turn count

    Returns:
        Tuple of (continue_game, treasure_found)

    Example:
        >>> continue_game, found = game.execute_turn(1)
        >>> if found:
        ...     print("Treasure found!")
    """
```

#### `get_results()`

Get current game state and statistics.

```python
def get_results(self) -> dict:
    """
    Return game statistics and results.

    Returns:
        dict: Complete game results

    Example:
        >>> results = game.get_results()
        >>> print(f"Turns: {results['turns']}")
        >>> print(f"Success: {results['success']}")
    """
```

## Agent Interface

### Required Methods

Custom agents must implement:

```python
class CustomAgent:
    def generate_response(self, messages: List[dict]) -> dict:
        """
        Generate response from conversation.

        Args:
            messages: Conversation history

        Returns:
            dict with 'text' and 'tool_calls' keys
        """
        pass

    def add_to_history(self, role: str, content: str) -> None:
        """Add message to conversation history."""
        pass

    def get_token_usage(self) -> dict:
        """Return token usage statistics (optional)."""
        return {}

    def get_tool_stats(self) -> dict:
        """Return tool usage statistics (optional)."""
        return {}
```

### Response Format

Agent responses must follow this format:

```python
{
    "text": "I'll list the current directory",
    "tool_calls": [
        {
            "tool": "ls"
        }
    ]
}
```

Multiple tool calls:

```python
{
    "text": "Let me check where I am and list files",
    "tool_calls": [
        {"tool": "pwd"},
        {"tool": "ls"}
    ]
}
```

## Configuration

### Agent Settings

```python
# Gemini configuration
GEMINI_CONFIG = {
    "model_name": "gemini-1.5-pro",
    "temperature": 0.7,
    "max_output_tokens": 8192,
    "top_p": 0.95
}

# Game settings
GAME_CONFIG = {
    "max_turns": 50,
    "timeout_per_turn": 300,
    "verbose": True
}
```

### Environment Variables

```python
import os

api_key = os.getenv("GOOGLE_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
```

## Usage Examples

### Running Gemini Agent

```python
from treasure_hunt_agent.gemini_agent import GeminiAgent
from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame
from pathlib import Path
import json

# Load configuration
with open("treasure_hunt/.treasure_hunt_config.json") as f:
    config = json.load(f)

# Create agent
agent = GeminiAgent(api_key="your-key")

# Create game
game = TreasureHuntGame(
    agent=agent,
    hunt_path=Path("treasure_hunt"),
    config=config,
    max_turns=30
)

# Run game
results = game.run()

# Display results
print(f"Success: {results['success']}")
print(f"Turns: {results['turns']}")
print(f"Tokens: {results['token_usage']['total_tokens']}")
```

### Creating Custom Agent

```python
class MyCustomAgent:
    def __init__(self):
        self.history = []

    def generate_response(self, messages):
        # Your custom logic here
        return {
            "text": "Following the clue",
            "tool_calls": [
                {"tool": "cat", "file": "clue.txt"}
            ]
        }

    def add_to_history(self, role, content):
        self.history.append({"role": role, "content": content})

# Use custom agent
agent = MyCustomAgent()
game = TreasureHuntGame(agent, hunt_path, config)
results = game.run()
```

## Error Handling

### Common Errors

```python
# API key not set
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

# Invalid tool call
if "tool" not in tool_call:
    raise ValueError("Tool call missing 'tool' field")

# Timeout exceeded
if time.time() - start_time > timeout:
    raise TimeoutError("Turn exceeded timeout limit")
```

## Performance Metrics

### Tracking Metrics

```python
# Token efficiency
tokens_per_turn = total_tokens / turns

# Tool efficiency
tool_calls_per_turn = sum(tool_calls.values()) / turns

# Success rate
success_rate = successful_hunts / total_hunts
```

## Testing

Test agent implementations:

```bash
pytest tests/test_gemini_agent.py -v
pytest tests/test_treasure_hunt_game.py -v
```

## Next Steps

- Review [Generator API](generator.md)
- Explore [Game Tools API](game-tools.md)
- Learn about [testing strategies](../development/testing.md)
