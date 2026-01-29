import json
from datetime import timezone

import pytest

from tests.db.utils import DB_URLS, managed_db_session
from zodiac_core.db.sql import SQLBase, UUIDMixin
from zodiac_core.schemas import UUIDSchema


# 1. DB Model
class ProductDB(SQLBase, UUIDMixin, table=True):
    __tablename__ = "schema_test_products"
    name: str
    price: float


# 2. Response Schema (DTO)
class ProductResponse(UUIDSchema):
    name: str
    price: float


@pytest.mark.serial
class TestSchemaConsistency:
    @pytest.mark.parametrize("name,url,connect_args", DB_URLS)
    @pytest.mark.asyncio
    async def test_schema_serialization_consistency(self, name, url, connect_args):
        """
        Test that data retrieved from different DB engines is serialized
        consistently by Pydantic Schemas, especially Timezones.
        """
        async with managed_db_session(url, connect_args) as (engine, session):
            p = ProductDB(name="Standard Item", price=99.9)
            session.add(p)
            await session.commit()
            await session.refresh(p)

            dto = ProductResponse.model_validate(p)

            assert dto.name == "Standard Item"
            assert str(dto.id) == str(p.id)

            assert dto.created_at.tzinfo == timezone.utc
            assert dto.updated_at.tzinfo == timezone.utc

            json_output = dto.model_dump_json()
            data = json.loads(json_output)

            created_str = data["created_at"]
            assert created_str.endswith("+00:00") or created_str.endswith("Z")
