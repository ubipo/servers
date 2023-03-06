import json
from typing import Any, Optional
from contextlib import closing
import secretstorage


SECRET_KEY = "server-provisioning-secrets"

_secrets: Optional[dict[str, Any]] = None


def get_secrets():
    global _secrets
    if _secrets is not None:
        return _secrets

    with closing(secretstorage.dbus_init()) as conn:
        collection = secretstorage.get_default_collection(conn)
        collection.unlock()
        items = collection.get_all_items()
        item = next(
            (item for item in items if SECRET_KEY in item.get_attributes()), None
        )
        if item is None:
            raise Exception(f'No item found with attribute/key "{SECRET_KEY}"')
        item.unlock()
        # Not using item.get_secret() because it's a single line in KeePassXC
        new_secrets: dict[str, Any] = json.loads(item.get_attributes()["secrets"])
        _secrets = new_secrets
        return new_secrets
