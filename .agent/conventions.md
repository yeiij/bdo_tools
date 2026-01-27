# Coding Conventions

## Code Style
- **Formatter**: Use `ruff` for linting and formatting. Ensure code is compliant with PEP 8.
- **Type Hints**: Use python type hints heavily. All function signatures should have type annotations for arguments and return values.
- **Docstrings**: Include clear docstrings for all modules, classes, and public functions.

## Architecture
- **Dependency Rule**: The `domain` layer must NOT depend on `infrastructure` or `ui`. Dependencies should point inwards.
- **Interfaces**: Define abstract base classes (protocols) in definitions within `src/domain` for any infrastructure requirement. Implement them in `src/infrastructure`.
- **ViewModels**: UI logic should reside in ViewModels (`src/ui/viewmodels`), not in the View code (`src/ui/views`). Views should observe ViewModels.

## Testing
- **Framework**: `pytest`
- **Unit Tests**: Place in `tests/`. Mirror the source structure where possible.
- **Mocking**: Use `unittest.mock` to mock external dependencies (system calls, network) when testing core logic.
- **Coverage**: Aim for high test coverage, especially in `domain` and `utils`.
