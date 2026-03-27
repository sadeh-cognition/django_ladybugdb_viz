"""Django views for the ladybug_viz front-end."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from ladybug_viz import services


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

    return render(
        request,
        "ladybug_viz/table_detail.html",
        {
            "db_name": db_name,
            "table_name": table_name,
            "table_type": table_type,
            "columns": columns,
            "rows": rows,
            "total_count": total,
            "connections": connections,
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
