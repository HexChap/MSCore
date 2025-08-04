# MSCore

Toolkit for writing HTTP microservices using FastAPI, Pydantic and TortoiseORM

## Installation

Create and activate a virtual environment and then install MSCore:

```bash
pip install git+https://github.com/HexChap/MSCore#egg=ms_core
```

## Development Setup

1. Clone the repo
```bash
git clone https://github.com/HexChap/MSCore
cd MSCore
```

2. Install dependencies using uv (recommended)
```bash
uv sync --group dev
```

## Testing

MSCore includes a comprehensive test suite covering all major components:

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=ms_core --cov-report=html
```

## Local Documentation

1. Serve the docs
```bash
mkdocs serve
```

## Continuous Integration

The project uses GitHub Actions for automated testing:
- Runs on Python 3.12 and 3.13
- Includes linting and security checks
- Generates coverage reports
- Tests all major functionality
