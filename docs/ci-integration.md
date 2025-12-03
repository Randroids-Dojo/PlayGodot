# CI Integration

This guide covers how to set up PlayGodot for continuous integration testing.

## GitHub Actions

### Basic Setup

Create `.github/workflows/tests.yml`:

```yaml
name: Game Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Godot
        uses: chickensoft-games/setup-godot@v2
        with:
          version: 4.3.0
          include-templates: false

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install playgodot pytest pytest-asyncio

      - name: Run tests
        run: |
          pytest tests/ -v --tb=short
```

### With Screenshot Testing

For visual regression testing, you'll need to store reference screenshots:

```yaml
name: Game Tests with Screenshots

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          lfs: true  # If storing screenshots in Git LFS

      - name: Setup Godot
        uses: chickensoft-games/setup-godot@v2
        with:
          version: 4.3.0
          include-templates: false

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install playgodot[image] pytest pytest-asyncio

      - name: Run tests
        run: |
          pytest tests/ -v --tb=short

      - name: Upload failed screenshots
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: failed-screenshots
          path: tests/screenshots/failures/
```

### Matrix Testing

Test across multiple Godot versions:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        godot-version: ['4.2.0', '4.3.0']
        python-version: ['3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Setup Godot
        uses: chickensoft-games/setup-godot@v2
        with:
          version: ${{ matrix.godot-version }}

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install and test
        run: |
          pip install playgodot pytest pytest-asyncio
          pytest tests/ -v
```

## GitLab CI

Create `.gitlab-ci.yml`:

```yaml
image: python:3.11

stages:
  - test

variables:
  GODOT_VERSION: "4.3.0"

before_script:
  # Install Godot
  - wget -q https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip
  - unzip -q Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip
  - mv Godot_v${GODOT_VERSION}-stable_linux.x86_64 /usr/local/bin/godot
  - chmod +x /usr/local/bin/godot

  # Install Python dependencies
  - pip install playgodot pytest pytest-asyncio

test:
  stage: test
  script:
    - pytest tests/ -v --tb=short
  artifacts:
    when: on_failure
    paths:
      - tests/screenshots/failures/
```

## CircleCI

Create `.circleci/config.yml`:

```yaml
version: 2.1

jobs:
  test:
    docker:
      - image: cimg/python:3.11

    steps:
      - checkout

      - run:
          name: Install Godot
          command: |
            wget -q https://github.com/godotengine/godot/releases/download/4.3.0-stable/Godot_v4.3.0-stable_linux.x86_64.zip
            unzip -q Godot_v4.3.0-stable_linux.x86_64.zip
            sudo mv Godot_v4.3.0-stable_linux.x86_64 /usr/local/bin/godot
            sudo chmod +x /usr/local/bin/godot

      - run:
          name: Install Python dependencies
          command: pip install playgodot pytest pytest-asyncio

      - run:
          name: Run tests
          command: pytest tests/ -v --tb=short

      - store_artifacts:
          path: tests/screenshots/failures/
          destination: failed-screenshots

workflows:
  test:
    jobs:
      - test
```

## Docker

For local or self-hosted CI, use Docker:

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libgl1 \
    libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*

# Install Godot
ARG GODOT_VERSION=4.3.0
RUN wget -q https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip \
    && unzip -q Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip \
    && mv Godot_v${GODOT_VERSION}-stable_linux.x86_64 /usr/local/bin/godot \
    && chmod +x /usr/local/bin/godot \
    && rm Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip

# Install Python packages
RUN pip install playgodot pytest pytest-asyncio

WORKDIR /app

# Run tests by default
CMD ["pytest", "tests/", "-v"]
```

### Usage

```bash
# Build
docker build -t playgodot-tests .

# Run tests
docker run -v $(pwd):/app playgodot-tests
```

## Best Practices

### 1. Use Headless Mode

Always run in headless mode in CI:

```python
async with Godot.launch("game/", headless=True) as game:
    ...
```

### 2. Increase Timeouts

CI environments can be slower:

```python
async with Godot.launch("game/", timeout=60.0) as game:
    await game.wait_for_node("/root/Main", timeout=30.0)
```

### 3. Handle Flaky Tests

Add retries for potentially flaky tests:

```python
import pytest

@pytest.mark.flaky(reruns=3, reruns_delay=1)
@pytest.mark.asyncio
async def test_network_dependent(game):
    ...
```

### 4. Isolate Tests

Each test should be independent:

```python
@pytest.fixture
async def game():
    async with Godot.launch("game/") as g:
        yield g
        # Game is automatically terminated after each test
```

### 5. Store Screenshots Separately

Keep reference screenshots in a separate directory or Git LFS:

```
tests/
├── screenshots/
│   ├── reference/       # Checked into version control
│   │   ├── menu.png
│   │   └── gameplay.png
│   └── failures/        # Generated on failure, gitignored
└── test_visual.py
```

### 6. Parallel Test Execution

For faster CI, run tests in parallel:

```bash
pytest tests/ -v -n auto  # Requires pytest-xdist
```

Note: Each test needs its own Godot instance, so ensure your CI has enough resources.

### 7. Cache Dependencies

Speed up CI by caching:

```yaml
# GitHub Actions
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

## Troubleshooting

### "Display not found" errors

Ensure headless mode is enabled, or use a virtual display:

```yaml
- name: Setup virtual display
  run: |
    sudo apt-get install -y xvfb
    Xvfb :99 &
    export DISPLAY=:99
```

### Connection timeouts

Increase the timeout and add startup delay:

```python
async with Godot.launch("game/", timeout=120.0) as game:
    await asyncio.sleep(5)  # Wait for server to start
    ...
```

### Out of memory

Limit parallel test execution:

```bash
pytest tests/ -v -n 2  # Only 2 parallel workers
```
