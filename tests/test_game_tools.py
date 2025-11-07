"""
Tests for treasure hunt game tools.

Properties tested:
- ls() lists files and directories, stays within hunt root
- cd() changes directory, stays within hunt root
- cat() reads files, stays within hunt root
- pwd() returns current directory relative to hunt root
- All tools reject paths that escape hunt root
- Tools return appropriate error messages
- Tools handle missing files/directories gracefully

Function signatures:
def ls(state: GameState, path: str = ".") -> str
def cd(state: GameState, path: str) -> str
def cat(state: GameState, file_path: str) -> str
def pwd(state: GameState) -> str
def check_treasure(state: GameState, key: str) -> dict
def give_up(state: GameState) -> dict
def ask_human(state: GameState, question: str) -> str
"""

import os
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass

import pytest


@dataclass
class GameState:
    """Minimal GameState for testing."""
    treasure_hunt_root: Path
    current_dir: Path
    treasure_key: str
    game_over: bool = False
    success: bool | None = None


class TestGameTools:
    """Test the game tool functions."""

    @pytest.fixture
    def temp_hunt(self):
        """Create a temporary treasure hunt directory."""
        temp_dir = tempfile.mkdtemp()
        hunt_root = Path(temp_dir) / "hunt"
        hunt_root.mkdir()

        # Create some test structure
        (hunt_root / "start.txt").write_text("Welcome!")
        (hunt_root / "subdir").mkdir()
        (hunt_root / "subdir" / "file1.txt").write_text("Content 1")
        (hunt_root / "subdir" / "nested").mkdir()
        (hunt_root / "subdir" / "nested" / "file2.txt").write_text("Content 2")

        yield hunt_root

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def game_state(self, temp_hunt):
        """Create a game state for testing."""
        return GameState(
            treasure_hunt_root=temp_hunt,
            current_dir=temp_hunt,
            treasure_key="SECRET123"
        )

    def test_ls_current_directory(self, game_state):
        """
        Test ls lists current directory.

        Properties:
        - Returns list of files and directories
        - Includes both files and directories
        - Does not show absolute paths
        """
        from treasure_hunt_agent.game_tools import ls

        result = ls(game_state, ".")

        assert "start.txt" in result
        assert "subdir" in result
        assert isinstance(result, str)

    def test_ls_subdirectory(self, game_state):
        """
        Test ls can list subdirectories.

        Properties:
        - Can list relative subdirectory
        - Shows contents of that directory
        """
        from treasure_hunt_agent.game_tools import ls

        result = ls(game_state, "subdir")

        assert "file1.txt" in result
        assert "nested" in result

    def test_ls_rejects_escape_attempt(self, game_state):
        """
        Test ls rejects paths that escape hunt root.

        Properties:
        - Detects ../ attempts to escape
        - Returns error message
        - Does not expose information outside hunt
        """
        from treasure_hunt_agent.game_tools import ls

        result = ls(game_state, "../..")

        assert "error" in result.lower() or "invalid" in result.lower()
        assert "root" in result.lower() or "boundary" in result.lower()

    def test_ls_missing_directory(self, game_state):
        """
        Test ls handles missing directory.

        Properties:
        - Returns error message
        - Does not crash
        """
        from treasure_hunt_agent.game_tools import ls

        result = ls(game_state, "nonexistent")

        assert "error" in result.lower() or "not found" in result.lower()

    def test_cd_to_subdirectory(self, game_state):
        """
        Test cd changes to subdirectory.

        Properties:
        - Updates current_dir in state
        - current_dir stays within hunt root
        - Returns confirmation message
        """
        from treasure_hunt_agent.game_tools import cd

        result = cd(game_state, "subdir")

        assert game_state.current_dir == game_state.treasure_hunt_root / "subdir"
        assert "subdir" in result.lower()

    def test_cd_parent_directory_within_bounds(self, game_state):
        """
        Test cd can go to parent directory if within bounds.

        Properties:
        - Allows ../ if result is within hunt root
        - Updates current_dir correctly
        """
        from treasure_hunt_agent.game_tools import cd

        # First go to subdir
        game_state.current_dir = game_state.treasure_hunt_root / "subdir" / "nested"

        # Then go back up
        result = cd(game_state, "..")

        assert game_state.current_dir == game_state.treasure_hunt_root / "subdir"

    def test_cd_rejects_escape_attempt(self, game_state):
        """
        Test cd rejects attempts to escape hunt root.

        Properties:
        - Detects paths that would escape
        - Does not modify current_dir
        - Returns error message
        """
        from treasure_hunt_agent.game_tools import cd

        original_dir = game_state.current_dir

        result = cd(game_state, "../../..")

        assert game_state.current_dir == original_dir
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_cd_missing_directory(self, game_state):
        """
        Test cd handles missing directory.

        Properties:
        - Returns error message
        - Does not modify current_dir
        """
        from treasure_hunt_agent.game_tools import cd

        original_dir = game_state.current_dir

        result = cd(game_state, "nonexistent")

        assert game_state.current_dir == original_dir
        assert "error" in result.lower() or "not found" in result.lower()

    def test_cat_reads_file(self, game_state):
        """
        Test cat reads file contents.

        Properties:
        - Returns file contents
        - Works with relative paths
        """
        from treasure_hunt_agent.game_tools import cat

        result = cat(game_state, "start.txt")

        assert result == "Welcome!"

    def test_cat_reads_file_in_subdirectory(self, game_state):
        """
        Test cat can read files in subdirectories.

        Properties:
        - Resolves relative paths correctly
        - Returns file contents
        """
        from treasure_hunt_agent.game_tools import cat

        result = cat(game_state, "subdir/file1.txt")

        assert result == "Content 1"

    def test_cat_from_different_current_dir(self, game_state):
        """
        Test cat works when current_dir is not root.

        Properties:
        - Resolves paths relative to current_dir
        - Can use ../ to go up
        """
        from treasure_hunt_agent.game_tools import cat

        game_state.current_dir = game_state.treasure_hunt_root / "subdir"

        result = cat(game_state, "file1.txt")
        assert result == "Content 1"

        result = cat(game_state, "../start.txt")
        assert result == "Welcome!"

    def test_cat_rejects_escape_attempt(self, game_state):
        """
        Test cat rejects paths that escape hunt root.

        Properties:
        - Detects escape attempts
        - Returns error message
        - Does not read files outside hunt
        """
        from treasure_hunt_agent.game_tools import cat

        result = cat(game_state, "../../../etc/passwd")

        assert "error" in result.lower() or "invalid" in result.lower()

    def test_cat_missing_file(self, game_state):
        """
        Test cat handles missing file.

        Properties:
        - Returns error message
        - Does not crash
        """
        from treasure_hunt_agent.game_tools import cat

        result = cat(game_state, "nonexistent.txt")

        assert "error" in result.lower() or "not found" in result.lower()

    def test_cat_directory_instead_of_file(self, game_state):
        """
        Test cat handles directory instead of file.

        Properties:
        - Returns error message
        - Indicates it's a directory not a file
        """
        from treasure_hunt_agent.game_tools import cat

        result = cat(game_state, "subdir")

        assert "error" in result.lower() or "directory" in result.lower()

    def test_pwd_returns_current_directory(self, game_state):
        """
        Test pwd returns current directory.

        Properties:
        - Returns path relative to hunt root
        - Shows "." when at root
        """
        from treasure_hunt_agent.game_tools import pwd

        result = pwd(game_state)

        assert result == "." or result == "/"

    def test_pwd_in_subdirectory(self, game_state):
        """
        Test pwd returns correct path in subdirectory.

        Properties:
        - Returns relative path
        - Does not include hunt root in output
        """
        from treasure_hunt_agent.game_tools import pwd

        game_state.current_dir = game_state.treasure_hunt_root / "subdir" / "nested"

        result = pwd(game_state)

        assert "subdir/nested" in result or "subdir\\nested" in result

    def test_check_treasure_correct_key(self, game_state):
        """
        Test check_treasure with correct key.

        Properties:
        - Returns dict with correct=True
        - Sets game_over=True
        - Sets success=True
        """
        from treasure_hunt_agent.game_tools import check_treasure

        result = check_treasure(game_state, "SECRET123")

        assert isinstance(result, dict)
        assert result["correct"] is True
        assert game_state.game_over is True
        assert game_state.success is True

    def test_check_treasure_wrong_key(self, game_state):
        """
        Test check_treasure with wrong key.

        Properties:
        - Returns dict with correct=False
        - Does not set game_over
        - Does not set success
        """
        from treasure_hunt_agent.game_tools import check_treasure

        result = check_treasure(game_state, "WRONG")

        assert isinstance(result, dict)
        assert result["correct"] is False
        assert game_state.game_over is False
        assert game_state.success is None

    def test_give_up(self, game_state):
        """
        Test give_up ends game.

        Properties:
        - Returns dict with message
        - Sets game_over=True
        - Sets success=False
        """
        from treasure_hunt_agent.game_tools import give_up

        result = give_up(game_state)

        assert isinstance(result, dict)
        assert "message" in result
        assert game_state.game_over is True
        assert game_state.success is False

    def test_ask_human(self, game_state):
        """
        Test ask_human placeholder.

        Properties:
        - Returns string indicating human input needed
        - Contains the question
        """
        from treasure_hunt_agent.game_tools import ask_human

        result = ask_human(game_state, "Where should I look?")

        assert isinstance(result, str)
        assert "Where should I look?" in result

    def test_path_validation_with_absolute_paths(self, game_state):
        """
        Test that absolute paths are rejected.

        Properties:
        - ls rejects absolute paths
        - cd rejects absolute paths
        - cat rejects absolute paths
        """
        from treasure_hunt_agent.game_tools import ls, cd, cat

        abs_path = "/etc/passwd"

        ls_result = ls(game_state, abs_path)
        assert "error" in ls_result.lower() or "invalid" in ls_result.lower()

        original_dir = game_state.current_dir
        cd_result = cd(game_state, abs_path)
        assert game_state.current_dir == original_dir
        assert "error" in cd_result.lower() or "invalid" in cd_result.lower()

        cat_result = cat(game_state, abs_path)
        assert "error" in cat_result.lower() or "invalid" in cat_result.lower()
