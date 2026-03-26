import logging

from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.schemas import G2PResponse

from openg2p_registry_core.controller_services import (
    G2PChangeRequestCoreControllerService,
)
from openg2p_registry_core.schemas import (
    ChangeRequestRequest,
    ChangeRequestResponse,
    ChangeRequestResponsePayload,
)

from ..config import Settings
from ..helpers import RequestResponseHelper

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class G2PChangeRequestCoreController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["/change-requests-core-data"]
        self.router.prefix = "/change-requests-core-data"
        self.g2p_change_request_core_controller_service = (
            G2PChangeRequestCoreControllerService.get_component()
        )
        self.helper = RequestResponseHelper.get_component()

        self.router.add_api_route(
            "/create_change_request_for_core_data",
            self.create_change_request_for_core_data,
            responses={200: {"model": ChangeRequestResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/approve_change_request_for_core_data",
            self.approve_change_request_for_core_data,
            responses={200: {"model": ChangeRequestResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/reject_change_request_for_core_data",
            self.reject_change_request_for_core_data,
            responses={200: {"model": ChangeRequestResponse}},
            methods=["POST"],
        )

    async def create_change_request_for_core_data(
        self, change_request_request: ChangeRequestRequest
    ) -> ChangeRequestResponse:
        try:
            payload: ChangeRequestResponsePayload = await self.g2p_change_request_core_controller_service.create_change_request_for_core_data(
                change_request_request
            )
            return self.helper.construct_change_request_success_response(
                change_request_response_payload=payload,
                g2p_request=change_request_request,
            )
        except Exception as error_exception:
            _logger.error(
                "Error in create_change_request_for_core_data: %s",
                str(error_exception),
            )
            error_response: G2PResponse = self.helper.construct_error_response(
                error_exception, change_request_request
            )
            return error_response

    async def approve_change_request_for_core_data(
        self, change_request_request: ChangeRequestRequest
    ) -> ChangeRequestResponse:
        try:
            payload: ChangeRequestResponsePayload = await self.g2p_change_request_core_controller_service.approve_change_request_for_core_data(
                change_request_request
            )
            return self.helper.construct_change_request_success_response(
                change_request_response_payload=payload,
                g2p_request=change_request_request,
            )
        except Exception as error_exception:
            _logger.error(
                "Error in approve_change_request_for_core_data: %s",
                str(error_exception),
            )
            error_response: G2PResponse = self.helper.construct_error_response(
                error_exception, change_request_request
            )
            return error_response

    async def reject_change_request_for_core_data(
        self, change_request_request: ChangeRequestRequest
    ) -> ChangeRequestResponse:
        try:
            payload: ChangeRequestResponsePayload = await self.g2p_change_request_core_controller_service.reject_change_request_for_core_data(
                change_request_request
            )
            return self.helper.construct_change_request_success_response(
                change_request_response_payload=payload,
                g2p_request=change_request_request,
            )
        except Exception as error_exception:
            _logger.error(
                "Error in reject_change_request_for_core_data: %s",
                str(error_exception),
            )
            error_response: G2PResponse = self.helper.construct_error_response(
                error_exception, change_request_request
            )
            return error_response
