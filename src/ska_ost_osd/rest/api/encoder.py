"""JSON encoder for OSD REST API responses."""
import json
from typing import Any


class FloatPreservingJSONEncoder(json.JSONEncoder):
    """JSON encoder that preserves floating point numbers."""

    def default(self, obj: Any) -> Any:
        """Encode the object."""
        if isinstance(obj, float):
            return format(obj, ".1f")  # Ensure at least one decimal place is preserved
        return super().default(obj)

    def encode(self, obj: Any) -> str:
        """Custom encode method to preserve float format."""
        if isinstance(obj, (dict, list)):

            def convert(item):
                if isinstance(item, float):
                    return format(item, ".1f")
                elif isinstance(item, dict):
                    return {k: convert(v) for k, v in item.items()}
                elif isinstance(item, list):
                    return [convert(i) for i in item]
                return item

            obj = convert(obj)
        return super().encode(obj)
