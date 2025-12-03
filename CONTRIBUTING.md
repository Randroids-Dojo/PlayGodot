# Contributing to PlayGodot

Thank you for your interest in contributing to PlayGodot! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.9+
- Godot 4.x
- Git

### Setting Up the Development Environment

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/PlayGodot.git
   cd PlayGodot
   ```

2. **Set up the Python client for development:**
   ```bash
   cd python
   pip install -e ".[dev]"
   ```

3. **Run the Python tests:**
   ```bash
   pytest
   ```

4. **Set up the Godot addon:**
   - Create a test Godot project
   - Copy `addons/playgodot/` to your test project
   - Enable the plugin in Project Settings

## Project Structure

```
PlayGodot/
├── python/                 # Python client library
│   ├── playgodot/         # Main package
│   ├── tests/             # Python tests
│   └── pyproject.toml     # Package configuration
├── addons/playgodot/      # Godot addon
├── protocol/              # Protocol specification
├── examples/              # Example projects
├── docs/                  # Documentation
└── CONTRIBUTING.md        # This file
```

## Areas for Contribution

### Python Client

- Implement new API methods
- Improve error handling and messages
- Add type annotations
- Write tests
- Optimize performance

### Godot Addon

- Implement command handlers
- Improve input simulation accuracy
- Add support for more node types
- Optimize WebSocket communication

### Documentation

- Improve getting started guide
- Add more examples
- Document edge cases
- Fix typos and clarify wording

### Protocol

- Propose new commands
- Improve serialization
- Document behavior

### Other Clients

We welcome clients in other languages:
- TypeScript/JavaScript
- Rust
- Go
- C#

## Development Workflow

### 1. Create an Issue

Before starting work, create or find an issue describing the change:
- Bug reports should include reproduction steps
- Feature requests should describe the use case

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 3. Make Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 4. Run Tests

**Python:**
```bash
cd python
pytest
mypy playgodot
ruff check playgodot
```

### 5. Commit

Write clear commit messages:
```
Add screenshot comparison threshold parameter

- Allow users to specify comparison threshold
- Default to 0.99 (99% similarity)
- Add tests for edge cases
```

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use `ruff` for linting
- Use `mypy` for type checking

**Example:**
```python
async def get_property(self, path: str, property_name: str) -> Any:
    """Get a property value from a node.

    Args:
        path: The node path.
        property_name: The property name.

    Returns:
        The property value.
    """
    result = await self._client.send(
        "get_property",
        {"path": path, "property": property_name},
    )
    return result.get("value")
```

### GDScript

- Follow official GDScript style guide
- Use type hints where possible
- Document public functions with `##` comments

**Example:**
```gdscript
## Get a property value from a node.
##
## Returns a dictionary with the result or error.
func _get_property(params: Dictionary) -> Dictionary:
    var path = params.get("path", "")
    var property = params.get("property", "")

    var node = get_tree().root.get_node_or_null(path)
    if node == null:
        return {"error": {"code": -32000, "message": "Node not found: " + path}}

    var value = node.get(property)
    return {"result": {"value": _serialize_value(value)}}
```

## Testing

### Python Tests

```bash
cd python
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest -k "test_client"   # Run specific tests
pytest --cov=playgodot    # With coverage
```

### Integration Tests

Integration tests require a running Godot project. See `examples/` for test project setup.

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear

### PR Description

Include:
- What the PR does
- Why it's needed
- How to test it
- Related issues

### Review Process

1. Maintainers will review your PR
2. Address any feedback
3. Once approved, the PR will be merged

## Reporting Bugs

Include:
- PlayGodot version
- Godot version
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages or logs

## Feature Requests

Include:
- Use case description
- Proposed API (if applicable)
- Examples of how it would be used

## Questions

For questions:
- Check existing documentation
- Search existing issues
- Open a new issue with the "question" label

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn

Thank you for contributing to PlayGodot!
