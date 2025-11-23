# Contributing

Thank you for your interest in contributing to Treasure Hunt Agent! This guide will help you get started.

## Getting Started

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/agent_treasure_hunt.git
cd agent_treasure_hunt
```

3. Add upstream remote:

```bash
git remote add upstream https://github.com/matweldon/agent_treasure_hunt.git
```

### Development Setup

1. Install dependencies with uv:

```bash
uv sync
```

2. Activate the virtual environment:

```bash
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

3. Install development dependencies:

```bash
uv add --dev pytest pytest-cov black isort mypy
```

## Development Workflow

### Creating a Branch

Create a feature branch for your changes:

```bash
git checkout -b feature/your-feature-name
```

Use prefixes:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `test/` - Test additions or fixes
- `refactor/` - Code refactoring

### Making Changes

1. Make your changes
2. Write tests for new functionality
3. Ensure all tests pass
4. Format code and check types
5. Commit with clear messages

### Running Tests

Run the full test suite:

```bash
pytest tests/ -v
```

Run specific test file:

```bash
pytest tests/test_treasure_hunt_generator.py -v
```

Run with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

View coverage report:

```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Code Quality

#### Formatting with Black

```bash
black src/ tests/
```

#### Import Sorting with isort

```bash
isort src/ tests/
```

#### Type Checking with mypy

```bash
mypy src/
```

#### Run All Quality Checks

```bash
black src/ tests/ && isort src/ tests/ && mypy src/ && pytest tests/
```

## Coding Standards

### Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use Black for formatting (line length: 88)
- Use type hints for all functions
- Write docstrings for public APIs

### Example Code Style

```python
from pathlib import Path
from typing import Optional, List


def generate_treasure_hunt(
    base_path: str = "./treasure_hunt",
    depth: int = 6,
    seed: Optional[int] = None
) -> dict:
    """
    Generate a treasure hunt with specified parameters.

    Args:
        base_path: Root directory for the hunt
        depth: Maximum depth of directory tree
        seed: Random seed for reproducibility

    Returns:
        Configuration dictionary with hunt metadata

    Raises:
        ValueError: If parameters are invalid
        OSError: If directory creation fails

    Example:
        >>> config = generate_treasure_hunt(seed=42)
        >>> print(config['depth'])
        6
    """
    # Implementation here
    pass
```

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Short description.

    Longer description if needed. Can span
    multiple lines.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ErrorType: When this error occurs

    Example:
        >>> function_name("test", 42)
        True
    """
```

## Testing Guidelines

### Writing Tests

Follow TDD principles:

1. Write failing test first
2. Implement minimum code to pass
3. Refactor while keeping tests green

### Test Structure

```python
import pytest
from treasure_hunt_agent.module import function


class TestFunctionName:
    """Test suite for function_name."""

    def test_basic_functionality(self):
        """Test basic use case."""
        result = function(param="value")
        assert result == expected

    def test_edge_case(self):
        """Test edge case behavior."""
        with pytest.raises(ValueError):
            function(param="invalid")

    @pytest.mark.parametrize("input,expected", [
        ("case1", "result1"),
        ("case2", "result2"),
    ])
    def test_multiple_inputs(self, input, expected):
        """Test multiple input cases."""
        assert function(input) == expected
```

### Test Coverage

Aim for:
- 90%+ code coverage
- All public APIs tested
- Edge cases covered
- Error conditions tested

## Commit Guidelines

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or changes
- `refactor`: Code refactoring
- `style`: Formatting changes
- `chore`: Maintenance tasks

### Examples

```
feat: Add difficulty preset for expert mode

Adds a new 'expert' difficulty preset with depth 10,
branching factor 5, and file density 0.6.

Closes #123
```

```
fix: Prevent path traversal in cd tool

Validates paths more strictly to prevent escaping
hunt boundaries using ../../ patterns.

Fixes #456
```

## Pull Request Process

### Before Submitting

1. Update your branch with upstream:

```bash
git fetch upstream
git rebase upstream/main
```

2. Ensure all tests pass
3. Update documentation if needed
4. Add entry to CHANGELOG.md (if exists)

### Submitting PR

1. Push to your fork:

```bash
git push origin feature/your-feature-name
```

2. Create pull request on GitHub
3. Fill out PR template
4. Link related issues

### PR Template

```markdown
## Description
Brief description of changes

## Motivation and Context
Why is this change needed?

## Testing
How has this been tested?

## Types of Changes
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Checklist
- [ ] Tests pass
- [ ] Code formatted with Black
- [ ] Type hints added
- [ ] Documentation updated
- [ ] CHANGELOG updated
```

### Review Process

1. Maintainers will review your PR
2. Address feedback and push updates
3. Once approved, PR will be merged

## Areas for Contribution

### High Priority

- [ ] Additional agent implementations (LangChain, LLM library, etc.)
- [ ] Docker sandboxing for safe execution
- [ ] Performance metrics and benchmarking
- [ ] Cost tracking and optimization

### Documentation

- [ ] More usage examples
- [ ] Video tutorials
- [ ] API documentation improvements
- [ ] Translation to other languages

### Testing

- [ ] Integration tests
- [ ] Performance benchmarks
- [ ] Edge case coverage

### Features

- [ ] Web UI for treasure hunts
- [ ] Visualization of agent paths
- [ ] Leaderboard system
- [ ] Custom tool sets

## Getting Help

- **Questions**: Open a discussion on GitHub
- **Bugs**: Open an issue with reproduction steps
- **Chat**: Join our Discord (if available)

## Code of Conduct

Be respectful and constructive:

- Welcome newcomers
- Be patient with questions
- Accept constructive criticism
- Focus on what's best for the project

## Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing!
