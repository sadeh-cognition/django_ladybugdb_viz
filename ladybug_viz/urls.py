"""URL configuration for the ladybug_viz app.

Consumer project includes this via::

    path("ladybug-viz/", include("ladybug_viz.urls"))
"""

from django.urls import path

from ladybug_viz import views
from ladybug_viz.api import api

app_name = "ladybug_viz"

urlpatterns = [
    # Internal JSON API
    path("api/", api.urls),
    # HTML views
    path("<str:db_name>/", views.database_overview, name="database_overview"),
    path(
        "<str:db_name>/table/<str:table_name>/",
        views.table_detail,
        name="table_detail",
    ),
    path("<str:db_name>/graph/", views.graph_view, name="graph_view"),
    path("<str:db_name>/cypher/", views.cypher_console, name="cypher_console"),
]
