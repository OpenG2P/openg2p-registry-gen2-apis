import logging

from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PIntakeFormControllerService
from openg2p_registry_core.schemas import (
    SaveSubmissionDraftRequest, FinalizeSubmissionRequest, ApproveRejectSubmissionRequest, SubmissionResponse, SubmissionResponsePayload,
    GetSubmissionRequest,
    SearchInSubmissionRequest, SubmissionSearchResultsResponse
)
from openg2p_fastapi_common.schemas import G2PResponse

from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)

class G2PIntakeFormDataController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["/intake-form-data"]
        self.g2p_intake_form_controller_service = G2PIntakeFormControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/intake-form-data"

        self.router.add_api_route(
            "/save_submission_draft",
            self.save_submission_draft,
            responses={200: {"model": SubmissionResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/finalize_submission",
            self.finalize_submission,
            responses={200: {"model": SubmissionResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/approve_submission",
            self.approve_submission,
            responses={200: {"model": SubmissionResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/reject_submission",
            self.reject_submission,
            responses={200: {"model": SubmissionResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_submission",
            self.get_submission,
            responses={200: {"model": SubmissionResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/search_in_submission",
            self.search_in_submission,
            responses={200: {"model": SubmissionSearchResultsResponse}},
            methods=["POST"],
        )

    async def save_submission_draft(self, save_submission_draft_request: SaveSubmissionDraftRequest) -> SubmissionResponse:
        try:
            submission_response_payload: SubmissionResponsePayload = await self.g2p_intake_form_controller_service.save_submission_draft(save_submission_draft_request)
            submission_response: SubmissionResponse = self.helper.construct_submission_success_response(
                submission_response_payload=submission_response_payload, g2p_request=save_submission_draft_request
            )
            return submission_response
        except Exception as error_exception:
            _logger.error(f"Error in save_submission_draft: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, save_submission_draft_request)
            return error_response

    async def finalize_submission(self, finalize_submission_request: FinalizeSubmissionRequest) -> SubmissionResponse:
        try:
            submission_response_payload: SubmissionResponsePayload = await self.g2p_intake_form_controller_service.finalize_submission(finalize_submission_request)
            submission_response: SubmissionResponse = self.helper.construct_submission_success_response(
                submission_response_payload=submission_response_payload, g2p_request=finalize_submission_request
            )
            return submission_response
        except Exception as error_exception:
            _logger.error(f"Error in finalize_submission: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, finalize_submission_request)
            return error_response

    async def approve_submission(self, approve_submission_request: ApproveRejectSubmissionRequest) -> SubmissionResponse:
        try:
            submission_response_payload: SubmissionResponsePayload = await self.g2p_intake_form_controller_service.approve_submission(approve_submission_request)
            submission_response: SubmissionResponse = self.helper.construct_submission_success_response(
                submission_response_payload=submission_response_payload, g2p_request=approve_submission_request
            )
            return submission_response
        except Exception as error_exception:
            _logger.error(f"Error in approve_submission: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, approve_submission_request)
            return error_response

    async def reject_submission(self, reject_submission_request: ApproveRejectSubmissionRequest) -> SubmissionResponse:
        try:
            submission_response_payload: SubmissionResponsePayload = await self.g2p_intake_form_controller_service.reject_submission(reject_submission_request)
            submission_response: SubmissionResponse = self.helper.construct_submission_success_response(
                submission_response_payload=submission_response_payload, g2p_request=reject_submission_request
            )
            return submission_response
        except Exception as error_exception:
            _logger.error(f"Error in reject_submission: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, reject_submission_request)
            return error_response

    async def get_submission(self, get_submission_request: GetSubmissionRequest) -> SubmissionResponse:
        try:
            submission_response_payload: SubmissionResponsePayload = await self.g2p_intake_form_controller_service.get_submission(get_submission_request)
            submission_response: SubmissionResponse = self.helper.construct_submission_success_response(
                submission_response_payload=submission_response_payload, g2p_request=get_submission_request
            )
            return submission_response
        except Exception as error_exception:
            _logger.error(f"Error in get_submission: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, get_submission_request)
            return error_response

    async def search_in_submission(self, search_in_submission_request: SearchInSubmissionRequest) -> SubmissionSearchResultsResponse:
        try:
            search_results_list, total_items, number_of_pages = await self.g2p_intake_form_controller_service.search_in_submission(search_in_submission_request)
            search_results_response: SubmissionSearchResultsResponse = self.helper.construct_submission_search_results_success_response(
                search_results_list=search_results_list, g2p_request=search_in_submission_request,
                number_of_items=total_items, number_of_pages=number_of_pages
            )
            return search_results_response
        except Exception as error_exception:
            _logger.error(f"Error in search_in_submission: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, search_in_submission_request)
            return error_response
