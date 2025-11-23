# Claude instructions

## Workflow

- Use spec-driven development. Contribute to a spec document (append only - don't overwrite). If not told, ask the user where to find the spec.
- Always use red/green test-driven development
- Use an existing git repo if there is one, or create one if not
- Never interact with the remote GitHub repo. When the work is done, ask the user to create a PR
- Always work in a branch. 
- Never push to main, but do fetch changes in main and rebase/merge into your branch if necessary

## Testing

- When writing tests, write the function signature with type hints, and then list abstract and concrete properties the function/method should have, eg.:
  - result is positive float. Result is a list that shouldn't be longer/shorter than some dimension. Result is positive semi-definite matrix.
  - function is idempotent, or monotonic, or composable
  - Shape of result
  - Set of examples/fixtures
  - Behaviour with empty/missing args
  - Calling internal functions, behaviour
- Only then, write the test. Include the above reasoning on properties in the docstring.

## Python

- Use uv (add, sync etc) and save lock file to git. Don't use pip install -r requirements.txt
- Use uv for _everything_ Don't use the base python or pip _at all_
- Use uv run to run scripts and uvx to run tools without installation
- Use numpy style docstrings with examples where appropriate
- Use full type hints (3.11+). Use 'str | None' style
- Use pytest for tests, with unittest.mock Mock and MagicMock
- Run individual tests where possible for performance
- Preferred packages:
  - typer: for clis
