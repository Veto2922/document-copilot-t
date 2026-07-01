"""
Pytest configuration and shared fixtures for backend tests.
"""

import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.auth.dependencies import get_current_user, CurrentUser
from app.database.session import get_db_session

# Default test user data
TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_USER_EMAIL = "test@example.com"


@pytest.fixture
def mock_current_user() -> CurrentUser:
    """Fixture that returns a CurrentUser schema matching test auth context."""
    return CurrentUser(id=TEST_USER_ID, email=TEST_USER_EMAIL)


@pytest.fixture
def mock_db() -> AsyncMock:
    """Fixture that returns a mocked database AsyncSession."""
    session = AsyncMock()
    # Mock close and commit to prevent actual database calls
    session.close = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def client(mock_current_user, mock_db) -> TestClient:
    """
    TestClient with dependency overrides.
    Bypasses token validation and redirects db calls to mock_db.
    """
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db_session] = lambda: mock_db
    
    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()
