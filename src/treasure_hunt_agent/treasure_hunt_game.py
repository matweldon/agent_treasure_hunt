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
    """

    def __init__(
        self,
        hunt_path: str,
        agent: Any,
        max_turns: int = 50,
        max_tokens: int = 100000,
    ):
        """Initialize the game."""
        self.hunt_path = Path(hunt_path)
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

    def get_state(self) -> GameState:
        """Get current game state."""
        return self.state

    def get_logs(self) -> list[dict]:
        """Get tool call logs."""
        return self.tool_calls_log

    def run(self) -> GameResult:
        """
        Run the game loop.

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
        start_time = time.time()

        # Send initial message to agent
        initial_message = (
            f"You are at the root of a treasure hunt. "
            f"The starting file is '{self.state.start_file}'. "
            f"Use your tools to navigate the filesystem and find the treasure key. "
            f"When you think you have the key, use check_treasure to verify it."
        )

        game_input: str | list[ToolResult] = initial_message

        # Main game loop
        while (
            not self.state.game_over
            and self.state.turn_number < self.state.max_turns
            and self.state.tokens_used < self.state.max_tokens
        ):
            self.state.turn_number += 1

            # Agent step
            try:
                response = self.agent.step(game_input)
            except Exception as e:
                return self._end_game(
                    success=False,
                    end_reason="error",
                    error=f"Agent error: {e}",
                    start_time=start_time,
                )

            # Track token usage
            self.state.tokens_used += response.usage.get("total_tokens", 0)
            self.state.prompt_tokens_used += response.usage.get("prompt_tokens", 0)
            self.state.completion_tokens_used += response.usage.get(
                "completion_tokens", 0
            )

            # Check token limit
            if self.state.tokens_used >= self.state.max_tokens:
                return self._end_game(
                    success=False,
                    end_reason="max_tokens",
                    error=None,
                    start_time=start_time,
                )

            # Execute tool calls if any
            if response.tool_calls:
                tool_results = self._execute_tools(response.tool_calls)

                # Check if game ended during tool execution
                if self.state.game_over:
                    return self._end_game(
                        success=self.state.success or False,
                        end_reason="treasure_found"
                        if self.state.success
                        else "gave_up",
                        error=None,
                        start_time=start_time,
                    )

                # Feed results back to agent
                game_input = tool_results
            else:
                # No tool calls, just text response
                # This shouldn't happen normally, but handle it
                game_input = "No tools were called. Please use your tools to explore."

        # Loop ended without finding treasure
        if self.state.turn_number >= self.state.max_turns:
            end_reason = "max_turns"
        elif self.state.tokens_used >= self.state.max_tokens:
            end_reason = "max_tokens"
        else:
            end_reason = "unknown"

        return self._end_game(
            success=False, end_reason=end_reason, error=None, start_time=start_time
        )

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

    def _end_game(
        self, success: bool, end_reason: str, error: str | None, start_time: float
    ) -> GameResult:
        """
        End the game and return results.

        Parameters
        ----------
        success : bool
            Whether the game was successful
        end_reason : str
            Reason the game ended
        error : str | None
            Error message if any
        start_time : float
            When the game started

        Returns
        -------
        GameResult
            Final game result
        """
        total_time = time.time() - start_time

        # Try to find treasure key if checked
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
