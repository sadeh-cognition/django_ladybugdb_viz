"""Ninja schemas for the ladybug_viz internal API."""

from __future__ import annotations

from typing import Any

from ninja import Schema


class TableInfoSchema(Schema):
    id: int
    name: str
    type: str
    database_name: str
    comment: str


class ColumnInfoSchema(Schema):
    property_id: int
    name: str
    type: str
    default_expression: str | None
    primary_key: bool


class ConnectionInfoSchema(Schema):
    source_table_name: str
    destination_table_name: str
    source_table_primary_key: str
    destination_table_primary_key: str


class PaginatedRowsSchema(Schema):
    rows: list[dict[str, Any]]
    total_count: int
    limit: int
    offset: int


class CypherRequestSchema(Schema):
    query: str


class CypherResponseSchema(Schema):
    columns: list[str]
    rows: list[list[Any]]


class GraphNodeSchema(Schema):
    id: str
    label: str
    table: str
    tableIndex: int
    attributes: dict[str, Any]


class GraphEdgeSchema(Schema):
    source: str
    target: str
    label: str
    attributes: dict[str, Any]


class GraphDataSchema(Schema):
    nodes: list[GraphNodeSchema]
    edges: list[GraphEdgeSchema]


class ErrorSchema(Schema):
    detail: str
