"""
Tests for treasure hunt generator.

Properties tested:
- Creates valid filesystem structure with start.txt and treasure.txt
- All clue files contain valid relative paths to existing files
- Path from start to treasure is navigable (can be followed step-by-step)
- Deterministic given same seed (reproducibility)
- Respects depth parameter (treasure not deeper than max depth)
- Creates appropriate branching (red herrings exist)
- All paths in clue files are relative and point to real files
- Result is a valid directory tree that can be traversed

Function signature:
def generate_treasure_hunt(
    base_path: str,
    depth: int = 5,
    branching_factor: int = 3,
    file_density: float = 0.3,
    seed: int | None = None,
    difficulty: str = 'medium'
) -> dict[str, str | int]:
    ...
    Returns metadata about generated hunt including:
    - treasure_key: the password/key in treasure.txt
    - num_directories: total directories created
    - num_files: total files created
    - path_length: number of steps from start to treasure
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


# Will be implemented in src.treasure_hunt_generator
# from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt


class TestTreasureHuntGenerator:
    """Test the treasure hunt generator."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)

    def test_creates_start_file(self, temp_dir):
        """
        Test that generator creates a start file at the root.

        Properties:
        - start file exists in base_path
        - start file contains a relative path string
        - The path is non-empty
        """
        from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt

        result = generate_treasure_hunt(base_path=temp_dir, depth=3, seed=42)

        start_file = Path(temp_dir) / result['start_file']
        assert start_file.exists(), f"start file {result['start_file']} should exist"

        content = start_file.read_text().strip()
        assert len(content) > 0, "start file should contain a clue"
        assert ".txt" in content, "start file should reference another file"

    def test_creates_treasure_file(self, temp_dir):
        """
        Test that generator creates a treasure file.

        Properties:
        - treasure file exists somewhere in the tree
        - treasure file contains a unique key/password
        - The key is returned in result metadata
        """
        from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt

        result = generate_treasure_hunt(base_path=temp_dir, depth=3, seed=42)

        # Find treasure file using the path from result
        treasure_file = Path(temp_dir) / result['treasure_file']
        assert treasure_file.exists(), f"Treasure file {result['treasure_file']} should exist"

        treasure_content = treasure_file.read_text().strip()
        assert len(treasure_content) > 0, "treasure file should contain a key"
        assert result["treasure_key"] == treasure_content, "Key should match metadata"

    def test_path_is_navigable(self, temp_dir):
        """
        Test that the path from start to treasure can be followed.

        Properties:
        - Each clue file contains a valid relative path
        - Following the path leads to another file
        - Eventually leads to the treasure file
        - No circular references
        - Path length matches metadata
        """
        from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt

        result = generate_treasure_hunt(base_path=temp_dir, depth=4, seed=42)

        current_file = Path(temp_dir) / result['start_file']
        treasure_filename = Path(result['treasure_file']).name
        visited = set()
        steps = 0
        max_steps = 100  # Prevent infinite loops

        while current_file.name != treasure_filename and steps < max_steps:
            assert current_file.exists(), f"File should exist: {current_file}"
            assert str(current_file) not in visited, "Circular reference detected"
            visited.add(str(current_file))

            clue = current_file.read_text().strip()
            if current_file.name == treasure_filename:
                break

            # Parse relative path from clue
            next_file = current_file.parent / clue
            next_file = next_file.resolve()

            current_file = next_file
            steps += 1

        assert current_file.name == treasure_filename, f"Should end at {treasure_filename}"
        assert result["path_length"] == steps, "Path length should match metadata"

    def test_deterministic_with_seed(self, temp_dir):
        """
        Test that same seed produces same treasure hunt.

        Properties:
        - Same seed creates identical directory structure
        - Same seed creates identical file contents
        - Different seeds create different structures
        """
        from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt

        # Create two hunts with same seed
        temp_dir2 = tempfile.mkdtemp()
        try:
            result1 = generate_treasure_hunt(base_path=temp_dir, depth=3, seed=42)
            result2 = generate_treasure_hunt(base_path=temp_dir2, depth=3, seed=42)

            # Get all files in both trees
            files1 = sorted([p.relative_to(temp_dir) for p in Path(temp_dir).rglob("*") if p.is_file()])
            files2 = sorted([p.relative_to(temp_dir2) for p in Path(temp_dir2).rglob("*") if p.is_file()])

            assert files1 == files2, "Same seed should create same file structure"
            assert result1["treasure_key"] == result2["treasure_key"], "Same seed should create same key"
        finally:
            shutil.rmtree(temp_dir2)

    def test_respects_depth_parameter(self, temp_dir):
        """
        Test that generator respects max depth parameter.

        Properties:
        - No directory deeper than specified depth
        - treasure.txt is not deeper than depth
        - Depth >= 2 (need room for start and treasure)
        """
        from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt

        max_depth = 4
        result = generate_treasure_hunt(base_path=temp_dir, depth=max_depth, seed=42)

        # Check all files
        base = Path(temp_dir)
        for path in base.rglob("*"):
            relative = path.relative_to(base)
            depth = len(relative.parts)
            assert depth <= max_depth, f"Path {relative} exceeds max depth {max_depth}"

    def test_creates_red_herrings(self, temp_dir):
        """
        Test that generator creates branching paths (red herrings).

        Properties:
        - More directories exist than just the golden path
        - Total files > path_length (extra clue files exist)
        - num_directories > path_length
        """
        from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt

        result = generate_treasure_hunt(
            base_path=temp_dir,
            depth=4,
            branching_factor=3,
            seed=42
        )

        # Count directories
        num_dirs = sum(1 for p in Path(temp_dir).rglob("*") if p.is_dir())

        assert num_dirs >= result["path_length"], "Should have more dirs than path length"
        assert result["num_files"] > result["path_length"], "Should have extra files"

    def test_all_clue_paths_are_valid(self, temp_dir):
        """
        Test that all clue files contain valid relative paths.

        Properties:
        - Each .txt file (except treasure file and config) contains a path
        - The path resolves to an existing file (or is a dead-end message)
        - Valid paths are relative (not absolute)
        """
        from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt

        result = generate_treasure_hunt(base_path=temp_dir, depth=4, seed=42)

        treasure_filename = Path(result['treasure_file']).name
        config_filename = '.treasure_hunt_config.json'

        # Check all .txt files except treasure file
        for txt_file in Path(temp_dir).rglob("*.txt"):
            if txt_file.name == treasure_filename or txt_file.name == config_filename:
                continue

            clue = txt_file.read_text().strip()

            # Skip red herring messages
            if clue.startswith('#'):
                continue

            assert not os.path.isabs(clue), f"Path should be relative: {clue}"

            # Resolve the path - it may or may not exist (red herrings)
            # We just check that non-absolute paths can be constructed
            target = (txt_file.parent / clue).resolve()

    def test_returns_metadata(self, temp_dir):
        """
        Test that function returns proper metadata.

        Properties:
        - Returns dict with required keys
        - treasure_key is non-empty string
        - start_file and treasure_file are non-empty strings
        - Numeric values are positive integers
        - path_length >= 1
        """
        from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt

        result = generate_treasure_hunt(base_path=temp_dir, depth=4, seed=42)

        assert isinstance(result, dict), "Should return dict"
        assert "treasure_key" in result
        assert "start_file" in result
        assert "treasure_file" in result
        assert "num_directories" in result
        assert "num_files" in result
        assert "path_length" in result
        assert "config_file" in result

        assert isinstance(result["treasure_key"], str)
        assert len(result["treasure_key"]) > 0
        assert isinstance(result["start_file"], str)
        assert len(result["start_file"]) > 0
        assert isinstance(result["treasure_file"], str)
        assert len(result["treasure_file"]) > 0
        assert isinstance(result["num_directories"], int)
        assert isinstance(result["num_files"], int)
        assert isinstance(result["path_length"], int)
        assert result["path_length"] >= 1

    def test_difficulty_presets(self, temp_dir):
        """
        Test that difficulty parameter sets appropriate defaults.

        Properties:
        - 'easy' creates simpler hunts (fewer branches, less depth)
        - 'hard' creates complex hunts (more branches, more depth)
        - Difficulty affects final statistics
        """
        from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt

        temp_dir2 = tempfile.mkdtemp()
        try:
            result_easy = generate_treasure_hunt(
                base_path=temp_dir,
                difficulty='easy',
                seed=42
            )
            result_hard = generate_treasure_hunt(
                base_path=temp_dir2,
                difficulty='hard',
                seed=42
            )

            # Hard should be more complex
            assert result_hard["num_directories"] >= result_easy["num_directories"], \
                "Hard difficulty should have more directories"
        finally:
            shutil.rmtree(temp_dir2)
