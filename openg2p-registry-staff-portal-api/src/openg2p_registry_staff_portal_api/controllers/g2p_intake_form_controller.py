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

class G2PIntakeFormController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["/intake-forms"]
        self.g2p_intake_form_controller_service = G2PIntakeFormControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/intake-forms"

        self.router.add_api_route(
            "/save_intake_form_draft",
            self.save_intake_form_draft,
            responses={200: {"model": IntakeFormResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/finalize_intake_form",
            self.finalize_intake_form,
            responses={200: {"model": IntakeFormResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/approve_intake_form",
            self.approve_intake_form,
            responses={200: {"model": IntakeFormResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/reject_intake_form",
            self.reject_intake_form,
            responses={200: {"model": IntakeFormResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_intake_form",
            self.get_intake_form,
            responses={200: {"model": IntakeFormResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_all_intake_forms",
            self.get_all_intake_forms,
            responses={200: {"model": IntakeFormsDataResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/search_in_intake_form",
            self.search_in_intake_form,
            responses={200: {"model": IntakeFormSearchResultsResponse}},
            methods=["POST"],
        )

    async def save_intake_form_draft(self, save_intake_form_draft_request: SaveIntakeFormRequest) -> IntakeFormResponse:
        try:
            intake_form_response_payload: IntakeFormResponsePayload = await self.g2p_intake_form_controller_service.save_intake_form_draft(save_intake_form_draft_request)
            intake_form_response: IntakeFormResponse = self.helper.construct_intake_form_success_response(
                intake_form_response_payload=intake_form_response_payload, g2p_request=save_intake_form_draft_request
            )
            return intake_form_response
        except Exception as error_exception:
            _logger.error(f"Error in save_intake_form_draft: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, save_intake_form_draft_request)
            return error_response

    async def finalize_intake_form(self, finalize_intake_form_request: FinalizeIntakeFormRequest) -> IntakeFormResponse:
        try:
            intake_form_response_payload: IntakeFormResponsePayload = await self.g2p_intake_form_controller_service.finalize_intake_form(finalize_intake_form_request)
            intake_form_response: IntakeFormResponse = self.helper.construct_intake_form_success_response(
                intake_form_response_payload=intake_form_response_payload, g2p_request=finalize_intake_form_request
            )
            return intake_form_response
        except Exception as error_exception:
            _logger.error(f"Error in finalize_intake_form: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, finalize_intake_form_request)
            return error_response

    async def approve_intake_form(self, approve_intake_form_request: ApproveRejectIntakeFormRequest) -> IntakeFormResponse:
        try:
            intake_form_response_payload: IntakeFormResponsePayload = await self.g2p_intake_form_controller_service.approve_intake_form(approve_intake_form_request)
            intake_form_response: IntakeFormResponse = self.helper.construct_intake_form_success_response(
                intake_form_response_payload=intake_form_response_payload, g2p_request=approve_intake_form_request
            )
            return intake_form_response
        except Exception as error_exception:
            _logger.error(f"Error in approve_intake_form: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, approve_intake_form_request)
            return error_response

    async def reject_intake_form(self, reject_intake_form_request: ApproveRejectIntakeFormRequest) -> IntakeFormResponse:
        try:
            intake_form_response_payload: IntakeFormResponsePayload = await self.g2p_intake_form_controller_service.reject_intake_form(reject_intake_form_request)
            intake_form_response: IntakeFormResponse = self.helper.construct_intake_form_success_response(
                intake_form_response_payload=intake_form_response_payload, g2p_request=reject_intake_form_request
            )
            return intake_form_response
        except Exception as error_exception:
            _logger.error(f"Error in reject_intake_form: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, reject_intake_form_request)
            return error_response

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

    async def get_all_intake_forms(self, get_all_intake_forms_request: GetAllIntakeFormsRequest) -> IntakeFormsDataResponse:
        try:
            intake_forms_list, total_items, number_of_pages = await self.g2p_intake_form_controller_service.get_all_intake_forms(get_all_intake_forms_request)
            intake_forms_response: IntakeFormsDataResponse = self.helper.construct_intake_forms_success_response(
                intake_forms_list=intake_forms_list, g2p_request=get_all_intake_forms_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return intake_forms_response
        except Exception as error_exception:
            _logger.error(f"Error in get_all_intake_forms: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, get_all_intake_forms_request)
            return error_response

    async def search_in_intake_form(self, search_intake_form_request: SearchIntakeFormRequest) -> IntakeFormSearchResultsResponse:
        try:
            search_results_list, total_items, number_of_pages = await self.g2p_intake_form_controller_service.search_in_intake_form(search_intake_form_request)
            search_results_response: IntakeFormSearchResultsResponse = self.helper.construct_intake_form_search_results_success_response(
                search_results_list=search_results_list, g2p_request=search_intake_form_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return search_results_response
        except Exception as error_exception:
            _logger.error(f"Error in search_in_intake_form: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, search_intake_form_request)
            return error_response

