"""
Example: Run a treasure hunt with a Gemini agent.

This script demonstrates two ways to run the treasure hunt:
1. Batch mode: game.run() - runs to completion, returns GameResult
2. Interactive mode: game.take_turn() - step by step with turn visibility

Usage:
    # Batch mode (default)
    python examples/run_treasure_hunt.py

    # Interactive mode
    python examples/run_treasure_hunt.py --interactive

    # With options
    python examples/run_treasure_hunt.py --difficulty medium --seed 42 --interactive

Requires GOOGLE_API_KEY environment variable to be set.

For a nicer CLI experience, use the treasure-hunt command:
    treasure-hunt quick --difficulty easy --interactive
"""

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

from treasure_hunt_agent.game_tools import TOOL_DEFINITIONS
from treasure_hunt_agent.gemini_agent import GeminiAgent
from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame
from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt


def create_agent(model_name: str, api_key: str) -> GeminiAgent:
    """Create a Gemini agent with treasure hunt instructions."""
    system_instructions = """You are an expert at navigating filesystems and solving puzzles.
You are in a treasure hunt where you need to find a hidden treasure key by exploring a directory structure.

Your goal:
1. Start by reading the start file to get your first clue
2. Follow clues by navigating directories and reading files
3. Each clue will point you to the next file with a relative path
4. When you find what you think is the treasure key, use check_treasure to verify it

Available tools:
- ls(path): List files and directories
- cd(path): Change to a directory
- cat(file_path): Read a file's contents
- pwd(): Show current directory
- check_treasure(key): Check if a key is correct (ends game if correct)
- give_up(): Give up (ends game as failure)
- ask_human(question): Ask for help

Tips:
- Read clues carefully - they contain relative paths
- You can use ../ to go up directories
- All paths must stay within the treasure hunt boundaries
- When you see a file that just contains text (not a path), it might be the treasure key!

Be methodical and follow the clues step by step. Good luck!
"""

    return GeminiAgent(
        model_name=model_name,
        system_instructions=system_instructions,
        tools=TOOL_DEFINITIONS,
        api_key=api_key,
    )


def run_batch_mode(game: TreasureHuntGame, treasure_key: str):
    """Run the game in batch mode using game.run()."""
    print("-" * 70)
    print("Running in BATCH mode (game.run())")
    print("-" * 70)
    print()

    game_result = game.run()

    # Print results
    print()
    print("=" * 70)
    print("GAME RESULTS")
    print("=" * 70)
    print()

    if game_result.success:
        print("SUCCESS! The agent found the treasure!")
    else:
        print("FAILURE. The agent did not find the treasure.")

    print()
    print(f"End reason: {game_result.end_reason}")
    print(f"Turns taken: {game_result.turns_taken}")
    print(f"Total time: {game_result.total_time:.2f}s")

    if game_result.error:
        print()
        print("ERROR:")
        print(f"  {game_result.error}")
    print()

    print("Token usage:")
    print(f"  Prompt tokens: {game_result.prompt_tokens:,}")
    print(f"  Completion tokens: {game_result.completion_tokens:,}")
    print(f"  Total tokens: {game_result.total_tokens:,}")
    print()

    if game_result.treasure_key_found:
        print(f"Key attempted: {game_result.treasure_key_found}")
        print(f"Actual key: {treasure_key}")
        if game_result.treasure_key_found == treasure_key:
            print("Keys match!")
        else:
            print("Keys don't match")
    print()

    print(f"Tool calls: {len(game_result.tool_calls)}")
    print()

    # Print tool call history
    print("Tool call history:")
    print("-" * 70)
    for i, call in enumerate(game_result.tool_calls, 1):
        print(f"{i}. Turn {call['turn']}: {call['name']}({call['arguments']})")
        result_str = str(call["result"])
        if len(result_str) > 100:
            result_str = result_str[:97] + "..."
        print(f"   -> {result_str}")
    print()

    return game_result


def run_interactive_mode(game: TreasureHuntGame, treasure_key: str):
    """Run the game in interactive mode using game.take_turn()."""
    print("-" * 70)
    print("Running in INTERACTIVE mode (game.take_turn())")
    print("-" * 70)
    print()

    turn_result = None

    while True:
        # Take a turn
        turn_result = game.take_turn()

        # Display turn info
        print(f"=== Turn {turn_result.turn_number} ===")

        if turn_result.agent_text:
            print(f"Agent: {turn_result.agent_text[:200]}...")
            print()

        if turn_result.tool_calls:
            for tc in turn_result.tool_calls:
                args_str = ", ".join(f"{k}={v!r}" for k, v in tc["arguments"].items())
                print(f"  {tc['name']}({args_str})")
                result_str = str(tc["result"])
                if len(result_str) > 80:
                    result_str = result_str[:77] + "..."
                print(f"    -> {result_str}")
        else:
            print("  (no tool calls)")

        print(f"  Tokens this turn: {turn_result.tokens_used:,}")
        print()

        # Handle human input if needed
        if turn_result.needs_human_input:
            print(f"Agent asks: {turn_result.pending_question}")
            response = input("Your response: ").strip()
            print()

            # Continue with human input
            turn_result = game.take_turn(human_input=response)

            # Display the follow-up turn
            print(f"=== Turn {turn_result.turn_number} (after human input) ===")
            if turn_result.tool_calls:
                for tc in turn_result.tool_calls:
                    args_str = ", ".join(
                        f"{k}={v!r}" for k, v in tc["arguments"].items()
                    )
                    print(f"  {tc['name']}({args_str})")
                    result_str = str(tc["result"])
                    if len(result_str) > 80:
                        result_str = result_str[:77] + "..."
                    print(f"    -> {result_str}")
            print()

        # Check if game is over
        if turn_result.game_over:
            break

    # Print final results
    game_result = turn_result.game_result
    print()
    print("=" * 70)
    print("GAME RESULTS")
    print("=" * 70)
    print()

    if game_result.success:
        print("SUCCESS! The agent found the treasure!")
    else:
        print("FAILURE. The agent did not find the treasure.")

    print()
    print(f"End reason: {game_result.end_reason}")
    print(f"Turns taken: {game_result.turns_taken}")
    print(f"Total time: {game_result.total_time:.2f}s")
    print()

    print("Token usage:")
    print(f"  Prompt tokens: {game_result.prompt_tokens:,}")
    print(f"  Completion tokens: {game_result.completion_tokens:,}")
    print(f"  Total tokens: {game_result.total_tokens:,}")
    print()

    if game_result.treasure_key_found:
        print(f"Key attempted: {game_result.treasure_key_found}")
        print(f"Actual key: {treasure_key}")
        if game_result.treasure_key_found == treasure_key:
            print("Keys match!")
        else:
            print("Keys don't match")

    return game_result


def main():
    parser = argparse.ArgumentParser(
        description="Run treasure hunt with Gemini agent"
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default="easy",
        help="Treasure hunt difficulty",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Gemini model to use",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=50,
        help="Maximum turns allowed",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=100000,
        help="Maximum tokens allowed",
    )
    parser.add_argument(
        "--keep-hunt",
        action="store_true",
        help="Keep the treasure hunt directory after completion",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run interactively using take_turn() instead of run()",
    )

    args = parser.parse_args()

    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set")
        print("Please set it with: export GOOGLE_API_KEY='your-api-key'")
        sys.exit(1)

    print("=" * 70)
    print("TREASURE HUNT EXAMPLE")
    print("=" * 70)
    print()

    # Create temporary directory for hunt
    temp_dir = tempfile.mkdtemp()
    hunt_path = Path(temp_dir) / "treasure_hunt"

    try:
        # Generate treasure hunt
        print(
            f"Generating treasure hunt "
            f"(difficulty: {args.difficulty}, seed: {args.seed})..."
        )
        result = generate_treasure_hunt(
            base_path=str(hunt_path),
            difficulty=args.difficulty,
            seed=args.seed,
        )

        print(f"Hunt generated:")
        print(f"  Path: {hunt_path}")
        print(f"  Start file: {result['start_file']}")
        print(f"  Treasure file: {result['treasure_file']}")
        print(f"  Path length: {result['path_length']} steps")
        print(f"  Directories: {result['num_directories']}")
        print(f"  Files: {result['num_files']}")
        print(f"  Treasure key: {result['treasure_key']} (hidden from agent)")
        print()

        # Create agent
        print(f"Creating Gemini agent (model: {args.model})...")
        agent = create_agent(args.model, api_key)
        print("Agent created")
        print()

        # Create game
        game = TreasureHuntGame(
            hunt_path=str(hunt_path),
            agent=agent,
            max_turns=args.max_turns,
            max_tokens=args.max_tokens,
        )

        # Run game in selected mode
        if args.interactive:
            run_interactive_mode(game, result["treasure_key"])
        else:
            run_batch_mode(game, result["treasure_key"])

        if args.keep_hunt:
            print(f"Treasure hunt kept at: {hunt_path}")
        else:
            print("Cleaning up treasure hunt...")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    finally:
        if not args.keep_hunt:
            shutil.rmtree(temp_dir)

    print()
    print("=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
