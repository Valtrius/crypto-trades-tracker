import json
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Convert Decimal to string
        # Let the base class default method raise the TypeError
        return super(DecimalEncoder, self).default(obj)
