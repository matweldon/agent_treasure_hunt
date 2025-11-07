"""
Example agent that navigates a treasure hunt.

This is a simple demonstration agent that reads the config file
and follows the clues to find the treasure.
"""

import argparse
import json
from pathlib import Path


def navigate_treasure_hunt(hunt_path: str) -> dict[str, str | int]:
    """
    Navigate a treasure hunt and find the treasure.

    This is a cheating agent that reads the config file.
    A real agent would need to explore the filesystem.

    Parameters
    ----------
    hunt_path : str
        Path to the treasure hunt directory

    Returns
    -------
    dict
        Results including steps taken and treasure key found
    """
    base = Path(hunt_path).resolve()

    # Read config (cheating!)
    config_path = base / '.treasure_hunt_config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    print(f"Starting treasure hunt at: {hunt_path}")
    print(f"Start file: {config['start_file']}")
    print()

    # Navigate the hunt
    current_file = base / config['start_file']
    treasure_filename = Path(config['treasure_file']).name
    steps = 0
    visited = []

    while current_file.name != treasure_filename and steps < 100:
        print(f"Step {steps + 1}: Reading {current_file.relative_to(base)}")
        visited.append(str(current_file.relative_to(base)))

        clue = current_file.read_text().strip()
        print(f"  Clue: {clue}")

        # Navigate to next file
        next_file = (current_file.parent / clue).resolve()
        current_file = next_file
        steps += 1

    # Read treasure
    treasure_key = current_file.read_text().strip()
    visited.append(str(current_file.relative_to(base)))

    print(f"\nFound treasure at: {current_file.relative_to(base)}")
    print(f"Treasure key: {treasure_key}")
    print(f"Total steps: {steps}")
    print(f"\nPath taken:")
    for i, step in enumerate(visited, 1):
        print(f"  {i}. {step}")

    # Verify
    if treasure_key == config['treasure_key']:
        print("\n✓ Treasure key matches!")
    else:
        print("\n✗ Treasure key does NOT match!")

    return {
        'steps': steps,
        'treasure_key': treasure_key,
        'path': visited,
        'success': treasure_key == config['treasure_key'],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Navigate a treasure hunt")
    parser.add_argument("--hunt-path", default="./treasure_hunt", help="Path to treasure hunt")

    args = parser.parse_args()

    result = navigate_treasure_hunt(args.hunt_path)

    if result['success']:
        print("\n SUCCESS! Found the treasure!")
    else:
        print("\n FAILED to find the treasure.")
