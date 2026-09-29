# Contributing to kodekloud-mcp

Thank you for your interest in improving `kodekloud-mcp`! We welcome contributions from all KodeKloud learners and community members.

## Development Setup

We recommend using [`uv`](https://docs.astral.sh/uv/) for fast, reliable virtual environment and dependency management.

```bash
# Clone the repository
git clone https://github.com/Maghav/kodekloud-mcp.git
cd kodekloud-mcp

# Create a virtual environment and install development dependencies
uv venv
uv pip install -e ".[dev]"
```

Or using standard `pip`:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running Quality Checks

Before submitting a Pull Request, ensure that all linters, type checks, and tests pass:

```bash
# Lint code and verify formatting
uv run ruff check .
uv run ruff format --check .

# Run static type checking
uv run mypy src tests

# Execute test suite
uv run pytest -v
```

## Helping Discover & Map Upstream Endpoints

KodeKloud does not provide official public API documentation. The client implementation in `src/kodekloud_mcp/kodekloud_client.py` contains isolated endpoint definitions marked with `TODO`.

If you are inspecting network requests in your browser and want to contribute endpoint schemas:
1. **Sanitize Everything First**: Open the network trace or HAR file in a text editor and search for `Cookie`, `Authorization`, `Bearer`, `token`, `email`, `password`, and student names. Replace all sensitive strings with placeholder text (e.g., `REDACTED`).
2. Compare the captured response schema with the Pydantic models in `src/kodekloud_mcp/models.py`.
3. Update the endpoint mapping dictionary in `src/kodekloud_mcp/kodekloud_client.py`.
4. Add unit test fixtures in `tests/test_client.py` using `httpx.MockTransport` so other developers can test without needing live credentials.

## Pull Request Guidelines

- Keep pull requests focused on a single feature or bug fix.
- Ensure all tests pass.
- Update `CHANGELOG.md` under the `[Unreleased]` section.
- Never include personal credentials or sensitive tokens in PR descriptions, code, or test data.
