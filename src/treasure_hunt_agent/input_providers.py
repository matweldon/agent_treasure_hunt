"""
Input providers for treasure hunt game.

Defines the InputProvider protocol and implementations for different
input sources (CLI, automatic responses for testing, etc.).

Example:
    >>> provider = CliInputProvider()
    >>> response = provider.get_human_input("What should I do next?")
    Agent asks: What should I do next?
    Your response: check the hidden folder
    >>> response
    'check the hidden folder'
"""

from typing import Iterator, Protocol


class InputProvider(Protocol):
    """
    Protocol for providing human input to the game.

    Implementations must provide a get_human_input method that
    takes a question and returns a response string.
    """

    def get_human_input(self, question: str) -> str:
        """
        Get input from a human in response to a question.

        Parameters
        ----------
        question : str
            Question to ask the human

        Returns
        -------
        str
            Human's response
        """
        ...


class CliInputProvider:
    """
    Input provider that reads from stdin.

    Uses standard input() for CLI interaction.

    Examples
    --------
    >>> provider = CliInputProvider()
    >>> response = provider.get_human_input("Where should I look?")
    """

    def get_human_input(self, question: str) -> str:
        """Get input from stdin."""
        print(f"\nAgent asks: {question}")
        return input("Your response: ").strip()


class AutoInputProvider:
    """
    Input provider that returns pre-configured responses.

    Useful for testing or automated runs where human input
    should be simulated.

    Parameters
    ----------
    responses : list[str]
        List of responses to return in order
    default : str
        Default response when responses are exhausted

    Examples
    --------
    >>> provider = AutoInputProvider(["look in basement", "check the safe"])
    >>> provider.get_human_input("Where should I look?")
    'look in basement'
    >>> provider.get_human_input("What next?")
    'check the safe'
    >>> provider.get_human_input("Any ideas?")
    '[No response available]'
    """

    def __init__(
        self, responses: list[str], default: str = "[No response available]"
    ):
        """Initialize with list of canned responses."""
        self._responses: Iterator[str] = iter(responses)
        self._default = default

    def get_human_input(self, question: str) -> str:
        """Return next canned response or default."""
        return next(self._responses, self._default)


class CallbackInputProvider:
    """
    Input provider that calls a callback function.

    Useful for integrating with external systems (web UI, API, etc.).

    Parameters
    ----------
    callback : callable
        Function that takes a question string and returns a response string

    Examples
    --------
    >>> def my_callback(q: str) -> str:
    ...     return f"Response to: {q}"
    >>> provider = CallbackInputProvider(my_callback)
    >>> provider.get_human_input("test")
    'Response to: test'
    """

    def __init__(self, callback: callable):
        """Initialize with callback function."""
        self._callback = callback

    def get_human_input(self, question: str) -> str:
        """Call the callback with the question."""
        return self._callback(question)
