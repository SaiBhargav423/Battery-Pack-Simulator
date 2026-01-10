# Unit Tests

This directory contains comprehensive unit tests for the BMS Simulator backend.

## Test Structure

- **test_api_endpoints.py**: Tests for all Flask REST API endpoints
- **test_database.py**: Tests for SQLite database operations
- **test_simulation_manager.py**: Tests for SimulationManager class
- **test_logger.py**: Tests for error logging functionality
- **test_config_validation.py**: Tests for configuration validation
- **run_all_tests.py**: Test runner script

## Running Tests

### Run All Tests

```bash
cd web_app/backend
python "Unit Tests/run_all_tests.py"
```

### Run Specific Test Module

```bash
python "Unit Tests/run_all_tests.py" test_api_endpoints
python "Unit Tests/run_all_tests.py" test_database test_logger
```

### Run Individual Test File

```bash
python -m unittest "Unit Tests.test_api_endpoints"
python -m unittest "Unit Tests.test_database"
```

### Run Specific Test Class or Method

```bash
python -m unittest "Unit Tests.test_api_endpoints.TestAPIEndpoints.test_health_check"
```

## Test Coverage

### API Endpoints (`test_api_endpoints.py`)

- ✅ Health check endpoint
- ✅ Simulation control (start/stop/pause/resume)
- ✅ Simulation status
- ✅ Configuration management
- ✅ Fault scenarios
- ✅ Session management
- ✅ Log monitoring
- ✅ Error handling

### Database (`test_database.py`)

- ✅ Database initialization
- ✅ Session creation and management
- ✅ BMS frame storage
- ✅ Data querying with filters
- ✅ Statistics calculation
- ✅ CSV export

### Simulation Manager (`test_simulation_manager.py`)

- ✅ Simulation lifecycle (start/stop/pause/resume)
- ✅ Status reporting
- ✅ Configuration handling
- ✅ Error handling

### Logger (`test_logger.py`)

- ✅ Exception logging
- ✅ Error message logging
- ✅ Log file management
- ✅ Recent errors retrieval

### Configuration Validation (`test_config_validation.py`)

- ✅ Required field validation
- ✅ Type conversion (string to number)
- ✅ Default value application
- ✅ Invalid data handling

## Test Requirements

All test dependencies are included in `requirements.txt`:
- `unittest` (built-in)
- `unittest.mock` (built-in)
- `requests` (for API testing)

## Writing New Tests

When adding new functionality, create corresponding test cases:

1. Create a new test file: `test_<module_name>.py`
2. Import necessary modules and mocks
3. Create test class inheriting from `unittest.TestCase`
4. Implement `setUp()` and `tearDown()` methods
5. Write test methods starting with `test_`
6. Use assertions to verify expected behavior

### Example Test Structure

```python
import unittest
from unittest.mock import patch, MagicMock

class TestMyModule(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        pass
    
    def tearDown(self):
        """Clean up after tests."""
        pass
    
    def test_feature_name(self):
        """Test description."""
        # Arrange
        # Act
        # Assert
        self.assertEqual(expected, actual)
```

## Mocking

Tests use `unittest.mock` to isolate units under test:

- **External dependencies**: Mock database, file system, network calls
- **Complex objects**: Mock BatteryPack, AFE, UART transmitters
- **Time-dependent code**: Mock time functions for deterministic tests

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Unit Tests
  run: |
    cd web_app/backend
    python "Unit Tests/run_all_tests.py"
```

## Notes

- Tests use temporary files/databases where possible to avoid side effects
- Tests clean up resources in `tearDown()` methods
- Some tests require backend modules to be available (marked with `@patch`)
- Database tests use temporary SQLite files
- API tests use Flask test client (no actual HTTP server needed)
