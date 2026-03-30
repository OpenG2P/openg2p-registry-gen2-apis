import logging

from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PIntakeFormControllerService
from openg2p_registry_core.schemas import (
    GetIntakeFormsForRegisterRequest,
    GetIntakeFormMetadataRequest,
    IntakeFormsForRegisterResponse,
    IntakeFormMetadataResponse,
)
from openg2p_fastapi_common.schemas import G2PResponse
from iam_core.user_auth.helpers import require_permissions

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
            "/get_intake_forms_for_register",
            self.get_intake_forms_for_register,
            responses={200: {"model": IntakeFormsForRegisterResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_intake_form",
            self.get_intake_form,
            responses={200: {"model": IntakeFormMetadataResponse}},
            methods=["POST"],
        )

    @require_permissions({"intakeForm:view"})
    async def get_intake_forms_for_register(
        self, get_intake_forms_for_register_request: GetIntakeFormsForRegisterRequest
    ) -> IntakeFormsForRegisterResponse:
        try:
            intake_forms_list, total_items, number_of_pages = await self.g2p_intake_form_controller_service.get_intake_forms_for_register(
                get_intake_forms_for_register_request
            )
            response: IntakeFormsForRegisterResponse = self.helper.construct_intake_forms_for_register_success_response(
                intake_forms_list=intake_forms_list,
                g2p_request=get_intake_forms_for_register_request,
                number_of_items=total_items,
                number_of_pages=number_of_pages,
            )
            return response
        except Exception as error_exception:
            _logger.error(f"Error in get_intake_forms_for_register: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(
                error_exception, get_intake_forms_for_register_request
            )
            return error_response

    @require_permissions({"intakeForm:view"})
    async def get_intake_form(
        self, get_intake_form_metadata_request: GetIntakeFormMetadataRequest
    ) -> IntakeFormMetadataResponse:
        try:
            intake_form_sections_list, total_items, number_of_pages = await self.g2p_intake_form_controller_service.get_intake_form_metadata(
                get_intake_form_metadata_request
            )
            response: IntakeFormMetadataResponse = self.helper.construct_intake_form_metadata_success_response(
                intake_form_sections_list=intake_form_sections_list,
                g2p_request=get_intake_form_metadata_request,
                number_of_items=total_items,
                number_of_pages=number_of_pages,
            )
            return response
        except Exception as error_exception:
            _logger.error(f"Error in get_intake_form: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(
                error_exception, get_intake_form_metadata_request
            )
            return error_response
