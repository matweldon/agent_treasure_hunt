"""
Tests for GeminiAgent.

Properties tested:
- Agent initializes with model name, system instructions, and tools
- step() accepts game_input (str, list[ToolResult], or None) and returns AgentResponse
- Agent handles text-only responses from LLM
- Agent handles tool call responses from LLM
- Agent accepts tool results and feeds them back to LLM
- Agent maintains conversation history
- Agent tracks token usage accurately
- Agent can be reset
- Agent returns appropriate finish_reason

Function signatures:
class GeminiAgent:
    def __init__(self, model_name: str, system_instructions: str, tools: list[dict])
    def step(self, game_input: str | list[ToolResult] | None = None) -> AgentResponse
    def get_history(self) -> list[dict]
    def reset(self) -> None

@dataclass
class AgentResponse:
    text: str | None
    tool_calls: list[ToolCall] | None
    finish_reason: str
    usage: dict

@dataclass
class ToolCall:
    name: str
    arguments: dict
    id: str

@dataclass
class ToolResult:
    tool_call_id: str
    name: str
    result: str | dict
"""

import os
from unittest.mock import Mock, MagicMock, patch

import pytest


class TestGeminiAgent:
    """Test the GeminiAgent class."""

    @pytest.fixture
    def sample_tools(self):
        """Sample tool definitions for testing."""
        return [
            {
                "name": "ls",
                "description": "List files and directories",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to list (defaults to current directory)"
                        }
                    }
                }
            },
            {
                "name": "cat",
                "description": "Read file contents",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        ]

    @pytest.fixture(autouse=True)
    def mock_genai(self):
        """Mock the google.generativeai module."""
        with patch('treasure_hunt_agent.gemini_agent.genai.GenerativeModel') as mock_model, \
             patch('treasure_hunt_agent.gemini_agent.genai.configure') as mock_configure, \
             patch('treasure_hunt_agent.gemini_agent.FunctionDeclaration') as mock_func_decl, \
             patch('treasure_hunt_agent.gemini_agent.Tool') as mock_tool:
            # Set up mock model and chat
            mock_chat = Mock()
            mock_chat.history = []
            mock_model.return_value.start_chat.return_value = mock_chat

            # Mock tool construction
            mock_tool.return_value = Mock()

            yield {
                'GenerativeModel': mock_model,
                'configure': mock_configure,
                'chat': mock_chat,
                'FunctionDeclaration': mock_func_decl,
                'Tool': mock_tool
            }

    def test_agent_initialization(self, sample_tools, mock_genai):
        """
        Test that agent initializes correctly.

        Properties:
        - Stores model_name
        - Stores system_instructions
        - Stores tools
        - Initializes empty conversation history
        - Creates GenerativeModel instance
        """
        from treasure_hunt_agent.gemini_agent import GeminiAgent

        agent = GeminiAgent(
            model_name="gemini-1.5-flash",
            system_instructions="You are a helpful agent",
            tools=sample_tools,
            api_key="test_key"  # Prevent trying to read env
        )

        # Should have created a model
        mock_genai['GenerativeModel'].assert_called_once()

        # Should have empty history initially
        history = agent.get_history()
        assert isinstance(history, list)
        assert len(history) == 0

    def test_step_with_initial_message(self, sample_tools, mock_genai):
        """
        Test agent step with initial game message.

        Properties:
        - Accepts string game_input
        - Calls LLM with input
        - Returns AgentResponse
        - Updates conversation history
        """
        from treasure_hunt_agent.gemini_agent import GeminiAgent

        # Mock LLM response (text only, no tool calls)
        mock_response = Mock()
        mock_response.text = "I'll start exploring"
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].finish_reason = "STOP"
        mock_response.candidates[0].content.parts = [Mock(text="I'll start exploring")]
        mock_response.usage_metadata = Mock(
            prompt_token_count=10,
            candidates_token_count=5,
            total_token_count=15
        )

        mock_chat = Mock()
        mock_chat.send_message.return_value = mock_response
        mock_genai.GenerativeModel.return_value.start_chat.return_value = mock_chat

        agent = GeminiAgent(
            model_name="gemini-1.5-flash",
            system_instructions="You are a helpful agent",
            tools=sample_tools
        )

        response = agent.step("You are at the root. Start file is start.txt")

        assert response.text == "I'll start exploring"
        assert response.tool_calls is None or len(response.tool_calls) == 0
        assert response.finish_reason == "STOP"
        assert response.usage["total_tokens"] == 15

    def test_step_with_tool_calls(self, sample_tools, mock_genai):
        """
        Test agent step that requests tool calls.

        Properties:
        - LLM response contains tool calls
        - AgentResponse.tool_calls is populated
        - Each tool call has name, arguments, id
        - finish_reason indicates tool calls
        """
        from treasure_hunt_agent.gemini_agent import GeminiAgent, ToolCall

        # Mock LLM response with tool calls
        mock_function_call = Mock()
        mock_function_call.name = "ls"
        mock_function_call.args = {"path": "."}

        mock_part = Mock()
        mock_part.function_call = mock_function_call
        mock_part.text = None

        mock_response = Mock()
        mock_response.text = None
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].finish_reason = "FUNCTION_CALL"
        mock_response.candidates[0].content.parts = [mock_part]
        mock_response.usage_metadata = Mock(
            prompt_token_count=10,
            candidates_token_count=5,
            total_token_count=15
        )

        mock_chat = Mock()
        mock_chat.send_message.return_value = mock_response
        mock_genai.GenerativeModel.return_value.start_chat.return_value = mock_chat

        agent = GeminiAgent(
            model_name="gemini-1.5-flash",
            system_instructions="You are a helpful agent",
            tools=sample_tools
        )

        response = agent.step("Explore the directory")

        assert response.tool_calls is not None
        assert len(response.tool_calls) > 0
        assert isinstance(response.tool_calls[0], ToolCall)
        assert response.tool_calls[0].name == "ls"
        assert response.tool_calls[0].arguments == {"path": "."}
        assert response.finish_reason == "FUNCTION_CALL"

    def test_step_with_tool_results(self, sample_tools, mock_genai):
        """
        Test agent step with tool results as input.

        Properties:
        - Accepts list[ToolResult] as game_input
        - Feeds results back to LLM correctly
        - LLM can respond with text or more tool calls
        """
        from treasure_hunt_agent.gemini_agent import GeminiAgent, ToolResult

        # Mock LLM response after receiving tool results
        mock_response = Mock()
        mock_response.text = "I see the start.txt file"
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].finish_reason = "STOP"
        mock_response.candidates[0].content.parts = [Mock(text="I see the start.txt file")]
        mock_response.usage_metadata = Mock(
            prompt_token_count=15,
            candidates_token_count=10,
            total_token_count=25
        )

        mock_chat = Mock()
        mock_chat.send_message.return_value = mock_response
        mock_genai.GenerativeModel.return_value.start_chat.return_value = mock_chat

        agent = GeminiAgent(
            model_name="gemini-1.5-flash",
            system_instructions="You are a helpful agent",
            tools=sample_tools
        )

        # Simulate tool results
        tool_results = [
            ToolResult(
                tool_call_id="call_123",
                name="ls",
                result="start.txt\ndocs/\n"
            )
        ]

        response = agent.step(tool_results)

        assert response.text == "I see the start.txt file"
        assert response.finish_reason == "STOP"

    def test_conversation_history(self, sample_tools, mock_genai):
        """
        Test that conversation history is maintained correctly.

        Properties:
        - History starts empty
        - Each step adds to history
        - History includes user messages, assistant messages, tool calls, tool results
        - get_history() returns the history
        """
        from treasure_hunt_agent.gemini_agent import GeminiAgent

        mock_response = Mock()
        mock_response.text = "Response"
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].finish_reason = "STOP"
        mock_response.candidates[0].content.parts = [Mock(text="Response")]
        mock_response.usage_metadata = Mock(
            prompt_token_count=10,
            candidates_token_count=5,
            total_token_count=15
        )

        mock_chat = Mock()
        mock_chat.send_message.return_value = mock_response
        mock_chat.history = []
        mock_genai.GenerativeModel.return_value.start_chat.return_value = mock_chat

        agent = GeminiAgent(
            model_name="gemini-1.5-flash",
            system_instructions="You are a helpful agent",
            tools=sample_tools
        )

        # Initial state
        assert len(agent.get_history()) == 0

        # After first step
        agent.step("Hello")
        history = agent.get_history()
        assert len(history) > 0

    def test_token_usage_tracking(self, sample_tools, mock_genai):
        """
        Test that token usage is tracked correctly.

        Properties:
        - Each response includes usage metadata
        - Usage contains prompt_tokens, completion_tokens, total_tokens
        - Token counts are accurate
        """
        from treasure_hunt_agent.gemini_agent import GeminiAgent

        mock_response = Mock()
        mock_response.text = "Response"
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].finish_reason = "STOP"
        mock_response.candidates[0].content.parts = [Mock(text="Response")]
        mock_response.usage_metadata = Mock(
            prompt_token_count=100,
            candidates_token_count=50,
            total_token_count=150
        )

        mock_chat = Mock()
        mock_chat.send_message.return_value = mock_response
        mock_genai.GenerativeModel.return_value.start_chat.return_value = mock_chat

        agent = GeminiAgent(
            model_name="gemini-1.5-flash",
            system_instructions="You are a helpful agent",
            tools=sample_tools
        )

        response = agent.step("Test message")

        assert "prompt_tokens" in response.usage
        assert "completion_tokens" in response.usage
        assert "total_tokens" in response.usage
        assert response.usage["prompt_tokens"] == 100
        assert response.usage["completion_tokens"] == 50
        assert response.usage["total_tokens"] == 150

    def test_reset(self, sample_tools, mock_genai):
        """
        Test that agent can be reset.

        Properties:
        - reset() clears conversation history
        - Agent can continue after reset
        - New conversation starts fresh
        """
        from treasure_hunt_agent.gemini_agent import GeminiAgent

        mock_response = Mock()
        mock_response.text = "Response"
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].finish_reason = "STOP"
        mock_response.candidates[0].content.parts = [Mock(text="Response")]
        mock_response.usage_metadata = Mock(
            prompt_token_count=10,
            candidates_token_count=5,
            total_token_count=15
        )

        mock_chat = Mock()
        mock_chat.send_message.return_value = mock_response
        mock_chat.history = []
        mock_genai.GenerativeModel.return_value.start_chat.return_value = mock_chat

        agent = GeminiAgent(
            model_name="gemini-1.5-flash",
            system_instructions="You are a helpful agent",
            tools=sample_tools
        )

        # Build up some history
        agent.step("Message 1")
        agent.step("Message 2")
        assert len(agent.get_history()) > 0

        # Reset
        agent.reset()
        assert len(agent.get_history()) == 0

        # Can continue after reset
        response = agent.step("New conversation")
        assert response.text == "Response"

    def test_multiple_tool_calls_in_response(self, sample_tools, mock_genai):
        """
        Test agent response with multiple tool calls.

        Properties:
        - LLM can return multiple tool calls in one response
        - All tool calls are captured
        - Tool calls maintain order
        """
        from treasure_hunt_agent.gemini_agent import GeminiAgent

        # Mock LLM response with multiple tool calls
        mock_fc1 = Mock()
        mock_fc1.name = "ls"
        mock_fc1.args = {"path": "."}

        mock_fc2 = Mock()
        mock_fc2.name = "cat"
        mock_fc2.args = {"file_path": "start.txt"}

        mock_part1 = Mock()
        mock_part1.function_call = mock_fc1
        mock_part1.text = None

        mock_part2 = Mock()
        mock_part2.function_call = mock_fc2
        mock_part2.text = None

        mock_response = Mock()
        mock_response.text = None
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].finish_reason = "FUNCTION_CALL"
        mock_response.candidates[0].content.parts = [mock_part1, mock_part2]
        mock_response.usage_metadata = Mock(
            prompt_token_count=10,
            candidates_token_count=5,
            total_token_count=15
        )

        mock_chat = Mock()
        mock_chat.send_message.return_value = mock_response
        mock_genai.GenerativeModel.return_value.start_chat.return_value = mock_chat

        agent = GeminiAgent(
            model_name="gemini-1.5-flash",
            system_instructions="You are a helpful agent",
            tools=sample_tools
        )

        response = agent.step("List and read file")

        assert response.tool_calls is not None
        assert len(response.tool_calls) == 2
        assert response.tool_calls[0].name == "ls"
        assert response.tool_calls[1].name == "cat"
