import logging

from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PIntakeFormControllerService
from openg2p_registry_core.schemas import (
    SaveIntakeFormRequest, FinalizeIntakeFormRequest, ApproveRejectIntakeFormRequest, IntakeFormResponse, IntakeFormResponsePayload,
    GetIntakeFormRequest, GetAllIntakeFormsRequest,
    IntakeFormsDataResponse,
    SearchIntakeFormRequest, IntakeFormSearchResultsResponse
)
from openg2p_fastapi_common.schemas import G2PResponse

from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)

class G2PIntakeFormMetadataController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["/intake-form-metadata"]
        self.g2p_intake_form_controller_service = G2PIntakeFormControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/intake-form-metadata"

        self.router.add_api_route(
            "/get_intake_form",
            self.get_intake_form,
            responses={200: {"model": IntakeFormResponse}},
            methods=["POST"],
        )

    async def get_intake_form(self, get_intake_form_request: GetIntakeFormRequest) -> IntakeFormResponse:
        try:
            intake_form_response_payload: IntakeFormResponsePayload = await self.g2p_intake_form_controller_service.get_intake_form(get_intake_form_request)
            intake_form_response: IntakeFormResponse = self.helper.construct_intake_form_success_response(
                intake_form_response_payload=intake_form_response_payload, g2p_request=get_intake_form_request
            )
            return intake_form_response
        except Exception as error_exception:
            _logger.error(f"Error in get_intake_form: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, get_intake_form_request)
            return error_response
