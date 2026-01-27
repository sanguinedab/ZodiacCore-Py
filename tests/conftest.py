import pytest
from starlette.requests import Request


@pytest.fixture
def mock_request():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/test",
        "headers": [],
        "query_string": b"page=1&limit=10",
        "client": ("127.0.0.1", 54321),
        "server": ("testserver", 8000),
        "scheme": "http",
        "root_path": "",
        "app": None,
    }
    return Request(scope)
