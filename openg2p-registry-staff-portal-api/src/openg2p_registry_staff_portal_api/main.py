#!/usr/bin/env python3

# ruff: noqa: I001, E402
from openg2p_registry_staff_portal_api.config import Settings
Settings.get_config()

from openg2p_fastapi_common.ping import PingInitializer
from openg2p_registry_staff_portal_api.app import Initializer
from openg2p_registry_core.app import Initializer as CoreInitializer
from openg2p_registry_extensions.app import Initializer as ExtensionsInitializer

from iam_core.user_auth.app import Initializer as IAMInitializer
from iam_core.user_auth.middleware import AuthMiddleware


IAMInitializer()
CoreInitializer()
ExtensionsInitializer()
initializer = Initializer()
PingInitializer()

_config = Settings.get_config()

app = initializer.return_app()
app.add_middleware(
    AuthMiddleware,
    client_id=_config.keycloak_client_id,
    allow_by_default=True,
)

if __name__ == "__main__":
    initializer.main()
