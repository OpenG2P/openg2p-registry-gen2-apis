#!/usr/bin/env python3

# ruff: noqa: I001

from .app import Initializer
from openg2p_fastapi_common.ping import PingInitializer
from openg2p_registry_core.app import Initializer as CoreInitializer
from openg2p_registry_extensions.app import Initializer as ExtensionsInitializer

CoreInitializer()
ExtensionsInitializer()
initializer = Initializer()
PingInitializer()

app = initializer.return_app()

if __name__ == "__main__":
    initializer.main()
