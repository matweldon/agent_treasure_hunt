"""
Treasure Hunt Agent - An AI agent framework for filesystem exploration games.

This package provides tools for running AI agents through treasure hunt
challenges, where agents must navigate filesystem structures to find
hidden keys.

Main components:
- TreasureHuntGame: The game loop (supports both batch and interactive modes)
- TurnResult: Result of a single turn (for interactive mode)
- GameResult: Final result of a complete game
- InputProvider: Protocol for human input sources

Example (batch mode):
    >>> from treasure_hunt_agent import TreasureHuntGame
    >>> game = TreasureHuntGame("./hunt", agent)
    >>> result = game.run()
    >>> print(f"Success: {result.success}")

Example (interactive mode):
    >>> from treasure_hunt_agent import TreasureHuntGame
    >>> game = TreasureHuntGame("./hunt", agent)
    >>> while True:
    ...     turn = game.take_turn()
    ...     print(f"Turn {turn.turn_number}: {len(turn.tool_calls)} calls")
    ...     if turn.game_over:
    ...         break
"""

from treasure_hunt_agent.treasure_hunt_game import (
    GameResult,
    GameState,
    TreasureHuntGame,
    TurnResult,
)
from treasure_hunt_agent.input_providers import (
    AutoInputProvider,
    CallbackInputProvider,
    CliInputProvider,
    InputProvider,
)
from treasure_hunt_agent.game_tools import TOOL_DEFINITIONS

__all__ = [
    # Game
    "TreasureHuntGame",
    "GameState",
    "GameResult",
    "TurnResult",
    # Input providers
    "InputProvider",
    "CliInputProvider",
    "AutoInputProvider",
    "CallbackInputProvider",
    # Tools
    "TOOL_DEFINITIONS",
]
