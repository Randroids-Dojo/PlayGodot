# Agent Instructions for PlayGodot

This file contains instructions for AI coding agents working on this repository.

## Project Overview

PlayGodot is an external automation and testing framework for Godot Engine games. It uses Godot's native RemoteDebugger protocol via a custom Godot fork for communication. It consists of:

- **Python package** (`python/`): The main testing library published to PyPI
- **Protocol** (`protocol/`): JSON-RPC message definitions

## Release Process

### Prerequisites

- Ensure all changes are merged to `main`
- Verify tests pass

### Steps to Release

1. **Update version in `python/pyproject.toml`**:
   ```toml
   version = "X.Y.Z"
   ```

2. **Commit and push the version bump**:
   ```bash
   git add python/pyproject.toml
   git commit -m "Bump version to X.Y.Z"
   git push origin main
   ```

3. **Create and push a git tag**:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z - Brief description"
   git push origin vX.Y.Z
   ```

4. **Create a GitHub Release**:
   - Go to https://github.com/Randroids-Dojo/PlayGodot/releases/new
   - Select the tag you just pushed
   - Title: `vX.Y.Z` or `vX.Y.Z - Description`
   - Add release notes describing changes
   - Click "Publish release"

5. **PyPI publishing is automatic**:
   - The `publish.yml` workflow triggers on release publication
   - It builds and uploads to PyPI using trusted publishing (OIDC)
   - No API tokens needed - GitHub Actions handles authentication
   - Monitor the workflow at: https://github.com/Randroids-Dojo/PlayGodot/actions/workflows/publish.yml

### Manual PyPI Publishing (if needed)

If you need to publish manually or to TestPyPI:

1. **Build the package**:
   ```bash
   cd python
   pip install build
   python -m build
   ```

2. **Upload to TestPyPI** (for testing):
   ```bash
   pip install twine
   twine upload --repository testpypi dist/*
   ```

3. **Upload to PyPI**:
   ```bash
   twine upload dist/*
   ```

Note: Manual uploads require a PyPI API token configured in `~/.pypirc` or passed via `-u __token__ -p <token>`.

## Code Style

- Python: Uses `ruff` for linting (config in `python/pyproject.toml`)
- Run linting: `cd python && ruff check .`
- Run type checking: `cd python && mypy playgodot`

## Testing

- Python tests: `cd python && pytest`
- Integration tests require a running Godot instance (custom fork with RemoteDebugger support)

## Important Notes

- The `license` field in `pyproject.toml` uses table format `{text = "MIT"}` for twine compatibility
- GitHub Actions uses trusted publishing - no secrets needed for PyPI uploads
