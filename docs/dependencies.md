# Dependencies

## Runtime Dependencies

The `pyproject.toml` file defines all project dependencies in the `[project]` section:

- **click** - Command-line interface framework for the CLI
- **requests** - HTTP library for the forex rates fetch feature

## Development Dependencies

Development and testing dependencies are defined as optional dependencies in `[project.optional-dependencies]`:

```toml
[project.optional-dependencies]
dev = [
  "pytest",
  "pytest-cov",
  "mkdocs>=1.5.0,<2.0",
  "mkdocs-material>=9.0.0,<10.0",
]
```

## Dependency Management

Dependencies are defined in `pyproject.toml` as the single source of truth. The `requirements.txt` file is generated from `pyproject.toml` using `pip-tools`.

### Generating requirements.txt

When dependencies change in `pyproject.toml`, regenerate the locked requirements:

```bash
pip install pip-tools
pip-compile pyproject.toml
```

This ensures `requirements.txt` always matches `pyproject.toml` dependencies with pinned versions.

