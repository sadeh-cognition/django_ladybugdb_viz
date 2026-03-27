"""Internal JSON API endpoints consumed by the ladybug_viz front-end."""

from __future__ import annotations

from ninja import NinjaAPI, Router

from ladybug_viz import services
from ladybug_viz.schemas import (
    CypherRequestSchema,
    CypherResponseSchema,
    ErrorSchema,
    GraphDataSchema,
    PaginatedRowsSchema,
)

router = Router()


@router.get(
    "/{db_name}/tables/{table_name}/rows",
    response={200: PaginatedRowsSchema, 400: ErrorSchema},
)
def get_table_rows(
    request,  # noqa: ANN001
    db_name: str,
    table_name: str,
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, PaginatedRowsSchema | ErrorSchema]:
    """Return paginated rows for a node or relationship table."""
    db_path = f"{db_name}.lbug"
    try:
        tables = services.list_tables(db_path)
        table_entry = next((t for t in tables if t["name"] == table_name), None)
        if table_entry is None:
            return 400, ErrorSchema(detail=f"Table '{table_name}' not found")

        if table_entry["type"] == "NODE":
            rows = services.get_node_rows(db_path, table_name, limit, offset)
            total = services.get_node_count(db_path, table_name)
        else:
            rows = services.get_rel_rows(db_path, table_name, limit, offset)
            total = services.get_rel_count(db_path, table_name)

        return 200, PaginatedRowsSchema(
            rows=rows, total_count=total, limit=limit, offset=offset
        )
    except Exception as exc:
        return 400, ErrorSchema(detail=str(exc))


@router.post(
    "/{db_name}/cypher",
    response={200: CypherResponseSchema, 400: ErrorSchema},
)
def execute_cypher(
    request,  # noqa: ANN001
    db_name: str,
    payload: CypherRequestSchema,
) -> tuple[int, CypherResponseSchema | ErrorSchema]:
    """Execute an arbitrary Cypher query."""
    db_path = f"{db_name}.lbug"
    try:
        result = services.run_cypher(db_path, payload.query)
        return 200, CypherResponseSchema(**result)
    except Exception as exc:
        return 400, ErrorSchema(detail=str(exc))


@router.get(
    "/{db_name}/graph",
    response={200: GraphDataSchema, 400: ErrorSchema},
)
def get_graph_data(
    request,  # noqa: ANN001
    db_name: str,
    node_limit: int = 200,
) -> tuple[int, GraphDataSchema | ErrorSchema]:
    """Return graph data (nodes + edges) for Sigma.js visualisation."""
    db_path = f"{db_name}.lbug"
    try:
        data = services.get_graph_data(db_path, node_limit=node_limit)
        return 200, GraphDataSchema(**data)
    except Exception as exc:
        return 400, ErrorSchema(detail=str(exc))


# ---------------------------------------------------------------------------
# Standalone NinjaAPI instance (used in urls.py)
# ---------------------------------------------------------------------------

api = NinjaAPI(urls_namespace="ladybug_viz_api", docs_url=None)
api.add_router("/", router)
