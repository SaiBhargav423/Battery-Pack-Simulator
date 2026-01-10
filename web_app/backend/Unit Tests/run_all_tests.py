"""
Test runner script for all unit tests.

Run all unit tests with:
    python run_all_tests.py

Or run specific test modules:
    python run_all_tests.py test_api_endpoints
    python run_all_tests.py test_database test_logger
"""

import unittest
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(backend_dir))


def discover_and_run_tests(test_modules=None):
    """
    Discover and run unit tests.
    
    Args:
        test_modules: Optional list of specific test modules to run.
                     If None, runs all tests.
    """
    # Get test directory
    test_dir = Path(__file__).parent
    
    if test_modules:
        # Load specific test modules
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        for module_name in test_modules:
            try:
                # Import the test module
                module = __import__(f'Unit Tests.{module_name}', fromlist=[module_name])
                # Load tests from module
                tests = loader.loadTestsFromModule(module)
                suite.addTests(tests)
                print(f"Loaded tests from {module_name}")
            except ImportError as e:
                print(f"Warning: Could not import {module_name}: {e}")
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
    else:
        # Discover and run all tests
        loader = unittest.TestLoader()
        suite = loader.discover(str(test_dir), pattern='test_*.py')
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_modules = sys.argv[1:]
        exit_code = discover_and_run_tests(test_modules)
    else:
        exit_code = discover_and_run_tests()
    
    sys.exit(exit_code)
