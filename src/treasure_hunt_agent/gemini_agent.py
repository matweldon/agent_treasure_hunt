"""
Gemini Agent implementation using google-generativeai SDK.

This agent manages conversation with Gemini models, handles tool calling,
and maintains conversation history.

Example:
    >>> tools = [{"name": "ls", "description": "List files", ...}]
    >>> agent = GeminiAgent("gemini-1.5-flash", "You are helpful", tools)
    >>> response = agent.step("Hello")
    >>> print(response.text)
    Hello! How can I help you?
"""

from dataclasses import dataclass, field
from typing import Any
import uuid

import google.generativeai as genai


@dataclass
class ToolCall:
    """
    Represents a tool call requested by the agent.

    Attributes
    ----------
    name : str
        Name of the tool to call
    arguments : dict
        Arguments to pass to the tool
    id : str
        Unique identifier for this tool call
    """

    name: str
    arguments: dict
    id: str = field(default_factory=lambda: f"call_{uuid.uuid4().hex[:8]}")


@dataclass
class ToolResult:
    """
    Represents the result of a tool execution.

    Attributes
    ----------
    tool_call_id : str
        ID of the tool call this is responding to
    name : str
        Name of the tool that was called
    result : str | dict
        The result from the tool execution
    """

    tool_call_id: str
    name: str
    result: str | dict


@dataclass
class AgentResponse:
    """
    Response from an agent step.

    Attributes
    ----------
    text : str | None
        Text response from the agent (if any)
    tool_calls : list[ToolCall] | None
        Tool calls requested by the agent (if any)
    finish_reason : str
        Why the response ended: "STOP", "FUNCTION_CALL", "MAX_TOKENS", etc.
    usage : dict
        Token usage statistics with keys: prompt_tokens, completion_tokens, total_tokens
    """

    text: str | None
    tool_calls: list[ToolCall] | None
    finish_reason: str
    usage: dict


class GeminiAgent:
    """
    Agent that uses Gemini models via google-generativeai SDK.

    The agent maintains conversation history, handles tool calling,
    and provides a clean interface for the game loop.

    Parameters
    ----------
    model_name : str
        Name of the Gemini model to use (e.g., "gemini-1.5-flash")
    system_instructions : str
        System instructions/prompt for the agent
    tools : list[dict]
        List of tool definitions in Gemini format

    Examples
    --------
    >>> tools = [{
    ...     "name": "get_weather",
    ...     "description": "Get weather for a location",
    ...     "parameters": {...}
    ... }]
    >>> agent = GeminiAgent("gemini-1.5-flash", "You are helpful", tools)
    >>> response = agent.step("What's the weather?")
    """

    def __init__(
        self,
        model_name: str,
        system_instructions: str,
        tools: list[dict],
        temperature: float = 1.0,
        api_key: str | None = None,
    ):
        """
        Initialize the Gemini agent.

        Parameters
        ----------
        model_name : str
            Gemini model name
        system_instructions : str
            System instructions for the agent
        tools : list[dict]
            Tool definitions
        temperature : float
            Sampling temperature (0.0 to 2.0)
        api_key : str | None
            Gemini API key (if None, uses GOOGLE_API_KEY env var)
        """
        self.model_name = model_name
        self.system_instructions = system_instructions
        self.tools = tools
        self.temperature = temperature

        # Configure API
        if api_key:
            genai.configure(api_key=api_key)

        # Convert tools to Gemini format
        gemini_tools = self._convert_tools_to_gemini_format(tools) if tools else None

        # Create model
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instructions,
            tools=gemini_tools,
        )

        # Initialize chat
        self.chat = None
        self._reset_chat()

    def _convert_tools_to_gemini_format(self, tools: list[dict]) -> list[Any]:
        """Convert tool definitions to Gemini's expected format."""
        # Gemini expects tools in a specific format
        # For now, we'll pass them as-is and let the SDK handle it
        # The SDK expects a list of function declarations
        from google.generativeai.types import FunctionDeclaration, Tool

        function_declarations = []
        for tool in tools:
            func_decl = FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=tool.get("parameters", {}),
            )
            function_declarations.append(func_decl)

        return [Tool(function_declarations=function_declarations)]

    def _reset_chat(self):
        """Reset the chat session."""
        self.chat = self.model.start_chat(
            history=[],
        )

    def step(
        self, game_input: str | list[ToolResult] | None = None
    ) -> AgentResponse:
        """
        Perform one step of agent execution.

        Parameters
        ----------
        game_input : str | list[ToolResult] | None
            Input to the agent:
            - str: Initial message, user input, or game announcement
            - list[ToolResult]: Results from tool calls made in previous turn
            - None: Continue from previous state

        Returns
        -------
        AgentResponse
            The agent's response including text and/or tool calls

        Examples
        --------
        >>> response = agent.step("You are at the root directory")
        >>> if response.tool_calls:
        ...     # Execute tools and feed results back
        ...     results = [execute_tool(tc) for tc in response.tool_calls]
        ...     next_response = agent.step(results)
        """
        # Prepare the message to send
        if game_input is None:
            # Continue conversation (shouldn't normally happen in our design)
            message = ""
        elif isinstance(game_input, str):
            # Text message from game
            message = game_input
        elif isinstance(game_input, list):
            # Tool results - need to convert to Gemini format
            message = self._tool_results_to_message(game_input)
        else:
            raise ValueError(f"Invalid game_input type: {type(game_input)}")

        # Send message to LLM
        response = self.chat.send_message(message)

        # Parse response
        return self._parse_response(response)

    def _tool_results_to_message(self, tool_results: list[ToolResult]) -> Any:
        """
        Convert tool results to Gemini message format.

        Parameters
        ----------
        tool_results : list[ToolResult]
            Results from tool executions

        Returns
        -------
        Any
            Message in Gemini's expected format for tool results
        """
        from google.generativeai.protos import Content, Part, FunctionResponse

        # Create function response parts
        parts = []
        for result in tool_results:
            # Convert result to dict if it's a string
            result_dict = result.result if isinstance(result.result, dict) else {"output": result.result}

            func_response = FunctionResponse(
                name=result.name,
                response=result_dict,
            )
            parts.append(Part(function_response=func_response))

        # Return the content with function responses
        return Content(parts=parts, role="user")

    def _parse_response(self, response: Any) -> AgentResponse:
        """
        Parse Gemini API response into AgentResponse.

        Parameters
        ----------
        response : Any
            Raw response from Gemini API

        Returns
        -------
        AgentResponse
            Parsed response with text, tool calls, and metadata
        """
        # Extract text (if any)
        # Note: response.text will raise an error if the response only contains function calls
        text = None
        try:
            if hasattr(response, "text"):
                text = response.text
        except ValueError:
            # Response contains only function calls, no text
            text = None

        # Extract tool calls (if any)
        tool_calls = None
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            parts = candidate.content.parts

            # Check for function calls
            function_calls = []
            for part in parts:
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    tool_call = ToolCall(
                        name=fc.name,
                        arguments=dict(fc.args) if fc.args else {},
                    )
                    function_calls.append(tool_call)

            if function_calls:
                tool_calls = function_calls

        # Extract finish reason
        finish_reason = "STOP"
        if response.candidates and len(response.candidates) > 0:
            finish_reason = str(response.candidates[0].finish_reason)
            # Remove enum prefix if present
            if "." in finish_reason:
                finish_reason = finish_reason.split(".")[-1]

        # Extract usage metadata
        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage_meta = response.usage_metadata
            usage["prompt_tokens"] = getattr(usage_meta, "prompt_token_count", 0)
            usage["completion_tokens"] = getattr(
                usage_meta, "candidates_token_count", 0
            )
            usage["total_tokens"] = getattr(usage_meta, "total_token_count", 0)

        return AgentResponse(
            text=text,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
        )

    def get_history(self) -> list[dict]:
        """
        Get conversation history.

        Returns
        -------
        list[dict]
            Conversation history (format depends on Gemini SDK)

        Examples
        --------
        >>> agent.step("Hello")
        >>> history = agent.get_history()
        >>> len(history) > 0
        True
        """
        if self.chat and hasattr(self.chat, "history"):
            return list(self.chat.history)
        return []

    def reset(self):
        """
        Reset the agent's conversation history.

        Starts a fresh conversation while keeping the same configuration.

        Examples
        --------
        >>> agent.step("Message 1")
        >>> agent.step("Message 2")
        >>> len(agent.get_history()) > 0
        True
        >>> agent.reset()
        >>> len(agent.get_history())
        0
        """
        self._reset_chat()
