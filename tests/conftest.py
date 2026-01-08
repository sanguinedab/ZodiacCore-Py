import pytest

from starlette.requests import Request


DB_URLS = [
    ("sqlite", "sqlite:///:memory:", None),
    ("postgresql", "postgresql://postgres:@localhost:5432/zodiac_test", {"options": "-c timezone=utc"}),
    (
        "mysql",
        "mysql+pymysql://root:root@localhost:3306/zodiac_test",
        {"init_command": "SET time_zone='+00:00'"},
    ),
]


@pytest.fixture
def mock_request():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/test",
        "headers": [
        ],
        "query_string": b"page=1&limit=10",
        "client": ("127.0.0.1", 54321),
        "server": ("testserver", 8000),
        "scheme": "http",
        "root_path": "",
        "app": None,
    }
    return Request(scope)
