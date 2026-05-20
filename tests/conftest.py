"""
Test configuration and fixtures.
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key"


import pytest


@pytest.fixture(scope="session")
def test_data_dir():
    """Get test data directory."""
    return PROJECT_ROOT / "tests" / "data"


@pytest.fixture(scope="session")
def sample_pdf_path(test_data_dir):
    """Get path to sample PDF for testing."""
    return test_data_dir / "sample.pdf"
