# Installation

This guide will help you install Treasure Hunt Agent and its dependencies.

## Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) package manager

## Installing uv

If you don't have `uv` installed, you can install it using:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Installing Treasure Hunt Agent

### From Source

1. Clone the repository:

```bash
git clone https://github.com/matweldon/agent_treasure_hunt.git
cd agent_treasure_hunt
```

2. Install dependencies using uv:

```bash
uv sync
```

This will:
- Create a virtual environment at `.venv`
- Install all required dependencies including:
  - `google-generativeai` for the Gemini agent
  - All testing dependencies

## Verify Installation

Verify that the installation was successful:

```bash
# Activate the virtual environment
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate  # On Windows

# Run the tests
pytest tests/ -v
```

If all tests pass, you're ready to start using Treasure Hunt Agent!

## Optional: Gemini API Key

To run treasure hunts with the Gemini agent, you'll need a Google AI API key:

1. Get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Set the environment variable:

```bash
export GOOGLE_API_KEY='your-api-key-here'
```

## Next Steps

Now that you have Treasure Hunt Agent installed, head to the [Quick Start](quickstart.md) guide to generate your first treasure hunt!
