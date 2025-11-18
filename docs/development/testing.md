# Testing

Comprehensive guide to testing Treasure Hunt Agent components.

## Overview

The project uses pytest for testing with TDD (Test-Driven Development) methodology.

## Running Tests

### All Tests

```bash
pytest tests/ -v
```

### Specific Test File

```bash
pytest tests/test_treasure_hunt_generator.py -v
```

### Specific Test Class

```bash
pytest tests/test_treasure_hunt_generator.py::TestTreasureHuntGenerator -v
```

### Specific Test Method

```bash
pytest tests/test_treasure_hunt_generator.py::TestTreasureHuntGenerator::test_basic_generation -v
```

## Test Coverage

### Generate Coverage Report

```bash
pytest tests/ --cov=src --cov-report=html
```

### View Coverage

```bash
# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# Windows
start htmlcov/index.html
```

### Coverage Goals

- **Overall**: 90%+ coverage
- **Critical paths**: 100% coverage
- **Edge cases**: Comprehensive coverage

## Test Structure

### Directory Layout

```
tests/
├── __init__.py
├── test_treasure_hunt_generator.py
├── test_game_tools.py
├── test_gemini_agent.py
└── test_treasure_hunt_game.py
```

### Test File Organization

```python
"""
Tests for treasure_hunt_generator module.

Tests cover:
- Basic generation
- Parameter validation
- Difficulty presets
- Reproducibility
"""

import pytest
from pathlib import Path
from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt


class TestTreasureHuntGenerator:
    """Test suite for treasure hunt generation."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.test_dir = Path("./test_hunt")

    def teardown_method(self):
        """Clean up after each test."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_basic_generation(self):
        """Test basic treasure hunt generation."""
        config = generate_treasure_hunt(
            base_path=str(self.test_dir),
            seed=42
        )
        assert self.test_dir.exists()
        assert "treasure_key" in config
```

## Test Categories

### Unit Tests

Test individual functions in isolation.

```python
def test_generate_treasure_key():
    """Test treasure key generation."""
    key1 = generate_treasure_key(length=16)
    key2 = generate_treasure_key(length=16)

    assert len(key1) == 16
    assert len(key2) == 16
    assert key1 != key2  # Random generation
```

### Integration Tests

Test components working together.

```python
def test_full_hunt_generation():
    """Test complete hunt generation and navigation."""
    # Generate hunt
    config = generate_treasure_hunt(seed=42)

    # Create agent
    agent = ExampleAgent()

    # Run game
    game = TreasureHuntGame(agent, hunt_path, config)
    results = game.run()

    # Verify success
    assert results['success'] is True
```

### Parametrized Tests

Test multiple input combinations.

```python
@pytest.mark.parametrize("difficulty,expected_depth", [
    ("easy", 4),
    ("medium", 6),
    ("hard", 8),
])
def test_difficulty_presets(difficulty, expected_depth):
    """Test difficulty preset parameters."""
    config = generate_treasure_hunt(
        difficulty=difficulty,
        seed=42
    )
    assert config['depth'] == expected_depth
```

### Fixture-Based Tests

Use pytest fixtures for reusable test data.

```python
@pytest.fixture
def sample_config():
    """Provide sample hunt configuration."""
    return {
        "treasure_key": "test_key_123",
        "start_file": "start.txt",
        "depth": 4,
        "seed": 42
    }

@pytest.fixture
def temp_hunt_dir(tmp_path):
    """Create temporary hunt directory."""
    hunt_dir = tmp_path / "hunt"
    hunt_dir.mkdir()
    return hunt_dir

def test_with_fixtures(sample_config, temp_hunt_dir):
    """Test using fixtures."""
    # Use provided fixtures
    assert sample_config['depth'] == 4
    assert temp_hunt_dir.exists()
```

## Testing Best Practices

### Arrange-Act-Assert Pattern

```python
def test_tool_execution():
    # Arrange
    hunt_root = Path("./hunt")
    current_dir = hunt_root
    tool_call = {"tool": "pwd"}

    # Act
    result = execute_tool(tool_call, current_dir, hunt_root, config)

    # Assert
    assert result['success'] is True
    assert result['output'] == "/"
```

### Test Independence

Each test should be independent:

```python
class TestGameTools:
    def setup_method(self):
        """Create fresh test environment."""
        self.hunt_dir = Path("./test_hunt")
        self.hunt_dir.mkdir()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.hunt_dir)

    def test_first(self):
        """First test - doesn't depend on others."""
        pass

    def test_second(self):
        """Second test - independent of first."""
        pass
```

### Descriptive Test Names

```python
# Good
def test_cd_tool_changes_directory_successfully():
    pass

def test_cd_tool_rejects_paths_outside_boundaries():
    pass

# Bad
def test_cd():
    pass

def test_cd_2():
    pass
```

### Testing Exceptions

```python
def test_invalid_depth_raises_error():
    """Test that invalid depth raises ValueError."""
    with pytest.raises(ValueError, match="Depth must be at least 1"):
        generate_treasure_hunt(depth=0)
```

## Test-Driven Development

### TDD Workflow

1. **Write failing test**

```python
def test_new_feature():
    """Test new feature that doesn't exist yet."""
    result = new_feature(param="value")
    assert result == "expected"
```

2. **Run test** (should fail)

```bash
pytest tests/test_new_feature.py -v
```

3. **Implement minimum code**

```python
def new_feature(param):
    return "expected"  # Simplest implementation
```

4. **Run test** (should pass)

```bash
pytest tests/test_new_feature.py -v
```

5. **Refactor** while keeping tests green

### TDD Benefits

- Clear requirements
- Better design
- Comprehensive coverage
- Confidence in refactoring

## Mocking and Patching

### Mocking External APIs

```python
from unittest.mock import Mock, patch

def test_gemini_agent_with_mock():
    """Test agent without calling real API."""
    with patch('google.generativeai.GenerativeModel') as mock_model:
        # Configure mock
        mock_model.return_value.generate_content.return_value = Mock(
            text="Response",
            tool_calls=[{"tool": "ls"}]
        )

        # Test with mock
        agent = GeminiAgent(api_key="fake_key")
        response = agent.generate_response([])

        # Verify mock was called
        assert mock_model.called
```

### Temporary Files and Directories

```python
def test_with_temp_directory(tmp_path):
    """Test using pytest's tmp_path fixture."""
    # tmp_path is automatically created and cleaned up
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    assert test_file.read_text() == "content"
    # No cleanup needed - pytest handles it
```

## Performance Testing

### Timing Tests

```python
import time

def test_generation_performance():
    """Test that generation completes within time limit."""
    start = time.time()

    generate_treasure_hunt(depth=8, seed=42)

    duration = time.time() - start
    assert duration < 5.0  # Should complete in under 5 seconds
```

### Benchmarking

```python
import pytest

@pytest.mark.benchmark
def test_benchmark_generation(benchmark):
    """Benchmark treasure hunt generation."""
    result = benchmark(
        generate_treasure_hunt,
        depth=6,
        seed=42
    )
    assert result is not None
```

Run benchmarks:

```bash
pytest tests/ --benchmark-only
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        pip install uv
        uv sync

    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Debugging Tests

### Verbose Output

```bash
pytest tests/ -vv
```

### Show Print Statements

```bash
pytest tests/ -s
```

### Drop into Debugger on Failure

```bash
pytest tests/ --pdb
```

### Run Last Failed Tests

```bash
pytest tests/ --lf
```

### Run Specific Markers

```bash
# Run only slow tests
pytest tests/ -m slow

# Skip slow tests
pytest tests/ -m "not slow"
```

### Test Markers

```python
import pytest

@pytest.mark.slow
def test_long_running():
    """Test that takes a long time."""
    pass

@pytest.mark.integration
def test_full_system():
    """Integration test."""
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    """Feature not yet implemented."""
    pass
```

## Common Testing Patterns

### Testing Random Behavior

```python
def test_reproducible_generation():
    """Test that same seed produces same result."""
    config1 = generate_treasure_hunt(seed=42)
    config2 = generate_treasure_hunt(seed=42)

    assert config1['golden_path'] == config2['golden_path']
```

### Testing File Operations

```python
def test_file_creation(tmp_path):
    """Test that files are created correctly."""
    hunt_dir = tmp_path / "hunt"
    config = generate_treasure_hunt(base_path=str(hunt_dir))

    start_file = hunt_dir / config['start_file']
    assert start_file.exists()
    assert start_file.read_text().startswith("Next clue:")
```

### Testing Error Messages

```python
def test_error_message_content():
    """Test that error messages are helpful."""
    with pytest.raises(ValueError) as exc_info:
        generate_treasure_hunt(depth=-1)

    assert "Depth must be at least 1" in str(exc_info.value)
```

## Next Steps

- Review [contributing guidelines](contributing.md)
- Explore [architecture details](architecture.md)
- Check [API reference](../api/generator.md)
