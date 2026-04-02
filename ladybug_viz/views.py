"""Django views for the ladybug_viz front-end."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from ladybug_viz import services

# Columns shown in the collapsed accordion summary row.
# The expanded detail panel always shows every column.
PREVIEW_KEYS: list[str] = [
    "n.id",
    "n.prefLabel",
    "n.altLabels",
    "n.definition",
    "a.id",
    "a.prefLabel",
    "a.altLabels",
    "a.definition",
    "b.id",
    "b.prefLabel",
    "b.altLabels",
    "b.definition",
]


def _has_meaningful_preview_value(value: Any) -> bool:
    """Return True when *value* contains something worth showing in a summary."""
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return True


def _display_value(value: Any) -> str:
    """Normalise values for HTML rendering."""
    if value is None:
        return "—"
    text = str(value)
    return text if text.strip() else "—"


def _build_row_cards(
    rows: list[dict[str, Any]],
    preview_keys: list[str],
) -> list[dict[str, list[dict[str, str]]]]:
    """Precompute preview/detail fields for the accordion template."""
    row_cards: list[dict[str, list[dict[str, str]]]] = []
    for row in rows:
        row_items = list(row.items())
        row_by_key = dict(row_items)
        fields = [
            {"key": key, "display_value": _display_value(value)}
            for key, value in row_items
        ]

        preferred_keys = [key for key in preview_keys if key in row_by_key] or [
            key for key, _value in row_items
        ]
        preview_fields = [
            {"key": key, "display_value": _display_value(row_by_key[key])}
            for key in preferred_keys
            if _has_meaningful_preview_value(row_by_key[key])
        ]

        if not preview_fields:
            preview_fields = [
                {"key": key, "display_value": _display_value(value)}
                for key, value in row_items
                if _has_meaningful_preview_value(value)
            ]

        row_cards.append(
            {
                "preview_fields": preview_fields or fields[:1],
                "fields": fields,
            }
        )

    return row_cards


def database_overview(request: HttpRequest, db_name: str) -> HttpResponse:
    """Dashboard: list tables, counts, and schema overview."""
    db_path = f"{db_name}.lbug"
    tables = services.list_tables(db_path)

    node_tables = [t for t in tables if t["type"] == "NODE"]
    rel_tables = [t for t in tables if t["type"] == "REL"]

    # Enrich with counts
    for nt in node_tables:
        nt["count"] = services.get_node_count(db_path, nt["name"])

    for rt in rel_tables:
        rt["count"] = services.get_rel_count(db_path, rt["name"])
        conns = services.get_connection_info(db_path, rt["name"])
        rt["connections"] = conns

    return render(
        request,
        "ladybug_viz/database_overview.html",
        {
            "db_name": db_name,
            "node_tables": node_tables,
            "rel_tables": rel_tables,
            "total_node_tables": len(node_tables),
            "total_rel_tables": len(rel_tables),
        },
    )


def table_detail(request: HttpRequest, db_name: str, table_name: str) -> HttpResponse:
    """Table detail: schema columns + initial paginated rows."""
    db_path = f"{db_name}.lbug"

    tables = services.list_tables(db_path)
    table_entry = next((t for t in tables if t["name"] == table_name), None)
    table_type = table_entry["type"] if table_entry else "NODE"

    columns = services.get_table_info(db_path, table_name)
    connections: list = []

    if table_type == "NODE":
        rows = services.get_node_rows(db_path, table_name, limit=50, offset=0)
        total = services.get_node_count(db_path, table_name)
    else:
        rows = services.get_rel_rows(db_path, table_name, limit=50, offset=0)
        total = services.get_rel_count(db_path, table_name)
        connections = services.get_connection_info(db_path, table_name)

    # Only show PREVIEW_KEYS that actually exist in the data.
    # If none match (e.g. REL tables), fall back to every column.
    # NOTE: the JS already does this same intersection clientside for paginated pages.
    actual_keys: list[str] = list(rows[0].keys()) if rows else []
    effective_preview_keys: list[str] = (
        [k for k in PREVIEW_KEYS if k in actual_keys] or actual_keys
    )
    row_cards = _build_row_cards(rows, effective_preview_keys)
    return render(
        request,
        "ladybug_viz/table_detail.html",
        {
            "db_name": db_name,
            "table_name": table_name,
            "table_type": table_type,
            "columns": columns,
            "rows": row_cards,
            "total_count": total,
            "connections": connections,
            "preview_keys": effective_preview_keys,
        },
    )


def graph_view(request: HttpRequest, db_name: str) -> HttpResponse:
    """Full-page Sigma.js graph visualisation."""
    return render(
        request,
        "ladybug_viz/graph_view.html",
        {
            "db_name": db_name,
        },
    )


def cypher_console(request: HttpRequest, db_name: str) -> HttpResponse:
    """Interactive Cypher query console."""
    return render(
        request,
        "ladybug_viz/cypher_console.html",
        {
            "db_name": db_name,
        },
    )
