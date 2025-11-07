"""
Tests for TreasureHuntGame loop.

Properties tested:
- Game initializes correctly with hunt path and agent
- Game runs the loop: agent step -> tool execution -> feed results back
- Game executes tools sequentially
- Game tracks turns and tokens
- Game ends on correct treasure key (success=True)
- Game ends on give_up (success=False)
- Game ends on max_turns (success=False)
- Game ends on max_tokens (success=False)
- Game logs all tool calls
- Game returns proper GameResult

Function signature:
class TreasureHuntGame:
    def __init__(self, hunt_path: str, agent: Agent, max_turns: int = 50, max_tokens: int = 100000)
    def run(self) -> GameResult
    def get_state(self) -> GameState
    def get_logs(self) -> list[dict]

@dataclass
class GameResult:
    success: bool
    turns_taken: int
    treasure_key_found: str | None
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_time: float
    tool_calls: list[dict]
    final_state: GameState
    end_reason: str
    error: str | None
"""

import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass

import pytest


# Mock agent response classes
@dataclass
class MockToolCall:
    name: str
    arguments: dict
    id: str = "call_123"


@dataclass
class MockAgentResponse:
    text: str | None
    tool_calls: list[MockToolCall] | None
    finish_reason: str
    usage: dict


class TestTreasureHuntGame:
    """Test the TreasureHuntGame class."""

    @pytest.fixture
    def temp_hunt(self):
        """Create a simple treasure hunt."""
        from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt

        temp_dir = tempfile.mkdtemp()
        hunt_path = Path(temp_dir) / "hunt"

        result = generate_treasure_hunt(
            base_path=str(hunt_path),
            depth=3,
            seed=42
        )

        yield hunt_path, result

        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = Mock()
        agent.get_history = Mock(return_value=[])
        agent.reset = Mock()
        return agent

    def test_game_initialization(self, temp_hunt, mock_agent):
        """
        Test game initializes correctly.

        Properties:
        - Loads hunt configuration
        - Creates GameState with correct hunt root
        - Stores agent reference
        - Sets initial values (turns=0, game_over=False)
        """
        from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame

        hunt_path, hunt_result = temp_hunt

        game = TreasureHuntGame(
            hunt_path=str(hunt_path),
            agent=mock_agent,
            max_turns=50,
            max_tokens=10000
        )

        state = game.get_state()
        assert state.treasure_hunt_root == hunt_path
        assert state.current_dir == hunt_path
        assert state.turn_number == 0
        assert state.game_over is False
        assert state.treasure_key == hunt_result['treasure_key']

    def test_game_runs_agent_step(self, temp_hunt, mock_agent):
        """
        Test game calls agent.step() in the loop.

        Properties:
        - Calls agent.step() with initial message
        - Initial message includes start file name
        """
        from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame

        hunt_path, hunt_result = temp_hunt

        # Mock agent to return success immediately
        mock_agent.step = Mock(return_value=MockAgentResponse(
            text="I'll check the key",
            tool_calls=[MockToolCall(
                name="check_treasure",
                arguments={"key": hunt_result['treasure_key']}
            )],
            finish_reason="FUNCTION_CALL",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        ))

        game = TreasureHuntGame(str(hunt_path), mock_agent)
        result = game.run()

        # Should have called agent.step with initial message
        assert mock_agent.step.called
        first_call = mock_agent.step.call_args_list[0]
        initial_message = first_call[0][0]
        assert hunt_result['start_file'] in initial_message

    def test_game_executes_tools(self, temp_hunt, mock_agent):
        """
        Test game executes tool calls.

        Properties:
        - Executes tools based on agent's tool_calls
        - Feeds results back to agent
        - Logs tool calls
        """
        from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame

        hunt_path, hunt_result = temp_hunt

        # Agent makes ls call, then finds treasure
        call_count = 0

        def mock_step(game_input):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # First call: list directory
                return MockAgentResponse(
                    text="Let me list files",
                    tool_calls=[MockToolCall(name="ls", arguments={"path": "."})],
                    finish_reason="FUNCTION_CALL",
                    usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
                )
            else:
                # Second call: check treasure
                return MockAgentResponse(
                    text="Found it",
                    tool_calls=[MockToolCall(
                        name="check_treasure",
                        arguments={"key": hunt_result['treasure_key']}
                    )],
                    finish_reason="FUNCTION_CALL",
                    usage={"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}
                )

        mock_agent.step = Mock(side_effect=mock_step)

        game = TreasureHuntGame(str(hunt_path), mock_agent)
        result = game.run()

        # Should have executed tools
        assert len(result.tool_calls) >= 2
        assert any(tc['name'] == 'ls' for tc in result.tool_calls)
        assert any(tc['name'] == 'check_treasure' for tc in result.tool_calls)

    def test_game_success_on_correct_treasure(self, temp_hunt, mock_agent):
        """
        Test game succeeds when agent finds treasure.

        Properties:
        - success=True when check_treasure returns correct
        - game_over=True
        - end_reason="treasure_found"
        - treasure_key_found is set
        """
        from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame

        hunt_path, hunt_result = temp_hunt

        mock_agent.step = Mock(return_value=MockAgentResponse(
            text="Checking key",
            tool_calls=[MockToolCall(
                name="check_treasure",
                arguments={"key": hunt_result['treasure_key']}
            )],
            finish_reason="FUNCTION_CALL",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        ))

        game = TreasureHuntGame(str(hunt_path), mock_agent)
        result = game.run()

        assert result.success is True
        assert result.end_reason == "treasure_found"
        assert result.treasure_key_found == hunt_result['treasure_key']

    def test_game_failure_on_give_up(self, temp_hunt, mock_agent):
        """
        Test game fails when agent gives up.

        Properties:
        - success=False
        - game_over=True
        - end_reason="gave_up"
        """
        from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame

        hunt_path, hunt_result = temp_hunt

        mock_agent.step = Mock(return_value=MockAgentResponse(
            text="I give up",
            tool_calls=[MockToolCall(name="give_up", arguments={})],
            finish_reason="FUNCTION_CALL",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        ))

        game = TreasureHuntGame(str(hunt_path), mock_agent)
        result = game.run()

        assert result.success is False
        assert result.end_reason == "gave_up"

    def test_game_failure_on_max_turns(self, temp_hunt, mock_agent):
        """
        Test game fails on reaching max turns.

        Properties:
        - success=False
        - end_reason="max_turns"
        - turns_taken == max_turns
        """
        from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame

        hunt_path, hunt_result = temp_hunt

        # Agent just keeps listing directory
        mock_agent.step = Mock(return_value=MockAgentResponse(
            text="Listing",
            tool_calls=[MockToolCall(name="ls", arguments={"path": "."})],
            finish_reason="FUNCTION_CALL",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        ))

        game = TreasureHuntGame(str(hunt_path), mock_agent, max_turns=3)
        result = game.run()

        assert result.success is False
        assert result.end_reason == "max_turns"
        assert result.turns_taken == 3

    def test_game_failure_on_max_tokens(self, temp_hunt, mock_agent):
        """
        Test game fails on reaching max tokens.

        Properties:
        - success=False
        - end_reason="max_tokens"
        - total_tokens >= max_tokens
        """
        from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame

        hunt_path, hunt_result = temp_hunt

        # Agent uses lots of tokens
        mock_agent.step = Mock(return_value=MockAgentResponse(
            text="Listing",
            tool_calls=[MockToolCall(name="ls", arguments={"path": "."})],
            finish_reason="FUNCTION_CALL",
            usage={"prompt_tokens": 500, "completion_tokens": 500, "total_tokens": 1000}
        ))

        game = TreasureHuntGame(str(hunt_path), mock_agent, max_tokens=2500)
        result = game.run()

        assert result.success is False
        assert result.end_reason == "max_tokens"
        assert result.total_tokens >= 2500

    def test_game_tracks_token_usage(self, temp_hunt, mock_agent):
        """
        Test game tracks token usage correctly.

        Properties:
        - total_tokens is sum of all turns
        - prompt_tokens and completion_tokens are separated
        - Matches agent's reported usage
        """
        from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame

        hunt_path, hunt_result = temp_hunt

        call_count = 0

        def mock_step(game_input):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return MockAgentResponse(
                    text="First",
                    tool_calls=[MockToolCall(name="ls", arguments={"path": "."})],
                    finish_reason="FUNCTION_CALL",
                    usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
                )
            else:
                return MockAgentResponse(
                    text="Second",
                    tool_calls=[MockToolCall(
                        name="check_treasure",
                        arguments={"key": hunt_result['treasure_key']}
                    )],
                    finish_reason="FUNCTION_CALL",
                    usage={"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300}
                )

        mock_agent.step = Mock(side_effect=mock_step)

        game = TreasureHuntGame(str(hunt_path), mock_agent)
        result = game.run()

        assert result.total_tokens == 450  # 150 + 300
        assert result.prompt_tokens == 300  # 100 + 200
        assert result.completion_tokens == 150  # 50 + 100

    def test_game_tracks_time(self, temp_hunt, mock_agent):
        """
        Test game tracks execution time.

        Properties:
        - total_time > 0
        - total_time is reasonable (< 10 seconds for mock)
        """
        from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame

        hunt_path, hunt_result = temp_hunt

        mock_agent.step = Mock(return_value=MockAgentResponse(
            text="Done",
            tool_calls=[MockToolCall(
                name="check_treasure",
                arguments={"key": hunt_result['treasure_key']}
            )],
            finish_reason="FUNCTION_CALL",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        ))

        game = TreasureHuntGame(str(hunt_path), mock_agent)
        result = game.run()

        assert result.total_time > 0
        assert result.total_time < 10.0

    def test_game_logs_tool_calls(self, temp_hunt, mock_agent):
        """
        Test game logs all tool calls.

        Properties:
        - Each tool call is logged
        - Log includes name, arguments, result
        - Logs are accessible via result.tool_calls
        """
        from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame

        hunt_path, hunt_result = temp_hunt

        mock_agent.step = Mock(return_value=MockAgentResponse(
            text="Testing",
            tool_calls=[
                MockToolCall(name="ls", arguments={"path": "."}),
                MockToolCall(name="pwd", arguments={})
            ],
            finish_reason="FUNCTION_CALL",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        ))

        game = TreasureHuntGame(str(hunt_path), mock_agent, max_turns=1)
        result = game.run()

        # Should have logged both tool calls
        assert len(result.tool_calls) >= 2
        logged_names = [tc['name'] for tc in result.tool_calls]
        assert 'ls' in logged_names
        assert 'pwd' in logged_names

    def test_sequential_tool_execution(self, temp_hunt, mock_agent):
        """
        Test tools are executed sequentially, not in parallel.

        Properties:
        - Multiple tool calls in one response execute in order
        - Each tool sees state changes from previous tool
        """
        from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame

        hunt_path, hunt_result = temp_hunt

        # Agent requests: cd subdir, then pwd
        mock_agent.step = Mock(return_value=MockAgentResponse(
            text="Moving",
            tool_calls=[
                MockToolCall(name="cd", arguments={"path": hunt_result['treasure_file'].split('/')[0]}),
                MockToolCall(name="pwd", arguments={})
            ],
            finish_reason="FUNCTION_CALL",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        ))

        game = TreasureHuntGame(str(hunt_path), mock_agent, max_turns=1)
        result = game.run()

        # pwd should reflect the cd change
        pwd_call = [tc for tc in result.tool_calls if tc['name'] == 'pwd'][0]
        assert hunt_result['treasure_file'].split('/')[0] in pwd_call['result']

    def test_terminating_tool_stops_execution(self, temp_hunt, mock_agent):
        """
        Test that check_treasure or give_up stops tool execution.

        Properties:
        - If check_treasure succeeds, remaining tools not executed
        - If give_up is called, remaining tools not executed
        """
        from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame

        hunt_path, hunt_result = temp_hunt

        # Agent requests: check_treasure (correct), then ls (should not execute)
        mock_agent.step = Mock(return_value=MockAgentResponse(
            text="Checking",
            tool_calls=[
                MockToolCall(name="check_treasure", arguments={"key": hunt_result['treasure_key']}),
                MockToolCall(name="ls", arguments={"path": "."})
            ],
            finish_reason="FUNCTION_CALL",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        ))

        game = TreasureHuntGame(str(hunt_path), mock_agent)
        result = game.run()

        # Should have executed check_treasure but not ls
        tool_names = [tc['name'] for tc in result.tool_calls]
        assert 'check_treasure' in tool_names
        assert 'ls' not in tool_names

    def test_game_result_structure(self, temp_hunt, mock_agent):
        """
        Test GameResult has all required fields.

        Properties:
        - All fields present
        - Types are correct
        - final_state is a GameState
        """
        from treasure_hunt_agent.treasure_hunt_game import TreasureHuntGame

        hunt_path, hunt_result = temp_hunt

        mock_agent.step = Mock(return_value=MockAgentResponse(
            text="Done",
            tool_calls=[MockToolCall(name="give_up", arguments={})],
            finish_reason="FUNCTION_CALL",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        ))

        game = TreasureHuntGame(str(hunt_path), mock_agent)
        result = game.run()

        assert hasattr(result, 'success')
        assert hasattr(result, 'turns_taken')
        assert hasattr(result, 'treasure_key_found')
        assert hasattr(result, 'total_tokens')
        assert hasattr(result, 'prompt_tokens')
        assert hasattr(result, 'completion_tokens')
        assert hasattr(result, 'total_time')
        assert hasattr(result, 'tool_calls')
        assert hasattr(result, 'final_state')
        assert hasattr(result, 'end_reason')
        assert hasattr(result, 'error')

        assert isinstance(result.success, bool)
        assert isinstance(result.turns_taken, int)
        assert isinstance(result.total_tokens, int)
        assert isinstance(result.total_time, float)
        assert isinstance(result.tool_calls, list)
