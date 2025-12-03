# PlayGodot

External automation and testing framework for Godot Engine games.

Control and test Godot games from Python scripts, similar to how [Playwright](https://playwright.dev/) automates web browsers.

## Status

**v0.1.0 - Initial Implementation**

Core framework structure is in place. See [docs/](docs/) for usage guides.

## Project Structure

```
PlayGodot/
├── python/playgodot/      # Python client library
├── addons/playgodot/      # Godot 4.x addon
├── protocol/              # JSON-RPC protocol spec
├── docs/                  # Documentation
└── examples/              # Example projects
```

## Quick Start

**Python Client:**
```bash
cd python
pip install -e ".[dev]"
```

**Godot Addon:**
1. Copy `addons/playgodot/` to your Godot project
2. Enable the plugin in Project Settings → Plugins

## Documentation

- [Getting Started](docs/getting-started.md)
- [API Reference](docs/api-reference.md)
- [CI Integration](docs/ci-integration.md)
- [Protocol Specification](protocol/PROTOCOL.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
