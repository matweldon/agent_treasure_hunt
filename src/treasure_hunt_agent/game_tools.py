"""
Game tools for the treasure hunt.

Provides filesystem navigation tools (ls, cd, cat, pwd) with path validation
to keep the agent within the treasure hunt boundaries, plus control tools
(check_treasure, give_up, ask_human).

Example:
    >>> state = GameState(treasure_hunt_root=Path("/hunt"), current_dir=Path("/hunt"))
    >>> ls(state, ".")
    'start.txt\\nsubdir/\\n'
    >>> cd(state, "subdir")
    'Changed directory to: subdir'
"""

import os
from pathlib import Path
from typing import Any


def _validate_path(
    state: Any, path: str, must_exist: bool = True, must_be_file: bool = False
) -> Path | str:
    """
    Validate that a path stays within treasure_hunt_root.

    Parameters
    ----------
    state : GameState
        Current game state with treasure_hunt_root and current_dir
    path : str
        Path to validate (relative or absolute)
    must_exist : bool
        If True, path must exist
    must_be_file : bool
        If True, path must be a file (not directory)

    Returns
    -------
    Path | str
        Resolved path if valid, error message string if invalid

    Examples
    --------
    >>> state = GameState(...)
    >>> result = _validate_path(state, "subdir/file.txt")
    >>> isinstance(result, Path)
    True
    """
    # Reject absolute paths
    if os.path.isabs(path):
        return "Error: Absolute paths are not allowed"

    # Resolve path relative to current directory
    try:
        resolved = (state.current_dir / path).resolve()
    except Exception as e:
        return f"Error: Invalid path: {e}"

    # Check if path escapes hunt root
    try:
        resolved.relative_to(state.treasure_hunt_root)
    except ValueError:
        return "Error: Path is outside treasure hunt boundary"

    # Check existence
    if must_exist and not resolved.exists():
        return f"Error: Path does not exist: {path}"

    # Check if file when required
    if must_be_file and resolved.exists() and not resolved.is_file():
        return f"Error: Path is a directory, not a file: {path}"

    return resolved


def ls(state: Any, path: str = ".") -> str:
    """
    List files and directories at path.

    Parameters
    ----------
    state : GameState
        Current game state
    path : str
        Path to list (relative to current_dir), defaults to "."

    Returns
    -------
    str
        Formatted list of files and directories, or error message

    Examples
    --------
    >>> ls(state, ".")
    'file1.txt\\nfile2.txt\\nsubdir/\\n'
    """
    resolved = _validate_path(state, path, must_exist=True)

    if isinstance(resolved, str):
        return resolved

    if not resolved.is_dir():
        return f"Error: Not a directory: {path}"

    try:
        items = []
        for item in sorted(resolved.iterdir()):
            name = item.name
            if item.is_dir():
                name += "/"
            items.append(name)

        if not items:
            return "(empty directory)"

        return "\\n".join(items)
    except PermissionError:
        return f"Error: Permission denied: {path}"
    except Exception as e:
        return f"Error: {e}"


def cd(state: Any, path: str) -> str:
    """
    Change current working directory.

    Parameters
    ----------
    state : GameState
        Current game state (modified in place)
    path : str
        Path to change to (relative to current_dir)

    Returns
    -------
    str
        Confirmation message or error message

    Examples
    --------
    >>> cd(state, "subdir")
    'Changed directory to: subdir'
    """
    resolved = _validate_path(state, path, must_exist=True)

    if isinstance(resolved, str):
        return resolved

    if not resolved.is_dir():
        return f"Error: Not a directory: {path}"

    # Update state
    state.current_dir = resolved

    # Return relative path for confirmation
    try:
        rel_path = resolved.relative_to(state.treasure_hunt_root)
        if str(rel_path) == ".":
            return "Changed directory to: / (hunt root)"
        return f"Changed directory to: {rel_path}"
    except ValueError:
        return "Changed directory"


def cat(state: Any, file_path: str) -> str:
    """
    Read contents of a file.

    Parameters
    ----------
    state : GameState
        Current game state
    file_path : str
        Path to file (relative to current_dir)

    Returns
    -------
    str
        File contents or error message

    Examples
    --------
    >>> cat(state, "start.txt")
    'Welcome to the treasure hunt!'
    """
    resolved = _validate_path(state, file_path, must_exist=True, must_be_file=True)

    if isinstance(resolved, str):
        return resolved

    try:
        return resolved.read_text()
    except UnicodeDecodeError:
        return f"Error: File is not a text file: {file_path}"
    except PermissionError:
        return f"Error: Permission denied: {file_path}"
    except Exception as e:
        return f"Error: {e}"


def pwd(state: Any) -> str:
    """
    Print current working directory.

    Parameters
    ----------
    state : GameState
        Current game state

    Returns
    -------
    str
        Current directory path relative to hunt root

    Examples
    --------
    >>> pwd(state)
    'subdir/nested'
    """
    try:
        rel_path = state.current_dir.relative_to(state.treasure_hunt_root)
        if str(rel_path) == ".":
            return "/"
        return str(rel_path)
    except ValueError:
        return "Error: Current directory is outside hunt root"


def check_treasure(state: Any, key: str) -> dict[str, bool | str]:
    """
    Check if the provided key is the treasure key.

    Parameters
    ----------
    state : GameState
        Current game state (modified if key is correct)
    key : str
        Key to check

    Returns
    -------
    dict
        {"correct": bool, "message": str}
        If correct, sets game_over=True and success=True

    Examples
    --------
    >>> check_treasure(state, "SECRET123")
    {'correct': True, 'message': 'Correct! You found the treasure!'}
    """
    if key == state.treasure_key:
        state.game_over = True
        state.success = True
        return {
            "correct": True,
            "message": "Correct! You found the treasure!"
        }
    else:
        return {
            "correct": False,
            "message": "Incorrect key. Keep searching!"
        }


def give_up(state: Any) -> dict[str, str]:
    """
    Give up and end the game.

    Parameters
    ----------
    state : GameState
        Current game state (modified)

    Returns
    -------
    dict
        {"message": str}
        Sets game_over=True and success=False

    Examples
    --------
    >>> give_up(state)
    {'message': 'Game ended. Agent gave up.'}
    """
    state.game_over = True
    state.success = False
    return {
        "message": "Game ended. Agent gave up."
    }


def ask_human(state: Any, question: str) -> str:
    """
    Ask the human operator for help.

    Parameters
    ----------
    state : GameState
        Current game state
    question : str
        Question to ask the human

    Returns
    -------
    str
        Placeholder response (in real implementation, would pause for human input)

    Examples
    --------
    >>> ask_human(state, "Where should I start?")
    '[Human input needed] Question: Where should I start?'
    """
    # In a real implementation, this would pause the game loop
    # and wait for human input. For now, return a placeholder.
    return f"[Human input needed] Question: {question}"


# Tool definitions for Gemini API
TOOL_DEFINITIONS = [
    {
        "name": "ls",
        "description": "List files and directories at the specified path",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to list (relative to current directory). Defaults to current directory."
                }
            }
        }
    },
    {
        "name": "cd",
        "description": "Change current working directory to the specified path",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to change to (relative to current directory)"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "cat",
        "description": "Read and return the contents of a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read (relative to current directory)"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "pwd",
        "description": "Print the current working directory path",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "check_treasure",
        "description": "Check if a key is the correct treasure key. If correct, the game ends successfully.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The treasure key to check"
                }
            },
            "required": ["key"]
        }
    },
    {
        "name": "give_up",
        "description": "Give up and end the game as a failure",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "ask_human",
        "description": "Ask the human operator for help or guidance",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Question to ask the human"
                }
            },
            "required": ["question"]
        }
    }
]
