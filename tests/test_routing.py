from typing import List, Union

import pytest
from fastapi import APIRouter as NativeAPIRouter
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from zodiac_core import APIRouter as ZodiacAPIRouter
from zodiac_core import Response, response_ok
from zodiac_core.routing import ZodiacRoute, _get_model_name


class User(BaseModel):
    """Mock user data model."""

    id: int
    name: str


class ErrorMessage(BaseModel):
    """Mock error response model."""

    detail: str


class TestZodiacRouting:
    """Tests for Zodiac routing enhancements, including response wrapping and OpenAPI doc generation."""

    @pytest.fixture(scope="class")
    def routing_app(self):
        app = FastAPI(title="Zodiac Test App")

        # 1. Native route: comparison group
        native_router = NativeAPIRouter(prefix="/native")

        @native_router.get("/user", response_model=User)
        async def get_native_user():
            return User(id=1, name="Native")

        # 2. Zodiac route: verify automatic wrapping logic
        zodiac_router = ZodiacAPIRouter(prefix="/zodiac")

        @zodiac_router.get("/user", response_model=User)
        async def get_zodiac_user():
            return User(id=2, name="Zodiac")

        # 3. Mixed scenario: manually return Response object to verify prevention of double wrapping
        @zodiac_router.get("/manual")
        async def get_manual_response():
            return response_ok(data={"item": "manual"})

        # 4. Conflict scenario: verify 409 and multiple response wrapping
        @zodiac_router.post(
            "/conflict",
            response_model=User,
            responses={409: {"model": ErrorMessage, "description": "Conflict"}},
        )
        async def create_user_conflict():
            return Response(code=409, message="User already exists", data=None)

        app.include_router(native_router)
        app.include_router(zodiac_router)
        return app

    @pytest.fixture(scope="class")
    def client(self, routing_app):
        return TestClient(routing_app)

    def test_response_structure_comparison(self, client):
        """Scenario 1: Ensure response contains the three core elements and compare with native behavior."""

        # Verify native: should return model JSON directly
        native_resp = client.get("/native/user")
        assert native_resp.status_code == 200
        native_data = native_resp.json()
        assert "id" in native_data
        assert "code" not in native_data

        # Verify Zodiac: should include code, data, and message
        zodiac_resp = client.get("/zodiac/user")
        assert zodiac_resp.status_code == 200
        zodiac_body = zodiac_resp.json()

        assert "code" in zodiac_body
        assert "data" in zodiac_body
        assert "message" in zodiac_body
        assert zodiac_body["code"] == 0
        assert zodiac_body["message"] == "Success"
        assert zodiac_body["data"]["id"] == 2
        assert zodiac_body["data"]["name"] == "Zodiac"

    def test_no_double_wrapping(self, client):
        """Scenario 2: Ensure manual Response return doesn't result in double wrapping."""
        resp = client.get("/zodiac/manual")
        body = resp.json()

        assert body["code"] == 0
        assert body["data"] == {"item": "manual"}
        assert isinstance(body["data"], dict)
        assert "item" in body["data"]

    def test_conflict_response(self, client):
        """Scenario 3: Ensure 409 conflict scenario returns correct business code and structure."""
        resp = client.post("/zodiac/conflict")
        body = resp.json()
        assert body["code"] == 409
        assert body["message"] == "User already exists"
        assert body["data"] is None

    def test_openapi_schema_contract(self, routing_app):
        """Scenario 4: Ensure OpenAPI (Swagger) documentation definitions are correct."""
        schema = routing_app.openapi()

        # 1. Verify native interface doc: points to User model
        native_path = schema["paths"]["/native/user"]["get"]["responses"]["200"]
        native_schema_ref = native_path["content"]["application/json"]["schema"]["$ref"]
        assert "User" in native_schema_ref

        # 2. Verify Zodiac interface doc: points to dynamically generated wrapped model (e.g., Response_User)
        zodiac_path = schema["paths"]["/zodiac/user"]["get"]["responses"]["200"]
        zodiac_schema_ref = zodiac_path["content"]["application/json"]["schema"]["$ref"]
        assert "Response_User" in zodiac_schema_ref

        # 3. Verify wrapped model structure
        components = schema["components"]["schemas"]
        assert "Response_User" in components
        wrapped_model = components["Response_User"]

        props = wrapped_model["properties"]
        assert "code" in props
        assert "message" in props
        assert "data" in props

        # Verify data field reference logic (handling anyOf for nullable fields in OpenAPI 3.1+)
        data_schema = props["data"]
        if "$ref" in data_schema:
            assert "User" in data_schema["$ref"]
        elif "anyOf" in data_schema:
            assert any("User" in item.get("$ref", "") for item in data_schema["anyOf"])

        # 4. Verify 409 error response is also wrapped
        conflict_responses = schema["paths"]["/zodiac/conflict"]["post"]["responses"]
        assert "409" in conflict_responses
        conflict_ref = conflict_responses["409"]["content"]["application/json"]["schema"]["$ref"]
        assert "Response_ErrorMessage" in conflict_ref


class TestRoutingInternalLogic:
    """Unit tests for internal routing logic to ensure 100% code coverage."""

    def test_get_model_name_coverage(self):
        """Covers lines 17-21 in zodiac_core/routing.py."""
        assert _get_model_name(User) == "User"
        assert _get_model_name(List[User]) == "List_User"
        assert _get_model_name(List[List[User]]) == "List_List_User"
        assert _get_model_name(List) == "List"
        assert _get_model_name(int) == "int"

    def test_should_wrap_logic(self):
        """Covers lines 65, 69-70 in zodiac_core/routing.py."""

        class MyResponse(Response):
            pass

        # 1. Standard types
        assert ZodiacRoute._should_wrap(User) is True
        assert ZodiacRoute._should_wrap(None) is True

        # 2. Response subclasses
        assert ZodiacRoute._should_wrap(Response) is False
        assert ZodiacRoute._should_wrap(MyResponse) is False

        # 3. Response[T] generic (Line 65)
        assert ZodiacRoute._should_wrap(Response[User]) is False

        # 4. Union types (Lines 69-70: TypeError in issubclass)
        assert ZodiacRoute._should_wrap(Union[User, None]) is True
