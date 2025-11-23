# Project to create and test a simple agent loop

The aim of this project is to learn about developing with agents.

Goals:

* Learn how to set up and manage LLM agents through the Google Vertex AI API using different packages (e.g. raw API access, langchain, simonw/llm, Google ADK) to compare their use and capabilities and learn the basics of how they all work
* Create a simple first prototype of a test harness in the form of a treasure hunt on the filesystem
* Find out about creating secure dockerised environments for agents, limiting vulnerabilities

## Treasure hunt agent

* A treasure hunt module sets up a deep and convoluted file tree, with small text files at various points
* The text files give instructions to the agent about where to go next
* The agent navigates the file tree and reads files using tools and eventually finds the 'treasure' - a key word that ends the agent loop
* The agent has limited access to tools so that it can't, for example, recursively grep the whole file system
* There is a separate 'docs' directory which the agent can look in for instructions and help
* The agent uses a 'gather context' -> 'act' -> 'verify' loop. It will be able to plan, reason, call tools, and gather context. The capabilities of the agent may be too advanced for the initial simple treasure hunt system, but are designed to cope with extensions to make the treasure hunt much more challenging and require planning and problem-solving.
* The agent has limited tools to navigate, list files and read files. These are named similarly to bash commands and call a 
  subset of the functionality of those bash commands.
* The agent has tools to control the loop:
  - a tool to check a key to verify if it has reached the 'treasure'. This tool immediately ends the loop if true
  - a tool to give up and fail. This tool ends the loop
  - a tool to ask the human for help. This tool pauses the loop. The human's response is treated like a tool call.
* A setup module initialises a secure docker container with the agent and the treasure hunt, that the user can then log into to start the agent
  - the setup module checks the API key is available in either an env variable or .env file and passes it to the agent on initialisation
  - the setup module builds and runs the docker container
  - the setup module runs the treasure hunt generation module and copies the filesystem into the container
  - it doesn't leave files in the local directory. If needed it uses temp directories
* The agent module includes different implementations of the agent using:
  - langchain
  - Simon Willison's LLM package [GitHub](https://github.com/simonw/llm) [python API docs](https://llm.datasette.io/en/stable/python-api.html) 
  - Google ADK
  - raw API
* To start with, we only use Gemini models through the generative language API

## Implementation: Treasure Hunt Generator

### Design (2025-11-07)

The treasure hunt generator creates a parametrized random filesystem tree with the following features:

**Parameters:**
- `depth`: Maximum depth of the directory tree (e.g., 4-10 levels)
- `branching_factor`: Average number of subdirectories per directory (with randomization)
- `file_density`: Probability of creating text files in directories
- `seed`: Random seed for reproducibility
- `base_path`: Root directory for the treasure hunt
- `difficulty`: Preset difficulty levels (easy/medium/hard) that set sensible defaults

**Algorithm:**
1. Generate a valid "treasure path" from start → treasure
2. At each level, create the correct directory plus additional red herrings
3. Place text files with clear relative path instructions (e.g., "navigate to ../../parsnips/a/windup.txt")
4. Add dead-end paths with misleading or no clues
5. Place treasure file at the end with a unique key/password

**Properties:**
- Deterministic given a seed (for testing/reproducibility)
- Scalable to large trees (hundreds of directories)
- Clear separation between "golden path" and red herrings
- Each clue file contains only the relative path to the next step

**Files:**
- `start.txt`: Entry point with first clue
- `clue_*.txt`: Intermediate clue files
- `treasure.txt`: Final file containing the treasure key
- Optional `docs/` directory with help files for the agent

## Implementation: Agent and Game Loop

### Design Principles (2025-11-07)

**Core Philosophy:**
- The agent should have general-purpose capabilities, not be hardcoded for this specific task
- Avoid constraining the agent's actions beyond what's necessary for safety/scope
- The agent is like a human user with certain tools available - it decides how to act
- Even though this challenge could be solved deterministically, we want to explore agent behavior
- Design for future complexity - later iterations will be much more challenging

**Separation of Concerns:**
1. **Agent**: LLM client that manages conversation, generates responses, and calls tools
2. **Game**: Environment/harness that provides tools, manages state, and runs the loop

### Agent Architecture

The agent is responsible for:
- Managing conversation history/context with the LLM
- Generating text responses
- Deciding which tools to call and with what parameters
- Maintaining its own internal state (if needed)

**Key Design Points:**

1. **LLM Client Interface**
   - Start with raw Gemini API (via google-generativeai package)
   - Abstract interface that can be swapped for different implementations
   - Manages API calls, retries, rate limiting
   - Handles streaming vs non-streaming responses

2. **Context Management**
   - Maintains conversation history (user messages, assistant messages, tool calls, tool results)
   - Supports context window management (truncation, summarization if needed)
   - Tracks token usage for monitoring

3. **Tool Calling**
   - Receives tool definitions from the game
   - Uses native Gemini function calling (not custom parsing)
   - Handles tool call requests from LLM
   - Returns tool results back to LLM in next turn

4. **State**
   - Conversation history (list of messages)
   - Model configuration (temperature, max_tokens, etc.)
   - System instructions/prompt
   - Current turn number

5. **Methods/Interface**
   ```python
   class Agent:
       def __init__(self, model_name: str, system_instructions: str, tools: list[Tool])
       def step(self, game_input: str | list[ToolResult] | None = None) -> AgentResponse
       def get_history(self) -> list[Message]
       def reset(self)
   ```

   Notes on `game_input`:
   - `str`: Initial game message, user input from ask_human, or game announcements
   - `list[ToolResult]`: Results from tool calls made in previous turn
   - `None`: Continue from previous state (agent thinking/responding)

**Agent Response Format:**
```python
@dataclass
class AgentResponse:
    text: str | None  # Text response from agent
    tool_calls: list[ToolCall] | None  # Tools the agent wants to call
    finish_reason: str  # "stop", "tool_calls", "max_tokens", etc.
    usage: dict  # Token usage stats
```

**Extensibility:**
- Design to support multiple backends: raw API, langchain, llm, ADK
- Start with raw API as the baseline implementation
- Common interface so implementations can be swapped

**Design Rationale:**
The Agent class design follows common patterns from agent frameworks:
- **LangChain**: Uses `invoke()` or `run()` methods with flexible input
- **Gemini API**: Maintains chat history internally, accepts new messages/tool results
- **OpenAI Assistants**: Manages conversation threads internally

Our design has the Agent manage conversation history because:
1. Different LLM APIs have different history/message formats
2. Agent needs to manage context windows and token limits
3. Agent knows how to format tool calls/results for its specific backend
4. Game loop stays clean and doesn't need to know about API specifics

### Game Loop Architecture

The game is responsible for:
- Providing the environment (treasure hunt filesystem)
- Defining and implementing tools
- Running the agent loop
- Tracking game state and success/failure conditions
- Providing the system instructions/prompt for the agent

**Key Design Points:**

1. **Tool Definitions**

   The agent has access to these tools (following the spec):

   **Navigation/Inspection Tools:**
   - `ls(path: str = ".") -> str`: List files and directories at path
     - Supports relative paths including `../`
     - Must stay within treasure_hunt_root (validated before execution)
     - Returns formatted list similar to `ls -la`
     - Returns error message if path escapes root or doesn't exist

   - `cd(path: str) -> str`: Change current working directory
     - Supports relative paths including `../`
     - Must stay within treasure_hunt_root (validated before execution)
     - Returns current directory after change
     - Returns error message if path escapes root or doesn't exist

   - `cat(file_path: str) -> str`: Read contents of a file
     - Supports relative paths including `../`
     - Must stay within treasure_hunt_root (validated before execution)
     - Returns file contents or error message if not found/not accessible

   - `pwd() -> str`: Print current working directory
     - Returns current directory path relative to hunt root

   **Control Tools:**
   - `check_treasure(key: str) -> dict`: Check if key is correct
     - Returns {"correct": bool, "message": str}
     - If correct, ends the game with success

   - `give_up() -> dict`: End the game as failure
     - Returns {"message": "Game ended by agent"}
     - Immediately ends the loop

   - `ask_human(question: str) -> str`: Pause and ask human for help
     - Pauses the loop
     - Human response is returned as a tool result
     - Treated like any other tool call by the agent

2. **Tool Implementation**

   Each tool:
   - Has a clear JSON schema definition (for Gemini function calling)
   - Implemented as a Python function
   - Returns string or dict results
   - Handles errors gracefully (e.g., file not found)
   - Logs all calls for analysis

3. **Game State**
   ```python
   @dataclass
   class GameState:
       treasure_hunt_root: Path  # Root of treasure hunt (boundary for all operations)
       current_dir: Path  # Agent's current directory (relative to root)
       turn_number: int  # Current turn
       max_turns: int  # Maximum allowed turns
       max_tokens: int  # Maximum total tokens allowed
       tokens_used: int  # Total tokens used so far
       start_time: float  # When game started
       treasure_key: str  # The correct key
       start_file: str  # Name of the starting file
       game_over: bool  # Is game finished
       success: bool | None  # Did agent succeed (None if ongoing)
   ```

4. **The Loop**

   The game loop follows this pattern:

   ```
   1. Initialize:
      - Create/load treasure hunt (or use existing)
      - Load hunt config to get treasure_key and start_file
      - Create agent with system instructions and tools
      - Initialize game state (including treasure_hunt_root)
      - Create empty docs/ directory in hunt root

   2. Give initial context:
      - Send starting message to agent: "You are at the root of the treasure hunt.
        The starting file is {start_file}. Use your tools to find the treasure key."
      - Agent can access docs/ for any help files (currently empty)

   3. Loop (while not game_over and turn < max_turns and tokens_used < max_tokens):
      a. Agent step:
         - Call agent.step(game_input)
         - game_input is tool results from previous turn, or initial message on first turn
         - Agent returns text and/or tool calls
         - Track token usage from this step

      b. Process agent response:
         - If agent provided text (reasoning), log it
         - If agent made tool calls, process them SEQUENTIALLY:
           * Execute first tool call
           * If it's a terminating tool (check_treasure, give_up), stop processing
           * Otherwise, execute remaining tool calls in order
         - Collect all tool results

      c. Check end conditions:
         - Did agent call check_treasure with correct key? (success = True)
         - Did agent call give_up? (success = False)
         - Hit max turns? (success = False, reason: max_turns)
         - Hit max tokens? (success = False, reason: max_tokens)
         - Did agent error out? (success = False, reason: error)

      d. If not game_over:
         - Feed tool results back to agent as next game_input
         - Increment turn counter
         - Update tokens_used

   4. Finalize:
      - Record final state
      - Generate summary/report with statistics
      - Return GameResult
   ```

   **Turn Structure:**
   - Each turn allows the agent to: think/speak (text output) + make tool calls
   - Tool calls are executed SEQUENTIALLY (not in parallel)
   - All tool results are fed back together in the next turn
   - Agent can make multiple tool calls per turn, but they execute one at a time

5. **System Instructions/Prompt**

   The agent receives clear instructions:
   - Goal: Find the treasure key
   - Available tools and how to use them
   - Starting location
   - No hints about the structure (let it explore)

   Example:
   ```
   You are an agent in a treasure hunt challenge. Your goal is to find a hidden
   treasure key by navigating a filesystem and reading files.

   You have these tools available:
   - ls: List files and directories
   - cd: Change directory
   - cat: Read file contents
   - pwd: Show current location
   - check_treasure: Check if a key is correct (ends game if correct)
   - give_up: End the game as failure
   - ask_human: Ask the human operator for help

   You are currently at the root of the treasure hunt. Look around and follow
   the clues to find the treasure key. Good luck!
   ```

6. **Logging and Observability**

   Track everything for analysis:
   - All tool calls with parameters and results
   - All agent responses (text and reasoning if visible)
   - Token usage per turn
   - Time per turn
   - Final statistics (turns taken, tools used, success/failure)

7. **Game Interface**
   ```python
   class TreasureHuntGame:
       def __init__(self, hunt_path: str, agent: Agent, max_turns: int = 50)
       def run(self) -> GameResult
       def get_state(self) -> GameState
       def get_logs(self) -> list[LogEntry]
   ```

**Game Result Format:**
```python
@dataclass
class GameResult:
    success: bool
    turns_taken: int
    treasure_key_found: str | None
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_time: float
    tool_calls: list[dict]  # All tool calls made
    final_state: GameState
    end_reason: str  # "treasure_found", "gave_up", "max_turns", "max_tokens", "error"
    error: str | None  # If game ended in error
```

### Implementation Strategy

**Phase 1: Raw Gemini API Agent**
1. Implement `GeminiAgent` using `google-generativeai` package
2. Implement basic tool calling using Gemini's native function calling
3. Test with simple examples (not full treasure hunt)

**Phase 2: Game Loop**
1. Implement tool functions with safety constraints
2. Implement `TreasureHuntGame` class
3. Implement the loop logic
4. Add logging/observability

**Phase 3: Integration**
1. Wire agent and game together
2. Test with generated treasure hunts
3. Analyze agent behavior and performance
4. Iterate on system instructions and tool descriptions

**Phase 4: Extensions** (later)
- Additional agent implementations (langchain, llm, ADK)
- More sophisticated tools
- Helper/docs system
- Performance metrics and scoring
- Docker sandboxing

### Testing Strategy

**Agent Tests:**
- Mock LLM responses to test tool calling
- Test conversation history management
- Test context truncation (if implemented)
- Test error handling (API failures, rate limits)

**Game Tests:**
- Test each tool function independently
- Test tool safety constraints (can't escape hunt directory)
- Test loop termination conditions
- Test with mock agent (returns predictable tool calls)

**Integration Tests:**
- Test full game with simple, known treasure hunts
- Test success path (agent finds treasure)
- Test failure paths (give up, max turns)
- Test ask_human interaction

### Design Decisions

**Resolved design questions:**

1. **Tool Granularity**: Keep `cd` and `cat` separate (realistic shell-like interface)

2. **Path Safety**: Allow `../` relative paths, but validate all paths stay within `treasure_hunt_root` boundary

3. **Turn Structure**: Sequential tool execution - agent can request multiple tool calls per turn, but they execute one at a time in order

4. **Initial Context**: Tell the agent the start file name in the initial message

5. **Docs Directory**: Create empty `docs/` directory in phase 1 (can add help files later)

6. **Error Handling**: Return error messages that the agent can use to correct its behavior

7. **Streaming**: Batch responses only for now (streaming can be added later)

8. **Cost Management**: Implement both turn limits and token limits with tracking

9. **Agent Interface**: Use `game_input` (not `user_message`) to accept various input types: initial messages, tool results, user responses

