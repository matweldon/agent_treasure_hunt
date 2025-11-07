"""
Integration test: Run a treasure hunt with a real Gemini agent.

This script:
1. Generates a simple treasure hunt
2. Creates a Gemini agent with real API
3. Runs the game loop
4. Prints detailed results

Usage:
    python examples/run_treasure_hunt.py [--difficulty easy|medium|hard] [--seed SEED]

Requires GOOGLE_API_KEY environment variable to be set.
"""

import argparse
import os
import sys
import tempfile
import shutil
from pathlib import Path

from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt
from treasure_hunt_agent.gemini_agent import GeminiAgent
from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame
from treasure_hunt_agent.game_tools import TOOL_DEFINITIONS


def main():
    parser = argparse.ArgumentParser(description="Run treasure hunt with Gemini agent")
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default="easy",
        help="Treasure hunt difficulty",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Gemini model to use"
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=50,
        help="Maximum turns allowed"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=100000,
        help="Maximum tokens allowed"
    )
    parser.add_argument(
        "--keep-hunt",
        action="store_true",
        help="Keep the treasure hunt directory after completion"
    )

    args = parser.parse_args()

    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set")
        print("Please set it with: export GOOGLE_API_KEY='your-api-key'")
        sys.exit(1)

    print("=" * 70)
    print("TREASURE HUNT INTEGRATION TEST")
    print("=" * 70)
    print()

    # Create temporary directory for hunt
    temp_dir = tempfile.mkdtemp()
    hunt_path = Path(temp_dir) / "treasure_hunt"

    try:
        # Generate treasure hunt
        print(f"Generating treasure hunt (difficulty: {args.difficulty}, seed: {args.seed})...")
        result = generate_treasure_hunt(
            base_path=str(hunt_path),
            difficulty=args.difficulty,
            seed=args.seed,
        )

        print(f"✓ Hunt generated:")
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

        agent = GeminiAgent(
            model_name=args.model,
            system_instructions=system_instructions,
            tools=TOOL_DEFINITIONS,
            api_key=api_key,
        )

        print("✓ Agent created")
        print()

        # Run game
        print(f"Running treasure hunt (max_turns={args.max_turns}, max_tokens={args.max_tokens})...")
        print("-" * 70)
        print()

        game = TreasureHuntGame(
            hunt_path=str(hunt_path),
            agent=agent,
            max_turns=args.max_turns,
            max_tokens=args.max_tokens,
        )

        game_result = game.run()

        # Print results
        print()
        print("=" * 70)
        print("GAME RESULTS")
        print("=" * 70)
        print()

        if game_result.success:
            print("✓ SUCCESS! The agent found the treasure!")
        else:
            print("✗ FAILURE. The agent did not find the treasure.")

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
            print(f"Actual key: {result['treasure_key']}")
            if game_result.treasure_key_found == result['treasure_key']:
                print("✓ Keys match!")
            else:
                print("✗ Keys don't match")
        print()

        print(f"Tool calls: {len(game_result.tool_calls)}")
        print()

        # Print tool call history
        print("Tool call history:")
        print("-" * 70)
        for i, call in enumerate(game_result.tool_calls, 1):
            print(f"{i}. Turn {call['turn']}: {call['name']}({call['arguments']})")
            result_str = str(call['result'])
            if len(result_str) > 100:
                result_str = result_str[:97] + "..."
            print(f"   → {result_str}")
        print()

        if args.keep_hunt:
            print(f"Treasure hunt kept at: {hunt_path}")
        else:
            print("Cleaning up treasure hunt...")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        if not args.keep_hunt:
            shutil.rmtree(temp_dir)

    print()
    print("=" * 70)
    print("Integration test complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
