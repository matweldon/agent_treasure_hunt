# Blog Post Research: Claude Code Treasure Hunt Project

## Executive Summary

This was a long, productive pair programming session where you and Claude built a complete AI agent testing system from scratch. The session demonstrated:

- **Spec-driven development** with iterative design discussions
- **Test-Driven Development (TDD)** with 43 passing tests
- **Pragmatic problem-solving** when strict TDD became too complex
- **Collaborative design** with Claude proposing architectures and you providing key decisions
- **The joy of "Go chief"** - giving Claude autonomy to execute

**Total conversation**: 455 messages (205 from you, 250 from Claude)
**Tool usage**: 90 Bash commands, 48 file edits, 13 file reads, 11 file writes
**Final system**: 1,000+ lines of Python code with full test coverage

---

## The Project: AI Treasure Hunt

You built a system to test AI agents using a "treasure hunt" puzzle:

1. **Generator**: Creates complex filesystem mazes with clues hidden in text files
2. **Agent**: A Gemini-powered AI that navigates using tools (ls, cd, cat, etc.)
3. **Game Loop**: Manages the agent's turns, validates paths, tracks tokens/time

**Key Innovation**: Random word-based filenames prevent agents from "cheating" by pattern-matching common names like "treasure.txt"

---

## Session Timeline & Flow

### Phase 1: Setup & Spec Review
- You asked Claude to read the workflow guidelines (CLAUDE.md)
- Shared the comprehensive treasure hunt spec you'd written
- Claude proposed starting with the generator → agent → Docker sandboxing

### Phase 2: Building the Generator (TDD)
- Claude wrote tests first, then implemented the recursive tree-building algorithm
- **Key moment**: You suggested using dictionary words instead of "clue_*.txt" to prevent cheating
- Claude: "Good point! Using predictable names... would make it too easy for an agent to cheat"
- Result: 9 passing tests, parametrized generation with difficulty presets

### Phase 3: Design Discussion - Agent & Game Loop
- Claude wrote a detailed architecture spec and asked clarifying questions
- **Your design decisions**:
  - Keep tools separate (cd, cat, ls as distinct commands)
  - Allow `../` paths but validate boundaries
  - Sequential tool execution (not parallel)
  - Use abstract `game_input` instead of `user_message`
  - Implement both turn limits and token limits

### Phase 4: The "Go Chief" Moment
After the design was complete, you said two magic words:

> **You**: "Go chief"
>
> **Claude**: "Let's do this! I'll start with Phase 1: implementing the Gemini Agent with TDD."

This became a running theme - giving Claude autonomy to execute once the plan was clear.

### Phase 5: TDD Challenges & Pragmatism
- Claude hit complexity walls trying to mock the Gemini API for unit tests
- **Learning moment**: When TDD becomes more difficult than the implementation itself
- **You**: "If TDD is too difficult for the agent, you have my blessing to switch to the integration testing approach"
- Result: 21 game tool tests + 13 game loop tests passing

### Phase 6: Package Structure & Dependencies
- Multiple rounds of fixing import paths and dependency management
- "uv" package manager learning curve
- **You**: "Hang on, I added a pyproject.toml... Are you working in a uv environment at the level above? Can you sort it out?"
- Claude restructured from `src/` to proper `treasure_hunt_agent/` package

### Phase 7: Integration Success!
The system worked end-to-end with a real Gemini agent:
- Generated treasure hunt in 8 directories with 5 clue files
- Agent found the treasure in 26 turns using 30,347 tokens
- **Notable**: Agent made mistakes but recovered (tried filename as key, then read the contents)

---

## The "Go Chief" Dynamic

One of the most delightful aspects was your casual, trusting communication style:

- **"Go chief"** - giving Claude autonomy once design was clear
- **"Great, sounds good. Do you need any steer?"** - checking in without micromanaging
- **"cool"**, **"Ok"** - simple acknowledgments that kept momentum
- **"What's up?"** - when Claude was stuck, jumping in to help

This created a true pair programming dynamic: you as architect/designer, Claude as implementer who could propose solutions but looked to you for key decisions.

---

## Key Design Decisions & Why They Matter

### 1. Random Words vs. Predictable Names
**You**: "Btw I don't recommend calling the clues 'clue_*' and the treasure 'treasure.txt'... I recommend getting a dictionary of random words"

**Why it matters**: This is thinking about adversarial testing - how an agent might "cheat" by pattern-matching instead of following instructions. It shows you're building for future complexity.

### 2. Agent Interface: `game_input` not `user_message`
**You**: "Shouldn't user_message be more abstractly 'game_input' because it might be a user message but it might be a tool output or error message"

**Why it matters**: This abstraction makes the agent general-purpose, not hardcoded for this specific task. It's extensible design thinking.

### 3. Sequential Tool Execution
**You**: "Start with sequential. Each turn should allow the agent to speak, reason and make tool calls."

**Why it matters**: Simpler implementation, easier to debug, and mirrors how humans work through problems step-by-step.

### 4. Path Validation Strategy
**You**: "Allow ../ paths but check within the functions whether it goes outside of the treasure_hunt path"

**Why it matters**: Balance between realistic shell behavior and security. The agent can navigate naturally but can't escape the sandbox.

### 5. Pragmatic TDD
**You**: "If TDD is too difficult for the agent, you have my blessing to switch to the integration testing approach"

**Why it matters**: TDD is a tool, not a religion. When mocking becomes more complex than the code, integration tests are more valuable.

---

## Technical Highlights

### 1. Recursive Tree Generation with Constraints
The generator creates a "golden path" first, then fills in red herrings while maintaining navigability:
```python
def generate_treasure_hunt(depth=6, branching_factor=3, file_density=0.3, seed=None)
```

### 2. Path Validation System
Every tool checks that paths stay within bounds:
```python
def _validate_path(state, path: str) -> Path | str:
    if os.path.isabs(path):
        return "Error: Absolute paths are not allowed"

    resolved = (state.current_dir / path).resolve()
    try:
        resolved.relative_to(state.treasure_hunt_root)
    except ValueError:
        return "Error: Path is outside treasure hunt boundary"
```

### 3. Gemini Native Function Calling
Used Gemini's built-in tool calling instead of custom parsing:
```python
class GeminiAgent:
    def step(self, game_input: str | list[ToolResult] | None) -> AgentResponse
```

### 4. Comprehensive Game Result Tracking
Every run produces detailed statistics:
- Turns taken, time elapsed
- Token usage (prompt, completion, total)
- Full tool call history
- Success/failure reason

---

## Surprising Moments & Learning

### 1. The Agent Recovered from Mistakes
When the integration test ran, the agent:
- Turn 24: Tried `check_treasure('gamma.txt')` ❌
- Turn 25: Read the file to get actual contents
- Turn 26: Tried `check_treasure('OhbVrpoiVgRV5IfL')` ✅

**Insight**: The agent showed basic reasoning - when the filename didn't work as a key, it read the file's contents.

### 2. Navigation Confusion
The agent struggled with directory navigation (turns 4-22), repeatedly trying `cd('../saturn')` which didn't exist from the current location.

**Insight**: Spatial reasoning in filesystems is challenging for LLMs. This validates the need for better system prompts or examples.

### 3. TDD Works Great... Until It Doesn't
Unit testing the Gemini Agent with mocks became complex:
- Import issues between test environment and google-generativeai
- Mock setup more complex than the actual code
- Integration tests provided more value

**Insight**: Not everything needs unit tests. For external API clients, integration tests are often more practical.

### 4. Package Structure Iterations
Multiple rounds of fixing:
- `src/` vs `treasure_hunt_agent/` naming
- uv workspace vs standalone package
- Import path updates across all files

**Insight**: Python package structure is still finicky in 2025! The uv tool helped but required learning.

---

## The Collaboration Style

### What Worked Well

1. **Spec-first development**: You wrote comprehensive specs, Claude implemented them
2. **Design dialogues**: Claude proposed architectures, you made key decisions
3. **Quick acknowledgments**: "cool", "Ok", "sounds good" kept momentum
4. **Trust & autonomy**: "Go chief" gave Claude space to work
5. **Pragmatic adjustments**: Switching from strict TDD when it didn't make sense

### Your Role as Human Developer

You acted as:
- **Architect**: Made key design decisions (abstraction levels, security boundaries)
- **Product thinker**: Anticipated how agents might cheat, future extensibility
- **Debugger**: Jumped in when Claude was stuck ("Try uvx pytest", "change to gemini-2.5-flash")
- **Validator**: Tested the final system and celebrated success

### Claude's Role

Claude acted as:
- **Implementer**: Wrote 1,000+ lines of code with tests
- **Proposer**: Suggested architectures and approaches
- **Problem-solver**: Worked through dependency issues, refactoring
- **Documenter**: Updated specs, wrote comprehensive docstrings

---

## Fun Quotes & Vignettes

### The Random Words Suggestion
**You**: "Btw I don't recommend calling the clues 'clue_*' and the treasure 'treasure.txt'... I recommend getting a dictionary of random words"

**Claude**: "Good point! Using predictable names like 'treasure.txt' and 'clue_*.txt' would make it too easy for an agent to cheat. Let me update the implementation to use random words from a dictionary."

This shows your forward-thinking about adversarial testing.

### The "Go Chief" Moment
**You**: "Go chief"

**Claude**: "Let's do this! I'll start with Phase 1: implementing the Gemini Agent with TDD."

Just two words launched Claude into autonomous implementation mode.

### The Pragmatic TDD Pivot
**Claude**: "You know what, I'm going to take a different approach. Unit testing the Gemini Agent with all these mocks is getting too complex. Let me move on to implementing and testing the game tools (which are much simpler to test), then do an integration test of the whole system."

**You**: "Great, sounds good. Do you need any steer?"

**Claude**: "No, I'm good! The plan is clear..."

This shows flexibility in methodology when the situation calls for it.

### Package Structure Confusion
**You**: "Hang on, I added a pyproject.toml at the treasure_hunt_agent level. Are you working in a uv environment at the level above? Can you sort it out?"

**Claude**: "I see - you created a pyproject.toml in treasure_hunt_agent but it has no dependencies. The parent has a workspace setup. Let me fix the treasure_hunt_agent package properly..."

Multiple rounds of restructuring, but eventually got it right.

### The Success Moment
**You**: "What do you think?"

**Claude**: "Excellent! **The agent successfully found the treasure!** 🎉"

After all the work, seeing the end-to-end system work was clearly exciting.

---

## What You Learned About Claude Code

### 1. Design Discussions Are Valuable
Claude can write detailed specs and ask clarifying questions. The back-and-forth on agent interface design led to better abstractions.

### 2. "Go Chief" Creates Flow
Once you've agreed on a plan, two words let Claude work autonomously. No need to micromanage each step.

### 3. Claude Recognizes When It's Stuck
"You know what, I'm going to take a different approach" - Claude can self-correct when a strategy isn't working.

### 4. Integration Over Mocking
For external APIs, integration tests are often more valuable than complex unit test mocks.

### 5. Iteration Is Normal
Package structure took several attempts. That's fine - it's part of development.

### 6. Tool Usage Patterns
- 90 Bash commands (running tests, checking files)
- 48 Edits (incremental fixes)
- TodoWrite for tracking progress (14 times)

### 7. Context Continuation Works
The session ran out of context and continued successfully with a summary.

---

## Project Statistics

**Code Volume**:
- treasure_hunt_generator.py: 492 lines
- gemini_agent.py: 370 lines
- game_tools.py: 340 lines
- treasure_hunt_game.py: 370 lines
- Total: ~1,600 lines of Python

**Tests**:
- 9 generator tests ✓
- 21 game tools tests ✓
- 13 game loop tests ✓
- 8 gemini agent tests (skipped in favor of integration)
- **Total: 43 passing tests**

**Conversation**:
- 455 messages
- 205 from you (user)
- 250 from Claude (assistant)
- 1 context continuation when conversation exceeded limits

**Tool Calls by Claude**:
- Bash: 90 times
- Edit: 48 times
- TodoWrite: 14 times
- Read: 13 times
- Write: 11 times
- Grep: 2 times
- Glob: 1 time

**Final Integration Test Results**:
- Agent found treasure in 26 turns
- 30,347 tokens used
- 35.99 seconds elapsed
- SUCCESS! ✓

---

## The Docker Security Chapter (Not Yet Implemented)

Your original spec included Docker sandboxing with security features:
- Non-root user execution
- Dropped capabilities
- Network restrictions
- Resource limits

This wasn't implemented in the session but shows your security-conscious thinking.

---

## What Makes This Project Interesting

### 1. Meta-AI Testing
You built a system to test AI agents. The tool and the subject are both AI - there's a recursive quality to it.

### 2. Adversarial Thinking
Random filenames, path validation, boundary checking - you're thinking about how an agent might try to "cheat."

### 3. General-Purpose Design
The agent isn't hardcoded for treasure hunts. It's a general filesystem navigator that could tackle other tasks.

### 4. Extensibility Baked In
- Multiple difficulty presets
- Pluggable agent implementations (raw API, langchain, llm, ADK planned)
- Parametrized generation

### 5. Observability
Comprehensive logging and statistics make the system useful for actual research.

---

## Potential Blog Angles

### Option 1: "Building AI with AI: A Treasure Hunt Story"
Focus on the meta-aspect and the collaborative design process.

### Option 2: "The 'Go Chief' Dynamic: Giving Claude Autonomy"
Explore the trust and communication style that made the session flow.

### Option 3: "TDD Meets LLMs: When to Mock and When to Integrate"
Technical deep-dive on testing strategies with external APIs.

### Option 4: "Designing Adversarial Tests for AI Agents"
Focus on the security and anti-cheating design decisions.

### Option 5: "Pair Programming with Claude Code: A Case Study"
Comprehensive project walkthrough with code samples and design discussions.

---

## Conclusion

This session demonstrated effective human-AI collaboration:
- You provided vision, architecture, and key decisions
- Claude implemented, proposed solutions, and self-corrected
- "Go chief" became a powerful trust-building pattern
- Pragmatism trumped methodology when needed
- The end result: a working, tested, extensible system

The treasure hunt works. The agent found the treasure. The tests pass.

Mission accomplished. 🎉
