# Installation Guide

ZodiacCore is designed to be modular. You can install only what you need.

## Prerequisites

- **Python**: 3.12 or higher
- **Package Manager**: `pip` (standard) or `uv` (recommended for performance)

## 1. Basic Installation

For a minimal setup (Core utilities, Logging, Exception Handling, Middleware):

=== "uv"
    ```bash
    uv add zodiac-core
    ```

=== "pip"
    ```bash
    pip install zodiac-core
    ```

## 2. Installing with Database Support

ZodiacCore separates database dependencies to keep the core lightweight.

### SQL Support (SQLAlchemy + SQLModel)
Includes `sqlmodel`, `asyncpg`, `aiosqlite`, etc.

=== "uv"
    ```bash
    uv add "zodiac-core[sql]"
    ```

=== "pip"
    ```bash
    pip install "zodiac-core[sql]"
    ```

### MongoDB Support (Motor)
Includes `motor` (Async MongoDB driver).

=== "uv"
    ```bash
    uv add "zodiac-core[mongo]"
    ```

=== "pip"
    ```bash
    pip install "zodiac-core[mongo]"
    ```

## 3. Installing Everything (For Development)

If you are setting up a development environment or need all features:

=== "uv"
    ```bash
    # Install all extras
    uv sync --all-extras
    ```

=== "pip"
    ```bash
    pip install "zodiac-core[sql,mongo]"
    ```

## 4. Verifying Installation

You can verify the installed version and importability:

```bash
python -c "import zodiac_core; print(zodiac_core.__version__)"
```
