"""Pytest fixtures for ladybug_viz tests.

Creates a real temporary LadybugDB database with a known schema and seed data.
No mocks are used.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from typing import Generator

import pytest
import real_ladybug as lb

from ninja.testing import TestClient

from ladybug_viz.api import api


@pytest.fixture()
def lbug_db() -> Generator[str, None, None]:
    """Create a temp LadybugDB database with seed data.

    Yields the *db_name* (without the ``.lbug`` extension) that the app expects.
    The database file is placed in the cwd so the service layer finds it at
    ``{db_name}.lbug``.
    """
    tmpdir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(tmpdir)

    db_name = "test_db"
    db_path = f"{db_name}.lbug"

    db = lb.Database(db_path)
    conn = lb.Connection(db)

    # Schema
    conn.execute(
        "CREATE NODE TABLE Person(name STRING PRIMARY KEY, age INT64)"
    )
    conn.execute(
        "CREATE NODE TABLE City(name STRING PRIMARY KEY, population INT64)"
    )
    conn.execute("CREATE REL TABLE LivesIn(FROM Person TO City)")
    conn.execute(
        "CREATE REL TABLE Knows(FROM Person TO Person, since INT64)"
    )

    # Seed data
    conn.execute("CREATE (p:Person {name: 'Alice', age: 30})")
    conn.execute("CREATE (p:Person {name: 'Bob', age: 25})")
    conn.execute("CREATE (p:Person {name: 'Charlie', age: 35})")
    conn.execute("CREATE (c:City {name: 'Berlin', population: 3700000})")
    conn.execute("CREATE (c:City {name: 'London', population: 8900000})")

    conn.execute(
        "MATCH (a:Person {name: 'Alice'}), (b:City {name: 'Berlin'}) "
        "CREATE (a)-[:LivesIn]->(b)"
    )
    conn.execute(
        "MATCH (a:Person {name: 'Bob'}), (b:City {name: 'London'}) "
        "CREATE (a)-[:LivesIn]->(b)"
    )
    conn.execute(
        "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) "
        "CREATE (a)-[:Knows {since: 2020}]->(b)"
    )
    conn.execute(
        "MATCH (a:Person {name: 'Bob'}), (b:Person {name: 'Charlie'}) "
        "CREATE (a)-[:Knows {since: 2022}]->(b)"
    )

    # Close so later accesses work
    del conn
    del db

    yield db_name

    os.chdir(original_cwd)
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture()
def api_client() -> TestClient:
    """Return a Ninja TestClient for the ladybug_viz API."""
    return TestClient(api)
