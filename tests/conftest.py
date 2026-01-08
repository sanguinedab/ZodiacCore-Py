import os
import pytest

from starlette.requests import Request


# Default local development URLs
DEFAULT_PG_URL = "postgresql://postgres:@localhost:5432/zodiac_test"
DEFAULT_MYSQL_URL = "mysql+pymysql://root:root@localhost:3306/zodiac_test"

DB_URLS = [
    ("sqlite", "sqlite:///:memory:", None),
    (
        "postgresql",
        os.getenv("POSTGRES_URL", DEFAULT_PG_URL),
        {"options": "-c timezone=utc"}
    ),
    (
        "mysql",
        os.getenv("MYSQL_URL", DEFAULT_MYSQL_URL),
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
