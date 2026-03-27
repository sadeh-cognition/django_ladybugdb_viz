"""Service layer for LadybugDB introspection and querying.

Every function opens a fresh connection, executes, and returns plain Python data.
The ``db_path`` argument is the filesystem path to a ``.lbug`` database file.
"""

from __future__ import annotations

from typing import Any

import real_ladybug as lb


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _connect(db_path: str) -> tuple[lb.Database, lb.Connection]:
    """Return a (Database, Connection) pair for *db_path*."""
    db = lb.Database(db_path)
    conn = lb.Connection(db)
    return db, conn


# ---------------------------------------------------------------------------
# Schema introspection
# ---------------------------------------------------------------------------

def list_tables(db_path: str) -> list[dict[str, Any]]:
    """Return every table in the database.

    Each dict has keys: ``id``, ``name``, ``type``, ``database_name``, ``comment``.
    """
    _db, conn = _connect(db_path)
    result = conn.execute("CALL SHOW_TABLES() RETURN *")
    tables: list[dict[str, Any]] = []
    for row in result:
        tables.append(
            {
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "database_name": row[3],
                "comment": row[4],
            }
        )
    return tables


def get_table_info(db_path: str, table_name: str) -> list[dict[str, Any]]:
    """Return column metadata for *table_name*.

    Each dict: ``property_id``, ``name``, ``type``, ``default_expression``,
    ``primary_key``.
    """
    _db, conn = _connect(db_path)
    result = conn.execute(f"CALL TABLE_INFO('{table_name}') RETURN *")
    columns: list[dict[str, Any]] = []
    for row in result:
        columns.append(
            {
                "property_id": row[0],
                "name": row[1],
                "type": row[2],
                "default_expression": row[3],
                "primary_key": row[4],
            }
        )
    return columns


def get_connection_info(db_path: str, rel_name: str) -> list[dict[str, Any]]:
    """Return source/destination table names for relationship *rel_name*."""
    _db, conn = _connect(db_path)
    result = conn.execute(f"CALL SHOW_CONNECTION('{rel_name}') RETURN *")
    connections: list[dict[str, Any]] = []
    for row in result:
        connections.append(
            {
                "source_table_name": row[0],
                "destination_table_name": row[1],
                "source_table_primary_key": row[2],
                "destination_table_primary_key": row[3],
            }
        )
    return connections


# ---------------------------------------------------------------------------
# Data browsing
# ---------------------------------------------------------------------------

def get_node_count(db_path: str, table_name: str) -> int:
    """Return the total number of nodes in *table_name*."""
    _db, conn = _connect(db_path)
    result = conn.execute(f"MATCH (n:`{table_name}`) RETURN COUNT(n)")
    for row in result:
        return int(row[0])
    return 0


def get_node_rows(
    db_path: str,
    table_name: str,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Return paginated node rows as dicts."""
    _db, conn = _connect(db_path)
    query = (
        f"MATCH (n:`{table_name}`) RETURN n.* SKIP {offset} LIMIT {limit}"
    )
    result = conn.execute(query)
    rows: list[dict[str, Any]] = []
    for row in result.rows_as_dict():
        rows.append(dict(row))
    return rows


def get_rel_count(db_path: str, rel_name: str) -> int:
    """Return the total number of relationships of type *rel_name*."""
    _db, conn = _connect(db_path)
    result = conn.execute(
        f"MATCH ()-[r:`{rel_name}`]->() RETURN COUNT(r)"
    )
    for row in result:
        return int(row[0])
    return 0


def get_rel_rows(
    db_path: str,
    rel_name: str,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Return paginated relationship rows as dicts."""
    _db, conn = _connect(db_path)
    query = (
        f"MATCH (a)-[r:`{rel_name}`]->(b) "
        f"RETURN a.*, r.*, b.* SKIP {offset} LIMIT {limit}"
    )
    result = conn.execute(query)
    rows: list[dict[str, Any]] = []
    for row in result.rows_as_dict():
        rows.append(dict(row))
    return rows


# ---------------------------------------------------------------------------
# Graph data for Sigma.js visualisation
# ---------------------------------------------------------------------------

def get_graph_data(
    db_path: str,
    node_limit: int = 200,
) -> dict[str, Any]:
    """Build a JSON-serialisable graph payload for Sigma.js.

    Returns ``{"nodes": [...], "edges": [...]}``.
    Nodes and edges are collected from *all* tables (capped at *node_limit* per
    node table and a proportional edge limit).
    """
    tables = list_tables(db_path)
    node_tables = [t for t in tables if t["type"] == "NODE"]
    rel_tables = [t for t in tables if t["type"] == "REL"]

    nodes: list[dict[str, Any]] = []
    node_id_set: set[str] = set()

    # Collect nodes
    for idx, nt in enumerate(node_tables):
        info = get_table_info(db_path, nt["name"])
        pk_col = next((c["name"] for c in info if c["primary_key"]), info[0]["name"] if info else "id")
        _db, conn = _connect(db_path)
        result = conn.execute(
            f"MATCH (n:`{nt['name']}`) RETURN n.* LIMIT {node_limit}"
        )
        for row in result.rows_as_dict():
            d = dict(row)
            pk_val = d.get(f"n.{pk_col}", "")
            node_id = f"{nt['name']}:{pk_val}"
            if node_id not in node_id_set:
                node_id_set.add(node_id)
                # Build label from either a 'name'/'username' column or the pk
                label = str(
                    d.get(f"n.name", d.get(f"n.username", pk_val))
                )
                nodes.append(
                    {
                        "id": node_id,
                        "label": label,
                        "table": nt["name"],
                        "tableIndex": idx,
                        "attributes": {
                            k.replace("n.", ""): _serialise(v) for k, v in d.items()
                        },
                    }
                )

    # Collect edges
    edges: list[dict[str, Any]] = []
    for rt in rel_tables:
        conn_info = get_connection_info(db_path, rt["name"])
        if not conn_info:
            continue
        ci = conn_info[0]
        src_table = ci["source_table_name"]
        dst_table = ci["destination_table_name"]
        src_pk = ci["source_table_primary_key"]
        dst_pk = ci["destination_table_primary_key"]

        _db, conn = _connect(db_path)
        result = conn.execute(
            f"MATCH (a:`{src_table}`)-[r:`{rt['name']}`]->(b:`{dst_table}`) "
            f"RETURN a.`{src_pk}`, b.`{dst_pk}`, r.* "
            f"LIMIT {node_limit * 2}"
        )
        for row in result.rows_as_dict():
            d = dict(row)
            src_id = f"{src_table}:{d.get(f'a.{src_pk}', '')}"
            dst_id = f"{dst_table}:{d.get(f'b.{dst_pk}', '')}"
            if src_id in node_id_set and dst_id in node_id_set:
                edge_attrs = {
                    k.replace("r.", ""): _serialise(v)
                    for k, v in d.items()
                    if k.startswith("r.")
                }
                edges.append(
                    {
                        "source": src_id,
                        "target": dst_id,
                        "label": rt["name"],
                        "attributes": edge_attrs,
                    }
                )

    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Arbitrary Cypher
# ---------------------------------------------------------------------------

def run_cypher(db_path: str, query: str) -> dict[str, Any]:
    """Execute an arbitrary Cypher query and return columns + rows."""
    _db, conn = _connect(db_path)
    result = conn.execute(query)
    rows: list[list[Any]] = []
    columns: list[str] = []
    for row in result:
        if not columns:
            columns = [f"col_{i}" for i in range(len(row))]
        rows.append([_serialise(v) for v in row])
    return {"columns": columns, "rows": rows}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _serialise(value: Any) -> Any:
    """Ensure *value* is JSON-serialisable."""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    return str(value)
