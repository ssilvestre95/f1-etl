import os

import psycopg
import pytest
from dotenv import load_dotenv

from etl.load import create_schema

load_dotenv()

DROP_ALL = (
    "DROP TABLE IF EXISTS fact_sprint_results, fact_results, "
    "dim_race, dim_constructor, dim_driver CASCADE"
)


@pytest.fixture
def conn():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        if os.environ.get("CI"):
            pytest.fail("TEST_DATABASE_URL secret is missing in CI")
        pytest.skip("TEST_DATABASE_URL not set")
    if url == os.environ.get("DATABASE_URL"):
        pytest.fail("TEST_DATABASE_URL must not point to the real database")

    connection = psycopg.connect(url)
    connection.execute(DROP_ALL)
    create_schema(connection)
    connection.commit()

    yield connection

    connection.rollback()
    connection.execute(DROP_ALL)
    connection.commit()
    connection.close()