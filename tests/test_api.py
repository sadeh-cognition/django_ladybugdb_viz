"""Functional API endpoint tests using Ninja TestClient.

All tests use a real LadybugDB database through the ``lbug_db`` fixture.
"""

from __future__ import annotations

import pytest

from ladybug_viz.schemas import (
    CypherResponseSchema,
    ErrorSchema,
    GraphDataSchema,
    PaginatedRowsSchema,
)


@pytest.mark.django_db
class TestGetTableRows:
    """Tests for GET /{db_name}/tables/{table_name}/rows."""

    def test_get_node_rows(self, api_client, lbug_db: str) -> None:
        resp = api_client.get(f"/{lbug_db}/tables/Person/rows?limit=10&offset=0")
        assert resp.status_code == 200
        data = PaginatedRowsSchema(**resp.json())
        assert data.total_count == 3
        assert len(data.rows) == 3
        assert data.limit == 10
        assert data.offset == 0

    def test_get_rel_rows(self, api_client, lbug_db: str) -> None:
        resp = api_client.get(f"/{lbug_db}/tables/Knows/rows?limit=10&offset=0")
        assert resp.status_code == 200
        data = PaginatedRowsSchema(**resp.json())
        assert data.total_count == 2
        assert len(data.rows) == 2

    def test_get_rows_pagination(self, api_client, lbug_db: str) -> None:
        resp = api_client.get(f"/{lbug_db}/tables/Person/rows?limit=2&offset=0")
        assert resp.status_code == 200
        data = PaginatedRowsSchema(**resp.json())
        assert len(data.rows) == 2
        assert data.total_count == 3

    def test_get_rows_unknown_table(self, api_client, lbug_db: str) -> None:
        resp = api_client.get(f"/{lbug_db}/tables/NonExistent/rows")
        assert resp.status_code == 400
        data = ErrorSchema(**resp.json())
        assert "NonExistent" in data.detail


@pytest.mark.django_db
class TestCypherEndpoint:
    """Tests for POST /{db_name}/cypher."""

    def test_run_cypher(self, api_client, lbug_db: str) -> None:
        resp = api_client.post(
            f"/{lbug_db}/cypher",
            json={"query": "MATCH (n:Person) RETURN n.name ORDER BY n.name"},
        )
        assert resp.status_code == 200
        data = CypherResponseSchema(**resp.json())
        assert len(data.rows) == 3
        names = [row[0] for row in data.rows]
        assert names == ["Alice", "Bob", "Charlie"]

    def test_run_cypher_bad_query(self, api_client, lbug_db: str) -> None:
        resp = api_client.post(
            f"/{lbug_db}/cypher",
            json={"query": "THIS IS NOT VALID CYPHER"},
        )
        assert resp.status_code == 400
        data = ErrorSchema(**resp.json())
        assert data.detail


@pytest.mark.django_db
class TestGraphEndpoint:
    """Tests for GET /{db_name}/graph."""

    def test_get_graph(self, api_client, lbug_db: str) -> None:
        resp = api_client.get(f"/{lbug_db}/graph")
        assert resp.status_code == 200
        data = GraphDataSchema(**resp.json())
        # 3 Person + 2 City = 5 nodes
        assert len(data.nodes) == 5
        # 2 LivesIn + 2 Knows = 4 edges
        assert len(data.edges) == 4

        # Check node labels include known values
        labels = {n.label for n in data.nodes}
        assert "Alice" in labels
        assert "Berlin" in labels

        # Check unique table types
        table_types = {n.table for n in data.nodes}
        assert table_types == {"Person", "City"}
