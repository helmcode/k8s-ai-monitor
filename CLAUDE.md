# Kubernetes Monitor Project Guidelines

## Development Commands
- **Run application**: `python main.py`
- **Install dependencies**: `pip install -r requirements.txt`
- **Linting**: `flake8 .`

## Code Style Guidelines
- **Imports**: Group standard library, third-party, and local imports with a blank line between groups
- **Typing**: Use type hints for all function parameters and return values (`from typing import Dict, List, Any`)
- **Error handling**: Use try/except blocks with specific exceptions and error logging
- **Logging**: Use the configured logger with appropriate log levels (info, error)
- **Naming**:
  - Classes: PascalCase
  - Functions/variables: snake_case
  - Constants: UPPER_SNAKE_CASE
- **Documentation**: Docstrings for all classes and methods using the """ format with Args section
- **Async pattern**: Use async/await for non-blocking operations
- **Max line length**: 88 characters

## Environment Variables
- SLACK_API_TOKEN: Required for Slack notifications
- ANTHROPIC_API_KEY: Required for LLM analysis
