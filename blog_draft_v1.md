# Building an AI Testing Framework with Claude Code: The "Go Chief" Dynamic

Last week, I used an AI assistant to build a system for testing AI agents. If that sounds a bit recursive, it was—and it taught me more about AI-assisted development than months of reading about it.

## The Challenge

How do you systematically test whether an AI agent can follow multi-step instructions? Not just complete a single task, but navigate a complex problem space, recover from mistakes, and achieve a goal without explicit step-by-step guidance?

I decided to build a "treasure hunt" system: generate randomized filesystem mazes where an AI agent must read clue files, navigate directories, and ultimately find a hidden treasure key. Think of it as a benchmark that tests spatial reasoning, instruction-following, and problem-solving—all skills we want AI agents to have.

The twist? I'd build this entire system using Claude Code, Anthropic's AI coding assistant. AI building tools to test AI. Meta enough to be interesting, practical enough to ship.

## The Vision

The architecture had three main components:

1. **A Generator** that creates parametrized filesystem trees with clues hidden in text files
2. **A Game Loop** that provides tools (ls, cd, cat, pwd) and enforces boundaries
3. **An Agent** that uses the Gemini API to navigate and solve the puzzle

The system needed to be production-ready: tests, security boundaries, observability, extensibility. Not a demo—a real testing framework that could scale to different difficulty levels and agent implementations.

I started with a detailed spec document outlining the requirements. This turned out to be crucial. Claude and I weren't just writing code—we were designing a system together.

## The "Go Chief" Moment

After reading my spec, Claude proposed an approach:

> "**My proposed approach:**
> 1. Start with the treasure hunt generator module (since everything depends on it)
> 2. Then build a basic agent implementation
> 3. Add Docker sandboxing for security
> 4. Expand to other agent implementations"

I agreed and provided constraints: "Start with the generator - a well-parametrised performant recursive tree-building alg will be key. Start with raw API but consider the extensibility."

Then Claude wrote out a detailed design specification for the agent and game loop architecture. We went back and forth on key decisions:

- Should tools be separate (ls, cd, cat) or combined? *Keep them separate—more realistic.*
- How should path validation work? *Allow `../` but enforce boundaries.*
- Sequential or parallel tool execution? *Sequential—simpler to debug.*

Once the design was clear, I typed two words:

**"Go chief"**

Claude responded: "Let's do this! I'll start with Phase 1: implementing the Gemini Agent with TDD."

And then it just... went. Over the next several hours (with context continuation when we hit limits), Claude wrote approximately 1,600 lines of Python code with 43 passing tests. I wasn't micromanaging every line—I was reviewing, making key decisions, and jumping in when Claude got stuck.

This became the pattern: clear design phase, then autonomous execution with checkpoints.

## The Random Words Insight

About a quarter of the way through implementation, I caught something in Claude's code:

```python
# Files:
# - `start.txt`: Entry point with first clue
# - `clue_*.txt`: Intermediate clue files
# - `treasure.txt`: Final file containing the treasure key
```

I interrupted:

> "Btw I don't recommend calling the clues 'clue_*' and the treasure 'treasure.txt' - that will be too easy for the agent to hack. I recommend getting a dictionary of random words and using that to generate directory and filenames - a big dictionary"

Claude immediately understood:

> "Good point! Using predictable names like 'treasure.txt' and 'clue_*.txt' would make it too easy for an agent to cheat. Let me update the implementation to use random words from a dictionary."

This is the kind of adversarial thinking that separates demos from real testing frameworks. We weren't just building a system that works—we were building one that couldn't be gamed. The agent would need to actually follow instructions, not pattern-match on "treasure.txt."

The final implementation pulled random words from `/usr/share/dict/words`, giving us filenames like "lemon.txt" pointing to "zeta/iron.txt" pointing to "saturn/zeta.txt" with the treasure in "gamma.txt". No patterns to exploit.

## Key Design Decisions

### The `game_input` Abstraction

When reviewing Claude's agent interface design, I noticed something:

```python
def step(self, user_message: str) -> AgentResponse
```

I pushed back: "Shouldn't `user_message` be more abstractly `game_input` because it might be a user message but it might be a tool output or error message?"

Claude agreed and updated the design:

```python
def step(self, game_input: str | list[ToolResult] | None = None) -> AgentResponse
```

This abstraction made the agent general-purpose. It doesn't know it's playing a treasure hunt—it just receives input (initial messages, tool results, or user responses) and produces output (text and tool calls). This means the same agent architecture could tackle completely different tasks.

### Path Validation: Security with Usability

Every tool needed to validate that the agent stayed within bounds:

```python
def _validate_path(state, path: str, must_exist: bool = True,
                   must_be_file: bool = False) -> Path | str:
    # Reject absolute paths
    if os.path.isabs(path):
        return "Error: Absolute paths are not allowed"

    # Resolve and check against hunt root
    resolved = (state.current_dir / path).resolve()
    try:
        resolved.relative_to(state.treasure_hunt_root)
    except ValueError:
        return "Error: Path is outside treasure hunt boundary"

    if must_exist and not resolved.exists():
        return "Error: Path does not exist"

    return resolved
```

This allows natural filesystem navigation (including `../`) while enforcing strict boundaries. The agent can't escape the treasure hunt directory no matter how creatively it tries.

### The TDD Pivot

About halfway through, Claude hit a wall trying to unit test the Gemini agent with mocks:

> "You know what, I'm going to take a different approach. Unit testing the Gemini Agent with all these mocks is getting too complex. Let me move on to implementing and testing the game tools (which are much simpler to test), then do an integration test of the whole system. That's still TDD, just at a higher level."

I gave my blessing: "Great, sounds good. Do you need any steer?"

"No, I'm good! The plan is clear..."

This is what pragmatic development looks like. We didn't abandon testing—we had 21 tests for game tools, 13 for the game loop, 9 for the generator. But when mocking became more complex than the code itself, we pivoted to integration tests. TDD is a tool, not a religion.

## The Messy Middle

Development isn't just elegant design decisions. There were multiple rounds of:

**Dependency wrangling**: "Hang on, I added a pyproject.toml at the treasure_hunt_agent level. Are you working in a uv environment at the level above? Can you sort it out?"

**Import path fixes**: Renaming `src/` to `treasure_hunt_agent/` and updating every import statement across the codebase.

**Model version errors**: Discovering that `gemini-1.5-flash` wasn't available and switching to `gemini-2.5-flash`.

**API response parsing**: Learning that Gemini's `response.text` throws `ValueError` when the response contains only function calls, no text.

Through all of this, the communication pattern stayed consistent:
- Quick acknowledgments ("cool", "Ok", "sounds good") kept momentum
- Specific debugging suggestions when Claude was stuck ("Try uvx pytest", "change to gemini-2.5-flash")
- Trust with checkpoints rather than constant oversight

## Success at Turn 26

Finally, the integration test:

```bash
$ uv run treasure_hunt_agent/examples/run_treasure_hunt.py --difficulty easy

TREASURE HUNT INTEGRATION TEST
======================================================================

✓ Hunt generated:
  Start file: lemon.txt
  Treasure file: zeta/saturn/gamma.txt
  Path length: 3 steps
  Directories: 8
  Files: 5

Running treasure hunt (max_turns=50, max_tokens=100000)...

✓ SUCCESS! The agent found the treasure!

Turns taken: 26
Total time: 35.99s
Token usage: 30,347 tokens
```

The agent navigated the maze, read clues, and found the treasure. More interestingly, it recovered from a mistake:

- **Turn 24**: Tried `check_treasure('gamma.txt')` ❌ (used filename instead of contents)
- **Turn 25**: Read the file to get actual contents
- **Turn 26**: Tried `check_treasure('OhbVrpoiVgRV5IfL')` ✅

This showed basic reasoning—when the filename didn't work as a key, it corrected course and read the file's contents.

The agent did struggle with navigation (turns 4-22), repeatedly trying invalid paths like `cd('../saturn')` from the wrong location. This suggests spatial reasoning in filesystems remains challenging for LLMs—a useful insight for future prompt engineering.

But it worked. After all the iterations, dependency wrangling, and refactoring, we had a working system that actually tested what we wanted it to test.

## What I Learned About AI Pair Programming

### 1. Specs Enable Autonomy

The detailed spec document wasn't bureaucracy—it was the foundation for "Go chief" moments. When both you and the AI understand the goal and constraints, the AI can work autonomously while you focus on architecture and key decisions.

### 2. Design Dialogues Are Valuable

Claude asking clarifying questions ("Should tools be separate or combined?") led to better design. The `game_input` abstraction came from my feedback on Claude's initial proposal. This is collaboration, not just code generation.

### 3. Communication Patterns Matter

What worked:
- **Minimal acknowledgments** ("cool", "sounds good") to maintain flow
- **"Go chief"** to launch autonomous work after design agreement
- **"Do you need any steer?"** to check in without micromanaging
- **Specific suggestions** when stuck ("Try uvx pytest")

What didn't work:
- Over-explaining when the plan was already clear
- Asking Claude to do everything perfectly on the first try
- Treating errors as failures rather than normal development

### 4. Pragmatism Over Methodology

We followed TDD rigorously for straightforward components (game tools, generator) but pivoted to integration tests for complex external APIs. The goal is working, tested code—not adherence to a specific process.

### 5. The Meta-Quality Is Real

Using AI to build AI testing tools creates an interesting feedback loop. Claude Code navigates filesystems, reads files, and executes commands—exactly what we're testing in the treasure hunt. The tool understands the domain because it operates in the domain.

## What's Next

The system is production-ready but there's room to grow:

- **Docker sandboxing**: Add security layers for running untrusted agent code
- **Multiple agent frameworks**: Compare Gemini vs LangChain vs other implementations
- **Statistical analysis**: Run 100 treasure hunts and analyze behavior patterns
- **Difficulty scaling**: Test how agents perform as complexity increases

But the foundation is solid. The tests pass. The agent finds the treasure. And I learned more about AI-assisted development than I expected.

## The Punchline

We built this in one extended session:
- 455 messages (205 from me, 250 from Claude)
- ~1,600 lines of Python
- 43 passing tests
- 179 tool calls by Claude (90 bash commands, 48 file edits)
- 1 context continuation when we hit limits

The code is on GitHub. The system works. And "Go chief" has become my favorite way to collaborate with AI.

When people ask me what AI-assisted development feels like, I think of that moment: after hours of design discussion, typing two words and watching Claude autonomously implement a complex system with tests, error handling, and thoughtful architecture.

Not micromanagement. Not full autonomy. Trust with checkpoints.

That's the future of development—and it's here now.

---

*The treasure hunt agent system is open source at [github.com/matweldon/agent_treasure_hunt](https://github.com/matweldon/agent_treasure_hunt). Try running your own treasure hunts and see how different agent frameworks compare.*
