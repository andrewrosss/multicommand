# Contributing

## Setup

```bash
# Clone and install
git clone https://github.com/andrewrosss/multicommand.git
cd multicommand
uv sync
```

## Development

```bash
# Lint
uv run ruff check .
uv run ruff format --check .

# Type check
uv run pyright src

# Run integration tests
./examples/01_simple/test_cli.sh
```

## Documentation

```bash
# Preview docs locally (macOS)
./docs/preview.sh

# Build docs (Linux/CI)
./docs/build.sh
```

Output is written to `docs/book/`.
