# Repository Guidelines

## Project Structure & Module Organization
- Code lives under `src/meshcap/`:
  - `main.py` (CLI entry, `meshcap.main:main`),
  - `filter.py` (filter parser/evaluator),
  - `identifiers.py` (node/user identity helpers),
  - `view/` and `packets/` (formatting and packet helpers).
- Tests are in `tests/` (e.g., `test_filtering.py`, `test_formatting.py`).
- Config: `pyproject.toml` (Python 3.12+, script entry), lockfile `uv.lock`.

## Build, Test, and Development Commands
- You run in an environment where `ast-grep` is available; whenever a search
requires syntax-aware or structural matching, default to 'ast-grep --lang python
-p'<pattern>' (or set '--lang' appropriately) and avoid falling back to
text-only tools like 'rg' or 'grep unless I explicitly request a plain-text
search.
- Linting and formatting using `uvx ruff`
- Install deps: `uv sync`
- Run CLI: `uv run meshcap [options] [filter ...]`
  - Example: `uv run meshcap -p /dev/ttyUSB0 --verbose port text`
- Run tests: `uv run pytest` (subset: `uv run pytest -k filtering`)
- Build package: `uv build`

## Coding Style & Naming Conventions
- Python, 4-space indentation, PEP 8 naming (modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`).
- Use type hints consistently; prefer pure functions in `filter.py` and keep I/O and side effects in `main.py`.
- Error handling: raise or log with `logging` (avoid bare prints in library code).
- No committed formatting config; keep code readable and consistent with existing files.

## Testing Guidelines
- Framework: `pytest`. Place tests under `tests/` as `test_*.py` and mirror module names when possible.
- Add cases alongside existing suites (e.g., extend `test_filtering.py` when changing the parser).
- Aim for deterministic, example-driven assertions for CLI output formatting.
- Run full suite before PRs: `uv run pytest -q`.

## Commit & Pull Request Guidelines
- Prefer Conventional Commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:` (history already follows this pattern).
- PRs should include: concise description, rationale, CLI examples (inputs + sample output), and test updates. Link related issues.
- Keep changes scoped; avoid unrelated refactors.

## Security & Configuration Tips
- Serial access: default port is `/dev/ttyACM0`; use `-p/--port` for others. Don’t commit packet capture files.
- Avoid secrets or personal node IDs in tests or examples.
- Local venvs (`.venv/`) are ignored; manage deps with `uv` only.
