import logging
from typing import List
from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PUIHelperControllerService
from openg2p_registry_core.schemas import (
    G2PInputMechanismRequest,
    G2PInputMechanismResponse,
    G2PInputMechanismData,
)

from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class G2PUIHelperController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["/ui_helper"]
        self.g2p_ui_helper_controller_service = G2PUIHelperControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/ui_helper"

        self.router.add_api_route(
            "/get_all_input_mechanisms",
            self.get_all_input_mechanisms,
            responses={200: {"model": G2PInputMechanismResponse}},
            methods=["POST"],
        )

    async def get_all_input_mechanisms(
        self,
        request: G2PInputMechanismRequest,
    ) -> G2PInputMechanismResponse:
        _logger.debug("Get G2P Input Mechanisms Request: %s", request)
        try:
            input_mechanisms: List[G2PInputMechanismData] = await self.g2p_ui_helper_controller_service.get_all_input_mechanisms(request)
            _logger.debug("Input mechanisms: %s", input_mechanisms)

            return self.helper.construct_input_mechanisms_success_response(
                input_mechanisms, request
            )
        except Exception as e:
            _logger.error("Error getting input mechanisms: %s", str(e), exc_info=True)
            return self.helper.construct_error_response(e, request)

