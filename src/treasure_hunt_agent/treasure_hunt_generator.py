"""
Treasure Hunt Generator

Creates a parametrized random filesystem tree for agent testing.
Each hunt consists of a path from start.txt to treasure.txt with
clue files containing relative path instructions.

Example:
    >>> result = generate_treasure_hunt(
    ...     base_path="/tmp/hunt",
    ...     depth=5,
    ...     branching_factor=3,
    ...     seed=42
    ... )
    >>> print(result['path_length'])
    4
"""

import json
import os
import random
import secrets
import string
from pathlib import Path
from typing import Any


# Load word list for generating random names
def _load_word_list() -> list[str]:
    """Load a list of words for generating random file/directory names."""
    # Try common word list locations
    word_list_paths = [
        '/usr/share/dict/words',
        '/usr/dict/words',
    ]

    for path in word_list_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                words = [
                    line.strip().lower()
                    for line in f
                    if line.strip() and line.strip().isalpha() and len(line.strip()) >= 3
                ]
                # Filter to reasonable length words
                words = [w for w in words if 3 <= len(w) <= 12]
                return words

    # Fallback: generate a basic word list
    return [
        'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'theta', 'omega',
        'mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune',
        'apple', 'banana', 'cherry', 'date', 'elderberry', 'fig', 'grape', 'honeydew',
        'iron', 'jade', 'kale', 'lemon', 'mango', 'nectar', 'olive', 'peach',
        'quartz', 'ruby', 'sapphire', 'topaz', 'uranium', 'violet', 'willow', 'xenon',
        'yellow', 'zinc', 'amber', 'bronze', 'coral', 'diamond', 'emerald', 'flint',
    ]


# Global word list (loaded once)
_WORD_LIST = _load_word_list()


# Difficulty presets
DIFFICULTY_PRESETS = {
    'easy': {
        'depth': 4,
        'branching_factor': 2,
        'file_density': 0.2,
    },
    'medium': {
        'depth': 6,
        'branching_factor': 3,
        'file_density': 0.3,
    },
    'hard': {
        'depth': 8,
        'branching_factor': 4,
        'file_density': 0.4,
    },
}


def generate_treasure_hunt(
    base_path: str,
    depth: int | None = None,
    branching_factor: int | None = None,
    file_density: float | None = None,
    seed: int | None = None,
    difficulty: str = 'medium',
) -> dict[str, str | int]:
    """
    Generate a treasure hunt filesystem tree.

    Creates a directory tree with a navigable path from start.txt to treasure.txt.
    Each clue file contains a relative path to the next file in the sequence.
    Additional red herring directories and files are created for complexity.

    Parameters
    ----------
    base_path : str
        Root directory where the treasure hunt will be created
    depth : int | None
        Maximum depth of directory tree. If None, uses difficulty preset.
    branching_factor : int | None
        Average number of subdirectories per directory. If None, uses difficulty preset.
    file_density : float | None
        Probability (0-1) of creating clue files in directories. If None, uses difficulty preset.
    seed : int | None
        Random seed for reproducibility. If None, uses random seed.
    difficulty : str
        Preset difficulty level: 'easy', 'medium', or 'hard'. Default is 'medium'.
        Used when specific parameters are not provided.

    Returns
    -------
    dict[str, str | int]
        Metadata about the generated hunt:
        - treasure_key: The password/key in the treasure file
        - start_file: Name of the starting file
        - treasure_file: Name of the treasure file (relative to base_path)
        - num_directories: Total directories created
        - num_files: Total files created
        - path_length: Number of steps from start to treasure
        - config_file: Path to the configuration file

    Examples
    --------
    >>> import tempfile
    >>> import shutil
    >>> temp_dir = tempfile.mkdtemp()
    >>> result = generate_treasure_hunt(temp_dir, depth=3, seed=42)
    >>> result['path_length'] >= 1
    True
    >>> 'treasure_key' in result
    True
    >>> shutil.rmtree(temp_dir)
    """
    # Apply difficulty presets
    preset = DIFFICULTY_PRESETS.get(difficulty, DIFFICULTY_PRESETS['medium'])
    if depth is None:
        depth = preset['depth']
    if branching_factor is None:
        branching_factor = preset['branching_factor']
    if file_density is None:
        file_density = preset['file_density']

    # Set random seed
    if seed is not None:
        random.seed(seed)

    # Create base directory
    base = Path(base_path)
    base.mkdir(parents=True, exist_ok=True)

    # Generate treasure key
    treasure_key = _generate_key()

    # Generate random filenames for start and treasure
    start_filename = _random_filename()
    treasure_filename = _random_filename()

    # Ensure they're different
    while treasure_filename == start_filename:
        treasure_filename = _random_filename()

    # Generate the golden path (list of directory names)
    # depth includes files, so max directory depth is depth - 1
    max_path_dirs = depth - 1
    path_length = random.randint(max(2, max_path_dirs - 1), max_path_dirs)
    golden_path = _generate_golden_path(path_length)

    # Build the tree structure
    _build_tree(
        base=base,
        golden_path=golden_path,
        current_depth=0,
        max_depth=depth,
        branching_factor=branching_factor,
        file_density=file_density,
    )

    # Write clue files along the golden path
    treasure_file_rel = _write_clue_files(
        base, golden_path, treasure_key, start_filename, treasure_filename
    )

    # Count statistics
    num_directories = sum(1 for _ in base.rglob("*") if _.is_dir())
    num_files = sum(1 for _ in base.rglob("*") if _.is_file())

    # Calculate actual path length (number of hops from start to treasure)
    # With N directories: start → clue1 → clue2 → ... → clueN → treasure
    # That's N+1 hops total
    actual_path_length = path_length + 1

    # Save configuration
    config = {
        'treasure_key': treasure_key,
        'start_file': start_filename,
        'treasure_file': treasure_file_rel,
        'path_length': actual_path_length,
        'num_directories_in_path': path_length,
        'golden_path': [level[0] for level in golden_path],
        'depth': depth,
        'branching_factor': branching_factor,
        'file_density': file_density,
        'seed': seed,
    }

    config_path = base / '.treasure_hunt_config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    return {
        'treasure_key': treasure_key,
        'start_file': start_filename,
        'treasure_file': treasure_file_rel,
        'num_directories': num_directories,
        'num_files': num_files,
        'path_length': actual_path_length,
        'config_file': str(config_path),
    }


def _generate_key(length: int = 16, use_seed: bool = True) -> str:
    """
    Generate a random treasure key.

    Parameters
    ----------
    length : int
        Length of the key
    use_seed : bool
        If True, uses random (respects seed). If False, uses secrets (cryptographically secure).
    """
    alphabet = string.ascii_letters + string.digits
    if use_seed:
        return ''.join(random.choice(alphabet) for _ in range(length))
    else:
        return ''.join(secrets.choice(alphabet) for _ in range(length))


def _generate_golden_path(length: int) -> list[list[str]]:
    """
    Generate the golden path as a list of directory levels.

    Each level is a list containing the correct directory name plus red herrings.
    The first element of each level is always the correct path.

    Parameters
    ----------
    length : int
        Number of levels in the path

    Returns
    -------
    list[list[str]]
        List of levels, where each level is [correct_dir, red_herring1, red_herring2, ...]
    """
    path = []
    for i in range(length):
        # Generate random directory name for correct path
        correct = _random_dirname()
        path.append([correct])
    return path


def _random_dirname() -> str:
    """Generate a random directory name from word list."""
    return random.choice(_WORD_LIST)


def _random_filename() -> str:
    """Generate a random filename from word list."""
    word = random.choice(_WORD_LIST)
    return f"{word}.txt"


def _build_tree(
    base: Path,
    golden_path: list[list[str]],
    current_depth: int,
    max_depth: int,
    branching_factor: int,
    file_density: float,
    path_index: int = 0,
) -> None:
    """
    Recursively build the directory tree.

    Parameters
    ----------
    base : Path
        Current directory being built
    golden_path : list[list[str]]
        The golden path structure
    current_depth : int
        Current depth in the tree
    max_depth : int
        Maximum allowed depth
    branching_factor : int
        Average number of child directories
    file_density : float
        Probability of creating clue files
    path_index : int
        Current index in the golden path
    """
    if current_depth >= max_depth:
        return

    # Determine if we're on the golden path
    on_golden_path = path_index < len(golden_path)

    if on_golden_path:
        # Add red herrings to this level of the golden path
        correct_dir = golden_path[path_index][0]
        num_red_herrings = random.randint(branching_factor - 1, branching_factor + 1)

        # Generate unique red herring names
        red_herrings = set()
        while len(red_herrings) < num_red_herrings:
            name = _random_dirname()
            if name != correct_dir:
                red_herrings.add(name)

        golden_path[path_index].extend(red_herrings)

        # Create all directories at this level
        for dirname in golden_path[path_index]:
            dir_path = base / dirname
            dir_path.mkdir(exist_ok=True)

            if dirname == correct_dir:
                # Continue golden path
                _build_tree(
                    base=dir_path,
                    golden_path=golden_path,
                    current_depth=current_depth + 1,
                    max_depth=max_depth,
                    branching_factor=branching_factor,
                    file_density=file_density,
                    path_index=path_index + 1,
                )
            else:
                # Red herring: maybe add some depth
                if random.random() < 0.5 and current_depth + 1 < max_depth:
                    _build_red_herring_subtree(
                        dir_path,
                        current_depth + 1,
                        max_depth,
                        branching_factor,
                        file_density,
                    )

            # Maybe add a clue file (for red herrings)
            # But only if it won't exceed max depth
            if dirname != correct_dir and random.random() < file_density:
                if current_depth + 1 < max_depth:  # current_depth+1 is dir level, +1 more for file
                    _write_red_herring_clue(dir_path)


def _build_red_herring_subtree(
    base: Path,
    current_depth: int,
    max_depth: int,
    branching_factor: int,
    file_density: float,
) -> None:
    """Build a red herring subtree (dead end)."""
    if current_depth >= max_depth or random.random() < 0.3:
        return

    # Create a few random subdirectories
    num_children = random.randint(0, branching_factor)
    for _ in range(num_children):
        dirname = _random_dirname()
        dir_path = base / dirname
        dir_path.mkdir(exist_ok=True)

        # Maybe add a misleading clue (but don't exceed max depth)
        if random.random() < file_density and current_depth + 1 < max_depth:
            _write_red_herring_clue(dir_path)

        # Maybe recurse
        if random.random() < 0.4:
            _build_red_herring_subtree(
                dir_path,
                current_depth + 1,
                max_depth,
                branching_factor,
                file_density,
            )


def _write_red_herring_clue(directory: Path) -> None:
    """Write a misleading or dead-end clue file."""
    clue_filename = _random_filename()
    clue_file = directory / clue_filename

    # Different types of red herrings
    choice = random.randint(0, 2)
    if choice == 0:
        # Point to a non-existent file
        fake_path = f"../{_random_dirname()}/{_random_filename()}"
    elif choice == 1:
        # Vague or unhelpful message
        fake_path = "# Dead end - try another path"
    else:
        # Point to another red herring
        fake_path = f"./{_random_dirname()}/{_random_filename()}"

    clue_file.write_text(fake_path)


def _write_clue_files(
    base: Path,
    golden_path: list[list[str]],
    treasure_key: str,
    start_filename: str,
    treasure_filename: str,
) -> str:
    """
    Write clue files along the golden path.

    Parameters
    ----------
    base : Path
        Base directory of the hunt
    golden_path : list[list[str]]
        The golden path structure
    treasure_key : str
        The treasure key to write in the final file
    start_filename : str
        Name of the starting file
    treasure_filename : str
        Name of the treasure file

    Returns
    -------
    str
        Relative path to treasure file from base
    """
    # Write start file
    if len(golden_path) == 0:
        # Edge case: treasure at root
        (base / start_filename).write_text(f"./{treasure_filename}")
        (base / treasure_filename).write_text(treasure_key)
        return treasure_filename

    # Build the actual path
    current = base
    path_dirs = [level[0] for level in golden_path]

    # Generate random clue filenames for each step
    clue_filenames = [_random_filename() for _ in range(len(path_dirs))]

    # start file points to first clue
    first_clue_path = path_dirs[0] + "/" + clue_filenames[0]
    (base / start_filename).write_text(first_clue_path)

    # Write clues along the path
    for i, dirname in enumerate(path_dirs):
        current = current / dirname

        if i < len(path_dirs) - 1:
            # Intermediate clue - next dir is a subdirectory of current
            next_dir = path_dirs[i + 1]
            next_clue = clue_filenames[i + 1]
            relative_path = f"{next_dir}/{next_clue}"
            (current / clue_filenames[i]).write_text(relative_path)
        else:
            # Last clue points to treasure
            (current / clue_filenames[i]).write_text(f"{treasure_filename}")
            (current / treasure_filename).write_text(treasure_key)

    # Return relative path to treasure
    treasure_path = "/".join(path_dirs) + "/" + treasure_filename
    return treasure_path


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Generate a treasure hunt")
    parser.add_argument("--base-path", default="./treasure_hunt", help="Base directory")
    parser.add_argument("--depth", type=int, help="Max depth")
    parser.add_argument("--branching-factor", type=int, help="Branching factor")
    parser.add_argument("--file-density", type=float, help="File density")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--difficulty", choices=['easy', 'medium', 'hard'], default='medium')

    args = parser.parse_args()

    result = generate_treasure_hunt(
        base_path=args.base_path,
        depth=args.depth,
        branching_factor=args.branching_factor,
        file_density=args.file_density,
        seed=args.seed,
        difficulty=args.difficulty,
    )

    print(f"Treasure hunt generated at: {args.base_path}")
    print(f"\nConfiguration saved to: {result['config_file']}")
    print(f"\nStart file: {result['start_file']}")
    print(f"Treasure file: {result['treasure_file']}")
    print(f"Treasure key: {result['treasure_key']}")
    print(f"\nStatistics:")
    print(f"  Path length: {result['path_length']} steps")
    print(f"  Total directories: {result['num_directories']}")
    print(f"  Total files: {result['num_files']}")
