# Contributing to AquaPredict

Thank you for your interest in contributing to AquaPredict! This document provides guidelines for contributing to the project.

## Code of Conduct

Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Error messages and logs

### Suggesting Features

1. Check if the feature has been suggested
2. Create a new issue with:
   - Clear description of the feature
   - Use cases and benefits
   - Possible implementation approach

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the code style guidelines
   - Add tests for new functionality
   - Update documentation

4. **Run tests**
   ```bash
   make test
   make lint
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add feature: description"
   ```
   
   Follow commit message conventions:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test additions/changes
   - `refactor:` Code refactoring
   - `style:` Code style changes
   - `chore:` Maintenance tasks

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide clear description
   - Reference related issues
   - Ensure CI passes

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/AquaPredict.git
cd AquaPredict

# Setup development environment
make setup

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

## Code Style

### Python
- Follow PEP 8
- Use Black for formatting: `black modules/`
- Use flake8 for linting: `flake8 modules/`
- Type hints encouraged
- Docstrings for all public functions (Google style)

Example:
```python
def compute_twi(dem: np.ndarray, flow_acc: np.ndarray) -> np.ndarray:
    """
    Compute Topographic Wetness Index.
    
    Args:
        dem: Digital Elevation Model
        flow_acc: Flow accumulation raster
        
    Returns:
        TWI values
    """
    pass
```

### JavaScript/TypeScript
- Follow ESLint configuration
- Use Prettier for formatting
- TypeScript for type safety
- JSDoc comments for functions

### Commit Messages
- Use present tense ("Add feature" not "Added feature")
- Keep first line under 50 characters
- Add detailed description if needed

## Testing

### Python Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest modules/modeling/tests/ -v

# Run with coverage
pytest tests/ --cov --cov-report=html
```

### Frontend Tests
```bash
cd modules/frontend
npm test
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

## Documentation

- Update README.md for user-facing changes
- Update module READMEs for module-specific changes
- Add docstrings to new functions/classes
- Update API documentation for endpoint changes

## Module Structure

When adding a new module:

```
modules/your-module/
├── README.md              # Module documentation
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container definition
├── __init__.py           # Module initialization
├── config.py             # Configuration
├── main.py               # Entry point
├── your_module.py        # Implementation
└── tests/                # Tests
    └── test_your_module.py
```

## Review Process

1. Automated checks must pass (CI/CD)
2. Code review by maintainers
3. Address feedback
4. Approval and merge

## Questions?

- Open an issue for questions
- Join discussions
- Check documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
