# Contributing to Mission42 Timesheet

Thank you for considering contributing to Mission42 Timesheet! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Format](#commit-message-format)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Documentation](#documentation)
- [Questions](#questions)

## Code of Conduct

This project adheres to professional standards of conduct. By participating, you are expected to:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the project
- Show empathy towards other contributors

## Getting Started

Before you start contributing:

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/mission42-timesheet.git
   cd mission42-timesheet
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ZisenisDigital/mission42-timesheet.git
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- uv package manager
- PocketBase binary
- Git

### Initial Setup

1. **Install dependencies**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv sync
   ```

2. **Setup PocketBase**:
   ```bash
   ./scripts/download_pocketbase.sh
   cd pocketbase
   ./pocketbase serve
   ```

3. **Setup environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your test credentials
   ```

4. **Seed test data**:
   ```bash
   python scripts/seed_settings.py
   python scripts/seed_work_packages.py
   python scripts/seed_project_specs.py
   ```

5. **Run tests**:
   ```bash
   uv run pytest tests/ -v
   ```

### Development Workflow

1. Keep your fork updated:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. Make your changes in your feature branch

3. Run tests frequently:
   ```bash
   uv run pytest tests/
   ```

4. Check code quality:
   ```bash
   uv run black app/ tests/
   uv run ruff check app/ tests/
   uv run mypy app/
   ```

## How to Contribute

### Types of Contributions

- **Bug fixes**: Fix identified bugs
- **New features**: Implement new functionality
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Performance**: Optimize existing code
- **Refactoring**: Improve code structure

### Before Starting Work

1. **Check existing issues**: Look for related issues or discussions
2. **Open an issue**: If no issue exists, create one describing your proposal
3. **Wait for feedback**: Give maintainers time to respond
4. **Get assignment**: Wait for issue assignment before starting work

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/issue-number-description
   ```

2. **Make focused commits**:
   - Keep changes small and focused
   - One logical change per commit
   - Write clear commit messages

3. **Add tests**:
   - All new features must include tests
   - Bug fixes should include regression tests
   - Maintain >80% code coverage

4. **Update documentation**:
   - Update README if needed
   - Add docstrings to new functions/classes
   - Update relevant guides

## Coding Standards

### Python Style Guide

Follow PEP 8 with these specifics:

- **Line length**: 100 characters (configured in pyproject.toml)
- **Formatting**: Use Black for automatic formatting
- **Linting**: Use Ruff for code quality checks
- **Type hints**: Use type annotations where applicable

### Code Formatting

Run Black before committing:
```bash
uv run black app/ tests/
```

### Linting

Check with Ruff:
```bash
uv run ruff check app/ tests/
```

Fix auto-fixable issues:
```bash
uv run ruff check --fix app/ tests/
```

### Type Checking

Run mypy for type checking:
```bash
uv run mypy app/
```

### Naming Conventions

- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Files**: `snake_case.py`

### Documentation Strings

Use Google-style docstrings:

```python
def process_time_blocks(
    blocks: List[TimeBlock],
    config: Config
) -> List[ProcessedBlock]:
    """
    Process raw time blocks according to configuration.

    Args:
        blocks: List of time blocks to process
        config: Configuration settings

    Returns:
        List of processed time blocks

    Raises:
        ValueError: If blocks contain invalid data
    """
    pass
```

## Testing Guidelines

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_processor.py -v

# Run specific test
uv run pytest tests/test_processor.py::test_process_blocks -v
```

### Writing Tests

- **Location**: Place tests in `tests/` directory
- **Naming**: Test files must start with `test_`
- **Test functions**: Must start with `test_`
- **Fixtures**: Use pytest fixtures for common setup
- **Coverage**: Aim for >80% code coverage

Example test:

```python
import pytest
from app.services.processor import TimeBlockProcessor


def test_process_blocks_with_overlap():
    """Test that overlapping blocks are resolved by priority."""
    processor = TimeBlockProcessor(config)

    blocks = [
        create_test_block(source="calendar", priority=80),
        create_test_block(source="wakatime", priority=100),
    ]

    result = processor.process_blocks(blocks)

    assert len(result) == 1
    assert result[0].source == "wakatime"
```

### Test Categories

- **Unit tests**: Test individual functions/classes
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows

## Commit Message Format

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or modifications
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Build process or auxiliary tool changes

### Examples

```
feat(exporter): add PDF export format

Implement PDF export for monthly timesheets using ReportLab.
Includes German formatting and matches existing layout.

Closes #45
```

```
fix(processor): correct overlap resolution logic

Fixed bug where lower priority blocks were incorrectly preserved
when overlapping with higher priority blocks.

Fixes #67
```

```
docs(readme): update installation instructions

Added section about PocketBase setup and seed scripts.
```

### Commit Message Rules

- Use imperative mood ("add feature" not "added feature")
- First line max 72 characters
- Reference issues/PRs in footer
- Explain *what* and *why*, not *how*

## Pull Request Process

### Before Submitting

1. **Update your branch**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run full test suite**:
   ```bash
   uv run pytest tests/ --cov=app
   ```

3. **Check code quality**:
   ```bash
   uv run black app/ tests/
   uv run ruff check app/ tests/
   uv run mypy app/
   ```

4. **Update documentation** if needed

### Submitting Pull Request

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR on GitHub**:
   - Use descriptive title
   - Reference related issues
   - Describe changes in detail
   - Include screenshots if UI changes
   - List any breaking changes

### PR Template

```markdown
## Description
Brief description of changes

## Related Issues
Closes #123

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing Done
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
[Add screenshots here]

## Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Commit messages follow convention
```

### Review Process

- Maintainers will review your PR
- Address feedback promptly
- Push additional commits to your branch
- Once approved, maintainer will merge

### After Merge

1. **Delete your branch**:
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. **Update your fork**:
   ```bash
   git checkout main
   git pull upstream main
   git push origin main
   ```

## Issue Reporting

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check documentation** for solutions
3. **Try latest version** of the project

### Bug Reports

Include:

- **Description**: Clear description of the bug
- **Steps to reproduce**: Detailed steps to reproduce the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Environment**: OS, Python version, package versions
- **Logs**: Relevant log output or error messages
- **Screenshots**: If applicable

Template:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
A clear description of what you expected to happen.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.5]
- Version: [e.g., 1.0.0]

**Additional context**
Add any other context about the problem here.
```

### Feature Requests

Include:

- **Description**: Clear description of the feature
- **Use case**: Why is this feature needed?
- **Proposed solution**: How should it work?
- **Alternatives**: Alternative solutions considered

## Documentation

### Types of Documentation

- **Code comments**: Explain complex logic
- **Docstrings**: Document functions/classes
- **README**: Setup and quick start
- **Guides**: Step-by-step tutorials
- **API docs**: Endpoint documentation

### Writing Documentation

- Use clear, concise language
- Include code examples
- Add screenshots where helpful
- Keep documentation up-to-date
- Link related documentation

### Documentation Structure

```
docs/
├── ADMIN_GUIDE.md         # PocketBase administration
├── OAUTH_GUIDE.md         # OAuth setup
├── DEPLOYMENT.md          # Deployment instructions
└── CONTRIBUTING.md        # This file
```

## Questions

### Getting Help

- **GitHub Discussions**: For general questions and discussions
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Check existing documentation first

### Contact

- GitHub: https://github.com/ZisenisDigital/mission42-timesheet
- Issues: https://github.com/ZisenisDigital/mission42-timesheet/issues

## Recognition

Contributors will be recognized in:

- GitHub contributors page
- Release notes for their contributions
- README acknowledgments section (for significant contributions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Mission42 Timesheet!
