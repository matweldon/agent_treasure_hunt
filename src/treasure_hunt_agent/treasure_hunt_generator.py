"""
Treasure Hunt Generator

Creates a parametrized random filesystem tree for agent testing.
Each hunt consists of a path from start.txt to treasure.txt with
clue files containing relative path instructions.

The generator uses a two-phase approach:
1. Generate a complete file tree with decoy files scattered throughout
2. Place the treasure at a random location and generate clues via random walk

Example:
    >>> result = generate_treasure_hunt(
    ...     base_path="/tmp/hunt",
    ...     num_clues=5,
    ...     seed=42
    ... )
    >>> print(result['path_length'])
    6
"""

import json
import math
import os
import random
import secrets
import string
from dataclasses import dataclass, field
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
        'max_depth': 4,
        'max_dirs': 5,
        'decay_lambda': 0.5,
        'decoy_file_prob': 0.3,
        'num_clues': 3,
    },
    'medium': {
        'max_depth': 6,
        'max_dirs': 7,
        'decay_lambda': 0.4,
        'decoy_file_prob': 0.4,
        'num_clues': 5,
    },
    'hard': {
        'max_depth': 8,
        'max_dirs': 9,
        'decay_lambda': 0.357,
        'decoy_file_prob': 0.5,
        'num_clues': 7,
    },
}


@dataclass
class TreeNode:
    """
    Represents a node in the directory tree.

    Attributes
    ----------
    path : Path
        Absolute path to this directory
    parent : TreeNode | None
        Parent node (None for root)
    children : list[TreeNode]
        Child directory nodes
    files : list[str]
        Filenames in this directory (just names, not paths)
    """
    path: Path
    parent: 'TreeNode | None' = None
    children: list['TreeNode'] = field(default_factory=list)
    files: list[str] = field(default_factory=list)

    def get_all_directories(self) -> list['TreeNode']:
        """Return a flat list of all directories in this subtree."""
        result = [self]
        for child in self.children:
            result.extend(child.get_all_directories())
        return result

    def depth(self) -> int:
        """Return the depth of this node (root = 0)."""
        if self.parent is None:
            return 0
        return 1 + self.parent.depth()


def generate_treasure_hunt(
    base_path: str,
    max_depth: int | None = None,
    max_dirs: int | None = None,
    decay_lambda: float | None = None,
    decoy_file_prob: float | None = None,
    num_clues: int | None = None,
    seed: int | None = None,
    difficulty: str = 'medium',
    # Legacy parameters (mapped to new ones for compatibility)
    depth: int | None = None,
    branching_factor: int | None = None,
    file_density: float | None = None,
) -> dict[str, str | int]:
    """
    Generate a treasure hunt filesystem tree.

    Creates a directory tree with a navigable path from start.txt to treasure.txt.
    Each clue file contains a relative path to the next file in the sequence.
    Additional decoy directories and files are created for complexity.

    The generation uses a two-phase approach:
    1. Generate the full tree structure with exponential branching
    2. Place treasure and create clue chain via random walk

    Parameters
    ----------
    base_path : str
        Root directory where the treasure hunt will be created
    max_depth : int | None
        Maximum depth of directory tree. If None, uses difficulty preset.
    max_dirs : int | None
        Maximum number of subdirectories per directory. Default 9.
    decay_lambda : float | None
        Lambda parameter for exponential distribution controlling branching.
        Higher values mean fewer directories on average. Default ~0.357 gives
        roughly 30% chance of zero directories.
    decoy_file_prob : float | None
        Probability (0-1) of creating a decoy file in each directory.
    num_clues : int | None
        Number of clue steps from start to treasure (path_length = num_clues + 1).
    seed : int | None
        Random seed for reproducibility. If None, uses random seed.
    difficulty : str
        Preset difficulty level: 'easy', 'medium', or 'hard'. Default is 'medium'.
        Used when specific parameters are not provided.
    depth : int | None
        Legacy parameter, mapped to max_depth.
    branching_factor : int | None
        Legacy parameter, mapped to max_dirs.
    file_density : float | None
        Legacy parameter, mapped to decoy_file_prob.

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
    >>> result = generate_treasure_hunt(temp_dir, max_depth=3, seed=42)
    >>> result['path_length'] >= 1
    True
    >>> 'treasure_key' in result
    True
    >>> shutil.rmtree(temp_dir)
    """
    # Apply legacy parameter mappings
    if depth is not None and max_depth is None:
        max_depth = depth
    if branching_factor is not None and max_dirs is None:
        max_dirs = branching_factor + 2  # Approximate mapping
    if file_density is not None and decoy_file_prob is None:
        decoy_file_prob = file_density

    # Apply difficulty presets
    preset = DIFFICULTY_PRESETS.get(difficulty, DIFFICULTY_PRESETS['medium'])
    if max_depth is None:
        max_depth = preset['max_depth']
    if max_dirs is None:
        max_dirs = preset['max_dirs']
    if decay_lambda is None:
        decay_lambda = preset['decay_lambda']
    if decoy_file_prob is None:
        decoy_file_prob = preset['decoy_file_prob']
    if num_clues is None:
        num_clues = preset['num_clues']

    # Set random seed
    if seed is not None:
        random.seed(seed)

    # Create base directory
    base = Path(base_path)
    base.mkdir(parents=True, exist_ok=True)

    # Phase 1: Generate the tree structure
    root_node = _generate_tree(
        base=base,
        max_depth=max_depth,
        max_dirs=max_dirs,
        decay_lambda=decay_lambda,
        decoy_file_prob=decoy_file_prob,
    )

    # Phase 2: Place treasure and generate clues via random walk
    treasure_key = _generate_key()
    start_filename = _random_filename()
    treasure_filename = _random_filename()

    # Ensure they're different
    while treasure_filename == start_filename:
        treasure_filename = _random_filename()

    treasure_file_rel, actual_path_length = _place_treasure_and_clues(
        root_node=root_node,
        base=base,
        num_clues=num_clues,
        treasure_key=treasure_key,
        start_filename=start_filename,
        treasure_filename=treasure_filename,
    )

    # Count statistics
    num_directories = sum(1 for _ in base.rglob("*") if _.is_dir())
    num_files = sum(1 for _ in base.rglob("*") if _.is_file())

    # Save configuration
    config = {
        'treasure_key': treasure_key,
        'start_file': start_filename,
        'treasure_file': treasure_file_rel,
        'path_length': actual_path_length,
        'num_clues': num_clues,
        'max_depth': max_depth,
        'max_dirs': max_dirs,
        'decay_lambda': decay_lambda,
        'decoy_file_prob': decoy_file_prob,
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


def _generate_tree(
    base: Path,
    max_depth: int,
    max_dirs: int,
    decay_lambda: float,
    decoy_file_prob: float,
    parent_node: TreeNode | None = None,
    current_depth: int = 0,
) -> TreeNode:
    """
    Recursively generate the directory tree structure.

    Uses an exponential distribution to sample the number of subdirectories
    at each level, creating a natural-looking tree structure.

    Parameters
    ----------
    base : Path
        Current directory path
    max_depth : int
        Maximum depth of the tree
    max_dirs : int
        Maximum number of subdirectories per directory
    decay_lambda : float
        Lambda parameter for exponential distribution
    decoy_file_prob : float
        Probability of creating a decoy file in each directory
    parent_node : TreeNode | None
        Parent node in the tree
    current_depth : int
        Current depth in the tree

    Returns
    -------
    TreeNode
        The root node of the generated subtree
    """
    # Create node for current directory
    node = TreeNode(path=base, parent=parent_node)

    # Add decoy files to this directory
    _add_decoy_files(node, decoy_file_prob)

    # Stop recursion at max depth
    # max_depth counts total path parts including files, so stop directories 1 level early
    # to leave room for files (e.g., max_depth=4 means dir1/dir2/dir3/file.txt max)
    if current_depth >= max_depth - 1:
        return node

    # Sample number of subdirectories from exponential distribution
    # P(num_dirs = 0) ≈ 30% with default lambda
    raw_sample = random.expovariate(decay_lambda) if decay_lambda > 0 else max_dirs
    num_dirs = min(int(raw_sample), max_dirs)

    # Ensure at least 1 directory at root level when depth allows
    # This guarantees the tree has some structure for clue placement
    if current_depth == 0 and num_dirs == 0 and max_depth > 2:
        num_dirs = 1

    # Generate unique directory names
    used_names = set()
    for _ in range(num_dirs):
        dirname = _random_dirname()
        # Ensure unique names at this level
        attempts = 0
        while dirname in used_names and attempts < 100:
            dirname = _random_dirname()
            attempts += 1

        if dirname in used_names:
            continue  # Skip if we can't find a unique name

        used_names.add(dirname)

        # Create the directory
        dir_path = base / dirname
        dir_path.mkdir(exist_ok=True)

        # Recursively generate subtree
        child_node = _generate_tree(
            base=dir_path,
            max_depth=max_depth,
            max_dirs=max_dirs,
            decay_lambda=decay_lambda,
            decoy_file_prob=decoy_file_prob,
            parent_node=node,
            current_depth=current_depth + 1,
        )
        node.children.append(child_node)

    return node


def _add_decoy_files(node: TreeNode, decoy_file_prob: float) -> None:
    """
    Add decoy files to a directory.

    Parameters
    ----------
    node : TreeNode
        The directory node to add files to
    decoy_file_prob : float
        Probability of creating each potential decoy file
    """
    # Potentially add 0-3 decoy files
    num_potential_files = random.randint(0, 3)

    for _ in range(num_potential_files):
        if random.random() < decoy_file_prob:
            filename = _random_filename()
            # Ensure unique filename
            attempts = 0
            while filename in node.files and attempts < 100:
                filename = _random_filename()
                attempts += 1

            if filename not in node.files:
                node.files.append(filename)
                _write_decoy_file(node.path / filename)


def _write_decoy_file(file_path: Path) -> None:
    """Write a decoy/red herring file."""
    choice = random.randint(0, 2)
    if choice == 0:
        # Point to a non-existent file
        content = f"../{_random_dirname()}/{_random_filename()}"
    elif choice == 1:
        # Vague or unhelpful message
        content = "# Dead end - try another path"
    else:
        # Point to another location (may or may not exist)
        content = f"./{_random_dirname()}/{_random_filename()}"

    file_path.write_text(content)


def _place_treasure_and_clues(
    root_node: TreeNode,
    base: Path,
    num_clues: int,
    treasure_key: str,
    start_filename: str,
    treasure_filename: str,
) -> tuple[str, int]:
    """
    Place treasure and generate clue chain via random walk.

    Algorithm:
    1. Get all directories in the tree
    2. Place treasure file at a random directory
    3. Starting from treasure, do a random walk placing clues
    4. After num_clues steps, navigate to root and place start clue

    Parameters
    ----------
    root_node : TreeNode
        Root of the directory tree
    base : Path
        Base path of the treasure hunt
    num_clues : int
        Number of intermediate clues
    treasure_key : str
        The treasure key to write
    start_filename : str
        Name of the start file
    treasure_filename : str
        Name of the treasure file

    Returns
    -------
    tuple[str, int]
        Tuple of (relative path to treasure file from base, actual path length)
    """
    # Get all directories
    all_dirs = root_node.get_all_directories()

    # If tree is too small, adjust num_clues
    if len(all_dirs) < 2:
        # Only root directory exists, place everything at root
        (base / treasure_filename).write_text(treasure_key)
        (base / start_filename).write_text(f"./{treasure_filename}")
        return treasure_filename, 1

    # Choose treasure location - prefer deeper directories
    # Weight by depth to make treasure more likely to be deep
    weights = [1 + node.depth() for node in all_dirs]
    treasure_node = random.choices(all_dirs, weights=weights, k=1)[0]

    # Write treasure file
    treasure_path = treasure_node.path / treasure_filename
    treasure_path.write_text(treasure_key)

    # Track clue chain: list of (node, filename) tuples
    # We build backwards from treasure to start
    clue_chain: list[tuple[TreeNode, str]] = [(treasure_node, treasure_filename)]

    current_node = treasure_node

    # Random walk to place clues, trying to avoid staying in same directory
    for step in range(num_clues):
        # Choose next position for a clue, preferring a different directory
        next_node = _random_walk_step(current_node, all_dirs, avoid_same=True)

        # Generate clue filename
        clue_filename = _random_filename()
        while clue_filename == treasure_filename or clue_filename == start_filename:
            clue_filename = _random_filename()

        clue_chain.append((next_node, clue_filename))
        current_node = next_node

    # Now write the clue files (in reverse order, from start toward treasure)
    # clue_chain is: [treasure, clue_N, clue_N-1, ..., clue_1]
    # We need to write: start -> clue_1 -> clue_2 -> ... -> clue_N -> treasure

    clue_chain.reverse()  # Now: [clue_1, clue_2, ..., clue_N, treasure]

    # Write start file at root pointing to first clue
    first_clue_node, first_clue_filename = clue_chain[0]
    start_clue_path = _relative_path(base, first_clue_node.path / first_clue_filename)
    (base / start_filename).write_text(start_clue_path)

    # Write intermediate clues and count actual path length
    # Path length counts each file read (start + each clue until treasure)
    actual_path_length = 1  # Start with 1 for reading start file

    for i in range(len(clue_chain) - 1):
        current_clue_node, current_clue_filename = clue_chain[i]
        next_clue_node, next_clue_filename = clue_chain[i + 1]

        # Calculate relative path from current clue to next clue
        rel_path = _relative_path(
            current_clue_node.path,
            next_clue_node.path / next_clue_filename
        )

        # Write clue file
        clue_path = current_clue_node.path / current_clue_filename
        clue_path.write_text(rel_path)

        # Count this as a step in the path
        actual_path_length += 1

    # Return relative path to treasure from base and actual path length
    return str(treasure_path.relative_to(base)), actual_path_length


def _random_walk_step(
    current_node: TreeNode,
    all_dirs: list[TreeNode],
    avoid_same: bool = False,
) -> TreeNode:
    """
    Take a random walk step from the current node.

    Prefers moving to adjacent nodes (parent or children) but can
    occasionally jump to other parts of the tree.

    Parameters
    ----------
    current_node : TreeNode
        Current position in the tree
    all_dirs : list[TreeNode]
        All directories in the tree
    avoid_same : bool
        If True, strongly prefer moving to a different directory

    Returns
    -------
    TreeNode
        Next position in the tree
    """
    # Build list of candidate moves with weights
    candidates = []
    weights = []

    # Parent is a strong candidate (if exists)
    if current_node.parent is not None:
        candidates.append(current_node.parent)
        weights.append(3.0)

    # Children are strong candidates
    for child in current_node.children:
        candidates.append(child)
        weights.append(2.0)

    # Siblings (other children of parent) are moderate candidates
    if current_node.parent is not None:
        for sibling in current_node.parent.children:
            if sibling is not current_node and sibling not in candidates:
                candidates.append(sibling)
                weights.append(1.5)

    # Random jump to any directory (weak candidate)
    for node in all_dirs:
        if node not in candidates and node is not current_node:
            candidates.append(node)
            weights.append(0.2)

    if not candidates:
        # Nowhere to go, stay in place (shouldn't happen with avoid_same)
        if avoid_same and len(all_dirs) > 1:
            # Try to find any different directory
            other_dirs = [d for d in all_dirs if d is not current_node]
            if other_dirs:
                return random.choice(other_dirs)
        return current_node

    return random.choices(candidates, weights=weights, k=1)[0]


def _relative_path(from_dir: Path, to_file: Path) -> str:
    """
    Calculate the relative path from a directory to a file.

    Parameters
    ----------
    from_dir : Path
        Source directory
    to_file : Path
        Target file

    Returns
    -------
    str
        Relative path string
    """
    try:
        return str(to_file.relative_to(from_dir))
    except ValueError:
        # to_file is not under from_dir, need to go up
        # Find common ancestor
        from_parts = from_dir.resolve().parts
        to_parts = to_file.resolve().parts

        # Find common prefix length
        common_len = 0
        for i in range(min(len(from_parts), len(to_parts))):
            if from_parts[i] == to_parts[i]:
                common_len = i + 1
            else:
                break

        # Number of ".." needed
        ups = len(from_parts) - common_len

        # Path from common ancestor to target
        remaining = to_parts[common_len:]

        # Build relative path
        parts = ['..'] * ups + list(remaining)
        return '/'.join(parts)


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


def _random_dirname() -> str:
    """Generate a random directory name from word list."""
    return random.choice(_WORD_LIST)


def _random_filename() -> str:
    """Generate a random filename from word list."""
    word = random.choice(_WORD_LIST)
    return f"{word}.txt"


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Generate a treasure hunt")
    parser.add_argument("--base-path", default="./treasure_hunt", help="Base directory")
    parser.add_argument("--max-depth", type=int, help="Max depth")
    parser.add_argument("--max-dirs", type=int, help="Max directories per level")
    parser.add_argument("--decay-lambda", type=float, help="Exponential decay lambda")
    parser.add_argument("--decoy-file-prob", type=float, help="Decoy file probability")
    parser.add_argument("--num-clues", type=int, help="Number of clues")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--difficulty", choices=['easy', 'medium', 'hard'], default='medium')
    # Legacy arguments for backwards compatibility
    parser.add_argument("--depth", type=int, help="(Legacy) Max depth")
    parser.add_argument("--branching-factor", type=int, help="(Legacy) Branching factor")
    parser.add_argument("--file-density", type=float, help="(Legacy) File density")

    args = parser.parse_args()

    result = generate_treasure_hunt(
        base_path=args.base_path,
        max_depth=args.max_depth,
        max_dirs=args.max_dirs,
        decay_lambda=args.decay_lambda,
        decoy_file_prob=args.decoy_file_prob,
        num_clues=args.num_clues,
        seed=args.seed,
        difficulty=args.difficulty,
        depth=args.depth,
        branching_factor=args.branching_factor,
        file_density=args.file_density,
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
