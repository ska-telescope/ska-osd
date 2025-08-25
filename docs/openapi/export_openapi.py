import json
from ska_ost_osd.app import main

def export_openapi(path: str = "openapi.json") -> None:
    """Export OpenAPI schema to a JSON file."""
    path = 'docs/openapi/openapi.json'
    with open(path, "w") as f:
        json.dump(main.openapi(), f, indent=2)