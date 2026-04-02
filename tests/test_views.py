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

    def test_preview_falls_back_to_non_empty_fields(self, monkeypatch) -> None:
        from ladybug_viz import views

        client = Client()
        row = {
            "n.id": "   ",
            "n.prefLabel": "\t",
            "n.altLabels": None,
            "n.definition": " ",
            "n.content": "Visible preview text",
        }

        monkeypatch.setattr(
            views.services,
            "list_tables",
            lambda db_path: [{"name": "Page", "type": "NODE"}],
        )
        monkeypatch.setattr(
            views.services,
            "get_table_info",
            lambda db_path, table_name: [],
        )
        monkeypatch.setattr(
            views.services,
            "get_node_rows",
            lambda db_path, table_name, limit=50, offset=0: [row],
        )
        monkeypatch.setattr(
            views.services,
            "get_node_count",
            lambda db_path, table_name: 1,
        )

        resp = client.get("/ladybug-viz/test_db/table/Page/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert '<span class="preview-key">n.content</span>' in content
        assert "Visible preview text" in content


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
