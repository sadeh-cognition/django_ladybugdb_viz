"""View tests using Django test Client.

Verifies HTML pages load correctly with a real LadybugDB database.
"""

from __future__ import annotations

import pytest
from django.test import Client


@pytest.mark.django_db
class TestDatabaseOverviewView:
    def test_overview_loads(self, lbug_db: str) -> None:
        client = Client()
        resp = client.get(f"/ladybug-viz/{lbug_db}/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Person" in content
        assert "City" in content
        assert "Knows" in content
        assert "LivesIn" in content

    def test_overview_contains_counts(self, lbug_db: str) -> None:
        client = Client()
        resp = client.get(f"/ladybug-viz/{lbug_db}/")
        content = resp.content.decode()
        # Node tables section should exist
        assert "NODE" in content


@pytest.mark.django_db
class TestTableDetailView:
    def test_node_table_detail(self, lbug_db: str) -> None:
        client = Client()
        resp = client.get(f"/ladybug-viz/{lbug_db}/table/Person/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Person" in content
        assert "name" in content
        assert "age" in content

    def test_rel_table_detail(self, lbug_db: str) -> None:
        client = Client()
        resp = client.get(f"/ladybug-viz/{lbug_db}/table/Knows/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Knows" in content
        assert "REL" in content


@pytest.mark.django_db
class TestGraphView:
    def test_graph_view_loads(self, lbug_db: str) -> None:
        client = Client()
        resp = client.get(f"/ladybug-viz/{lbug_db}/graph/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "sigma" in content.lower()
        assert "sigma-container" in content


@pytest.mark.django_db
class TestCypherConsoleView:
    def test_cypher_console_loads(self, lbug_db: str) -> None:
        client = Client()
        resp = client.get(f"/ladybug-viz/{lbug_db}/cypher/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "cypher-input" in content
        assert "run-cypher-btn" in content
