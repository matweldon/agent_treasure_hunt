"""
Treasure Hunt Game Loop.

Manages the game state, runs the agent loop, executes tools,
and tracks progress until the agent finds the treasure or fails.

Example:
    >>> from gemini_agent import GeminiAgent
    >>> agent = GeminiAgent("gemini-1.5-flash", "You are helpful", TOOL_DEFINITIONS)
    >>> game = TreasureHuntGame("./treasure_hunt", agent)
    >>> result = game.run()
    >>> print(f"Success: {result.success}, Turns: {result.turns_taken}")
    Success: True, Turns: 12
"""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from treasure_hunt_agent.game_tools import (
    ls,
    cd,
    cat,
    pwd,
    check_treasure,
    give_up,
    ask_human,
    TOOL_DEFINITIONS,
)


# Import ToolResult from gemini_agent if available, otherwise define it
try:
    from treasure_hunt_agent.gemini_agent import ToolResult
except ImportError:
    # Define locally for testing
    @dataclass
    class ToolResult:
        """Result of a tool execution."""

        tool_call_id: str
        name: str
        result: str | dict


@dataclass
class GameState:
    """
    State of the treasure hunt game.

    Attributes
    ----------
    treasure_hunt_root : Path
        Root directory of the treasure hunt (boundary for all operations)
    current_dir : Path
        Agent's current working directory
    turn_number : int
        Current turn number
    max_turns : int
        Maximum allowed turns
    max_tokens : int
        Maximum allowed tokens
    tokens_used : int
        Total tokens used so far
    start_time : float
        When the game started (Unix timestamp)
    treasure_key : str
        The correct treasure key
    start_file : str
        Name of the starting file
    game_over : bool
        Whether the game has ended
    success : bool | None
        Whether the agent succeeded (None if ongoing)
    """

    treasure_hunt_root: Path
    current_dir: Path
    turn_number: int = 0
    max_turns: int = 50
    max_tokens: int = 100000
    tokens_used: int = 0
    prompt_tokens_used: int = 0
    completion_tokens_used: int = 0
    start_time: float = field(default_factory=time.time)
    treasure_key: str = ""
    start_file: str = ""
    game_over: bool = False
    success: bool | None = None


@dataclass
class GameResult:
    """
    Result of a treasure hunt game.

    Attributes
    ----------
    success : bool
        Whether the agent found the treasure
    turns_taken : int
        Number of turns taken
    treasure_key_found : str | None
        The key the agent tried (if any)
    total_tokens : int
        Total tokens used
    prompt_tokens : int
        Prompt tokens used
    completion_tokens : int
        Completion tokens used
    total_time : float
        Total time taken (seconds)
    tool_calls : list[dict]
        All tool calls made during the game
    final_state : GameState
        Final game state
    end_reason : str
        Why the game ended
    error : str | None
        Error message if game ended in error
    """

    success: bool
    turns_taken: int
    treasure_key_found: str | None
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_time: float
    tool_calls: list[dict]
    final_state: Any  # GameState
    end_reason: str
    error: str | None = None


@dataclass
class TurnResult:
    """
    Result of a single turn in the treasure hunt.

    Attributes
    ----------
    turn_number : int
        Which turn this was
    agent_text : str | None
        Any text response from the agent
    tool_calls : list[dict]
        Tool calls made this turn (name, arguments, result)
    needs_human_input : bool
        Whether the agent is waiting for human input
    pending_question : str | None
        Question for the human (if needs_human_input)
    game_over : bool
        Whether the game has ended
    game_result : GameResult | None
        Final result (only set when game_over=True)
    tokens_used : int
        Tokens used this turn
    error : str | None
        Error message if turn failed
    """

    turn_number: int
    agent_text: str | None
    tool_calls: list[dict]
    needs_human_input: bool
    pending_question: str | None
    game_over: bool
    game_result: GameResult | None
    tokens_used: int
    error: str | None = None


class TreasureHuntGame:
    """
    Treasure hunt game loop.

    Manages the game state, runs the agent in a loop, executes tools,
    and tracks progress.

    Parameters
    ----------
    hunt_path : str
        Path to the treasure hunt directory
    agent : Agent
        Agent to run (must have step() method)
    max_turns : int
        Maximum number of turns allowed
    max_tokens : int
        Maximum number of tokens allowed

    Examples
    --------
    >>> game = TreasureHuntGame("./hunt", agent)
    >>> result = game.run()
    >>> print(result.success)
    True

    For interactive use:
    >>> game = TreasureHuntGame("./hunt", agent)
    >>> while True:
    ...     result = game.take_turn()
    ...     print(f"Turn {result.turn_number}: {len(result.tool_calls)} tool calls")
    ...     if result.needs_human_input:
    ...         response = input(f"Agent asks: {result.pending_question}")
    ...         result = game.take_turn(human_input=response)
    ...     if result.game_over:
    ...         break
    """

    def __init__(
        self,
        hunt_path: str,
        agent: Any,
        max_turns: int = 50,
        max_tokens: int = 100000,
    ):
        """Initialize the game."""
        self.hunt_path = Path(hunt_path).resolve()
        self.agent = agent
        self.tool_calls_log: list[dict] = []

        # Load hunt configuration
        config_path = self.hunt_path / ".treasure_hunt_config.json"
        with open(config_path, "r") as f:
            config = json.load(f)

        # Initialize game state
        self.state = GameState(
            treasure_hunt_root=self.hunt_path,
            current_dir=self.hunt_path,
            max_turns=max_turns,
            max_tokens=max_tokens,
            treasure_key=config["treasure_key"],
            start_file=config["start_file"],
        )

        # Tool function mapping
        self.tools = {
            "ls": ls,
            "cd": cd,
            "cat": cat,
            "pwd": pwd,
            "check_treasure": check_treasure,
            "give_up": give_up,
            "ask_human": ask_human,
        }

        # Turn-by-turn state
        self._initialized = False
        self._start_time: float = 0.0
        self._next_input: str | list[ToolResult] | None = None
        self._pending_human_question: str | None = None
        self._pending_tool_results: list[ToolResult] | None = None

    def get_state(self) -> GameState:
        """Get current game state."""
        return self.state

    def get_logs(self) -> list[dict]:
        """Get tool call logs."""
        return self.tool_calls_log

    def _initialize(self) -> None:
        """Initialize the game for the first turn."""
        if self._initialized:
            return

        self._start_time = time.time()
        self._next_input = (
            f"You are at the root of a treasure hunt. "
            f"The starting file is '{self.state.start_file}'. "
            f"Use your tools to navigate the filesystem and find the treasure key. "
            f"When you think you have the key, use check_treasure to verify it."
        )
        self._initialized = True

    def take_turn(self, human_input: str | None = None) -> TurnResult:
        """
        Execute a single turn and return the result.

        Parameters
        ----------
        human_input : str | None
            Response to a pending human question (if any)

        Returns
        -------
        TurnResult
            Result of this turn, including tool calls and whether game ended

        Examples
        --------
        >>> result = game.take_turn()
        >>> if result.needs_human_input:
        ...     answer = input(result.pending_question)
        ...     result = game.take_turn(human_input=answer)
        """
        # Initialize on first call
        self._initialize()

        # If game is already over, return the final result
        if self.state.game_over:
            return TurnResult(
                turn_number=self.state.turn_number,
                agent_text=None,
                tool_calls=[],
                needs_human_input=False,
                pending_question=None,
                game_over=True,
                game_result=self._build_game_result(
                    success=self.state.success or False,
                    end_reason="already_ended",
                    error=None,
                ),
                tokens_used=0,
            )

        # If we were waiting for human input, inject it
        if human_input is not None and self._pending_human_question is not None:
            # Find the ask_human result and replace it
            if self._pending_tool_results:
                for tr in self._pending_tool_results:
                    if tr.name == "ask_human":
                        tr.result = human_input
                        break
                self._next_input = self._pending_tool_results
            self._pending_human_question = None
            self._pending_tool_results = None

        # Check turn limit
        if self.state.turn_number >= self.state.max_turns:
            game_result = self._build_game_result(
                success=False, end_reason="max_turns", error=None
            )
            self.state.game_over = True
            return TurnResult(
                turn_number=self.state.turn_number,
                agent_text=None,
                tool_calls=[],
                needs_human_input=False,
                pending_question=None,
                game_over=True,
                game_result=game_result,
                tokens_used=0,
            )

        # Check token limit
        if self.state.tokens_used >= self.state.max_tokens:
            game_result = self._build_game_result(
                success=False, end_reason="max_tokens", error=None
            )
            self.state.game_over = True
            return TurnResult(
                turn_number=self.state.turn_number,
                agent_text=None,
                tool_calls=[],
                needs_human_input=False,
                pending_question=None,
                game_over=True,
                game_result=game_result,
                tokens_used=0,
            )

        # Increment turn
        self.state.turn_number += 1

        # Agent step
        try:
            response = self.agent.step(self._next_input)
        except Exception as e:
            game_result = self._build_game_result(
                success=False, end_reason="error", error=f"Agent error: {e}"
            )
            self.state.game_over = True
            return TurnResult(
                turn_number=self.state.turn_number,
                agent_text=None,
                tool_calls=[],
                needs_human_input=False,
                pending_question=None,
                game_over=True,
                game_result=game_result,
                tokens_used=0,
                error=f"Agent error: {e}",
            )

        # Track token usage
        turn_tokens = response.usage.get("total_tokens", 0)
        self.state.tokens_used += turn_tokens
        self.state.prompt_tokens_used += response.usage.get("prompt_tokens", 0)
        self.state.completion_tokens_used += response.usage.get("completion_tokens", 0)

        # Check token limit after this turn
        if self.state.tokens_used >= self.state.max_tokens:
            game_result = self._build_game_result(
                success=False, end_reason="max_tokens", error=None
            )
            self.state.game_over = True
            return TurnResult(
                turn_number=self.state.turn_number,
                agent_text=response.text,
                tool_calls=[],
                needs_human_input=False,
                pending_question=None,
                game_over=True,
                game_result=game_result,
                tokens_used=turn_tokens,
            )

        # Execute tool calls if any
        turn_tool_calls: list[dict] = []
        pending_question: str | None = None

        if response.tool_calls:
            tool_results = self._execute_tools(response.tool_calls)

            # Collect tool call info for this turn
            for tc in response.tool_calls:
                # Find the matching log entry
                for log in reversed(self.tool_calls_log):
                    if log["turn"] == self.state.turn_number and log["name"] == tc.name:
                        turn_tool_calls.append(log)
                        break

            # Check for ask_human call
            for tc, tr in zip(response.tool_calls, tool_results):
                if tc.name == "ask_human":
                    pending_question = tc.arguments.get("question", "")
                    self._pending_human_question = pending_question
                    self._pending_tool_results = tool_results
                    break

            # Check if game ended during tool execution
            if self.state.game_over:
                game_result = self._build_game_result(
                    success=self.state.success or False,
                    end_reason="treasure_found" if self.state.success else "gave_up",
                    error=None,
                )
                return TurnResult(
                    turn_number=self.state.turn_number,
                    agent_text=response.text,
                    tool_calls=turn_tool_calls,
                    needs_human_input=False,
                    pending_question=None,
                    game_over=True,
                    game_result=game_result,
                    tokens_used=turn_tokens,
                )

            # If waiting for human, don't advance to next input yet
            if pending_question is None:
                self._next_input = tool_results
        else:
            # No tool calls, just text response
            self._next_input = "No tools were called. Please use your tools to explore."

        return TurnResult(
            turn_number=self.state.turn_number,
            agent_text=response.text,
            tool_calls=turn_tool_calls,
            needs_human_input=pending_question is not None,
            pending_question=pending_question,
            game_over=False,
            game_result=None,
            tokens_used=turn_tokens,
        )

    def _build_game_result(
        self, success: bool, end_reason: str, error: str | None
    ) -> GameResult:
        """Build a GameResult from current state."""
        total_time = time.time() - self._start_time if self._start_time else 0.0

        # Find treasure key if checked
        treasure_key_found = None
        for log in self.tool_calls_log:
            if log["name"] == "check_treasure":
                treasure_key_found = log["arguments"].get("key")
                break

        return GameResult(
            success=success,
            turns_taken=self.state.turn_number,
            treasure_key_found=treasure_key_found,
            total_tokens=self.state.tokens_used,
            prompt_tokens=self.state.prompt_tokens_used,
            completion_tokens=self.state.completion_tokens_used,
            total_time=total_time,
            tool_calls=self.tool_calls_log,
            final_state=self.state,
            end_reason=end_reason,
            error=error,
        )

    def run(self) -> GameResult:
        """
        Run the game loop to completion.

        This is the non-interactive mode that runs until the game ends.
        For interactive/step-by-step control, use take_turn() instead.

        Returns
        -------
        GameResult
            Final result of the game

        Examples
        --------
        >>> result = game.run()
        >>> print(f"Success: {result.success}")
        Success: True
        """
        while True:
            result = self.take_turn()
            if result.game_over:
                return result.game_result  # type: ignore

    def _execute_tools(self, tool_calls: list[Any]) -> list[ToolResult]:
        """
        Execute tool calls sequentially.

        Parameters
        ----------
        tool_calls : list[ToolCall]
            Tool calls to execute

        Returns
        -------
        list[ToolResult]
            Results from each tool execution
        """
        results = []

        for tool_call in tool_calls:
            # Get tool function
            tool_func = self.tools.get(tool_call.name)
            if not tool_func:
                result = f"Error: Unknown tool: {tool_call.name}"
            else:
                # Execute tool
                try:
                    # Handle optional path parameter for ls
                    if tool_call.name == "ls" and "path" not in tool_call.arguments:
                        tool_call.arguments["path"] = "."

                    result = tool_func(self.state, **tool_call.arguments)
                except Exception as e:
                    result = f"Error executing {tool_call.name}: {e}"

            # Log tool call
            self.tool_calls_log.append(
                {
                    "turn": self.state.turn_number,
                    "name": tool_call.name,
                    "arguments": tool_call.arguments,
                    "result": result,
                }
            )

            # Create tool result
            tool_result = ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                result=result,
            )
            results.append(tool_result)

            # Check if this was a terminating tool
            if tool_call.name in ["check_treasure", "give_up"]:
                if self.state.game_over:
                    # Stop executing remaining tools
                    break

        return results
