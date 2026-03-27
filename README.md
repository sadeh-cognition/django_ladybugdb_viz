# ladybug-viz

A reusable Django app for visualizing LadybugDB graph databases.

## Installation

```bash
pip install ladybug-viz
```

## Usage

Add `"ladybug_viz"` to your `INSTALLED_APPS`, then include the URLs:

```python
# urls.py
urlpatterns = [
    path("ladybug-viz/", include("ladybug_viz.urls")),
]
```

Visit `/ladybug-viz/<db_name>/` to explore a local `.lbug` database.
