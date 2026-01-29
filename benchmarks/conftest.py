from typing import List, Tuple

import pytest
from fastapi import APIRouter as NativeAPIRouter
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from zodiac_core import APIRouter as ZodiacAPIRouter
from zodiac_core import register_middleware, setup_loguru


class BenchmarkUser(BaseModel):
    """Unified user model for benchmarking."""

    id: int
    name: str
    email: str


@pytest.fixture(scope="module", autouse=True)
def silence_logging():
    """Ensure logs don't interfere with performance measurement."""

    setup_loguru(level="WARNING")


@pytest.fixture(scope="module")
def large_user_list() -> List[BenchmarkUser]:
    """Generates a standard large dataset (100 users)."""
    return [BenchmarkUser(id=i, name=f"User {i}", email=f"user{i}@example.com") for i in range(100)]


@pytest.fixture(scope="module")
def benchmark_apps(large_user_list) -> Tuple[FastAPI, FastAPI, FastAPI]:
    """
    Creates standardized apps for head-to-head comparison.
    1. Native FastAPI
    2. Zodiac wrapping only
    3. Zodiac wrapping + Full middleware
    """
    # 1. Native
    native_app = FastAPI()
    native_router = NativeAPIRouter(prefix="/native")

    @native_router.get("/small", response_model=BenchmarkUser)
    def get_native_small():
        return BenchmarkUser(id=1, name="Native", email="n@t.com")

    @native_router.get("/large", response_model=List[BenchmarkUser])
    def get_native_large():
        return large_user_list

    native_app.include_router(native_router)

    # 2. Zodiac (Pure wrapping)
    zodiac_app = FastAPI()
    zodiac_router = ZodiacAPIRouter(prefix="/zodiac")

    @zodiac_router.get("/small", response_model=BenchmarkUser)
    def get_zodiac_small():
        return BenchmarkUser(id=1, name="Zodiac", email="z@t.com")

    @zodiac_router.get("/large", response_model=List[BenchmarkUser])
    def get_zodiac_large():
        return large_user_list

    zodiac_app.include_router(zodiac_router)

    # 3. Zodiac (Full stack with Middleware)
    full_app = FastAPI()
    register_middleware(full_app)
    full_router = ZodiacAPIRouter(prefix="/full")

    @full_router.get("/small", response_model=BenchmarkUser)
    def get_full_small():
        return BenchmarkUser(id=1, name="Full", email="f@t.com")

    full_app.include_router(full_router)

    return native_app, zodiac_app, full_app


@pytest.fixture(scope="module")
def benchmark_clients(benchmark_apps) -> Tuple[TestClient, TestClient, TestClient]:
    """Clients for each app configuration."""
    native, zodiac, full = benchmark_apps
    return TestClient(native), TestClient(zodiac), TestClient(full)
