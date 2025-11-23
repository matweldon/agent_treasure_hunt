# Running Agents

Learn how to run agents on treasure hunts, understand available tools, and interpret results.

## Available Tools

Agents have access to the following tools to navigate and solve treasure hunts:

### Navigation Tools

#### `pwd`
Get the current working directory.

```python
{"tool": "pwd"}
```

Returns the absolute path within the treasure hunt.

#### `cd`
Change directory to navigate the filesystem.

```python
{"tool": "cd", "path": "directory_name"}
```

- Accepts relative paths: `./subdir` or `../parent`
- Absolute paths from hunt root: `/directory/subdirectory`
- Path validation ensures agent stays within hunt boundaries

#### `ls`
List contents of the current or specified directory.

```python
{"tool": "ls"}
{"tool": "ls", "path": "./subdirectory"}
```

Shows files and directories available at that location.

### Reading Tools

#### `cat`
Read the contents of a file.

```python
{"tool": "cat", "file": "clue.txt"}
```

Returns the full content of the file, including clues to the next location.

### Completion Tools

#### `check_treasure`
Verify if the treasure has been found.

```python
{"tool": "check_treasure", "key": "treasure_key_value"}
```

Returns success if:
- Agent is in the correct directory
- The treasure file exists
- The provided key matches the treasure key

## Running the Example Agent

The example agent demonstrates basic navigation:

```bash
python src/treasure_hunt_agent/example_agent.py --hunt-path ./treasure_hunt
```

This is a simple scripted agent that shows how to use the tools.

## Running the Gemini Agent

The Gemini agent uses Google's Gemini API for intelligent navigation:

```bash
export GOOGLE_API_KEY='your-api-key-here'
python examples/run_treasure_hunt.py
```

### Command-Line Options

```bash
python examples/run_treasure_hunt.py \
  --difficulty medium \     # Hunt difficulty
  --seed 123 \             # Random seed
  --max-turns 30 \         # Maximum agent turns
  --keep-hunt              # Don't delete hunt after
```

## Understanding Results

After a run completes, you'll see:

### Success Metrics

```
=== TREASURE HUNT COMPLETE ===
Status: SUCCESS
Turns: 15
Total Tokens: 12,450
  - Prompt: 8,200
  - Response: 4,250
Time: 45.3s
```

### Failure Information

```
=== TREASURE HUNT COMPLETE ===
Status: FAILED
Turns: 30 (max reached)
Reason: Agent exceeded maximum turns
```

### Tool Usage Statistics

The output includes:
- Number of each tool call made
- Token usage breakdown
- Time per turn
- Path taken through the hunt

## Creating Your Own Agent

To create a custom agent, implement the agent interface:

```python
class MyCustomAgent:
    def __init__(self):
        self.conversation_history = []

    def generate_response(self, messages):
        # Process messages
        # Generate tool calls
        # Return response with tool calls
        pass

    def add_to_history(self, role, content):
        self.conversation_history.append({
            "role": role,
            "content": content
        })
```

Key requirements:

1. **Tool Calling**: Return tool calls in the expected format
2. **Context Management**: Track conversation history
3. **Error Handling**: Handle tool errors gracefully

## Agent Strategies

### Efficient Navigation

Good agents typically:

1. Start with `pwd` to understand current location
2. Use `ls` to see available options
3. Read files with `cat` to get clues
4. Follow clue paths using `cd`
5. Verify with `check_treasure` when treasure is found

### Common Pitfalls

Avoid these mistakes:

- **Random exploration**: Always read clues first
- **Ignoring paths**: Clues contain the correct path
- **Excessive tool calls**: Plan before acting
- **Path errors**: Validate paths are within hunt boundaries

## Debugging Agent Behavior

### Verbose Mode

Enable detailed logging to see each tool call:

```python
# In your agent code
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Save Conversation History

Keep the hunt directory to review:

```bash
python examples/run_treasure_hunt.py --keep-hunt
```

Then examine:
- Treasure hunt structure
- Configuration file
- Paths taken

## Performance Optimization

### Reducing Token Usage

- Use concise prompts
- Limit conversation history
- Summarize previous actions

### Reducing Turn Count

- Read and follow clues carefully
- Avoid backtracking
- Plan multiple steps ahead

## Next Steps

- Understand [configuration options](configuration.md)
- Review [API reference](../api/agents.md) for implementation details
- Check out [testing strategies](../development/testing.md)
