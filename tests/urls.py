"""URL configuration for tests — includes the ladybug_viz URLs."""

from django.urls import include, path

urlpatterns = [
    path("ladybug-viz/", include("ladybug_viz.urls")),
]
