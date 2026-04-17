import logging

from fastapi import Request
from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PIntakeFormControllerService
from openg2p_registry_core.schemas import (
    SaveSubmissionDraftRequest, FinalizeSubmissionRequest, ApproveRejectSubmissionRequest, SubmissionResponse, SubmissionResponsePayload,
    GetSubmissionRequest,
    SearchInSubmissionRequest, SubmissionSearchResultsResponse,
    GetIntakeFormSubmissionsSummaryRequest, IntakeFormSubmissionsSummaryResponse, IntakeFormSubmissionsSummaryData,
    GetChangeRequestsForSubmissionRequest, ChangeRequestFlattenedDataResponse,
    GetNumberOfPendingChangeRequestsForSubmissionRequest,
    NumberOfPendingChangeRequestsForSubmissionResponse, NumberOfPendingChangeRequestsForSubmissionData
)
from openg2p_fastapi_common.schemas import G2PResponse
from iam_core.user_auth.helpers import require_permissions

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
        self.router.add_api_route(
            "/get_change_requests_for_submission",
            self.get_change_requests_for_submission,
            responses={200: {"model": ChangeRequestFlattenedDataResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_number_of_pending_change_requests_for_submission",
            self.get_number_of_pending_change_requests_for_submission,
            responses={200: {"model": NumberOfPendingChangeRequestsForSubmissionResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_intake_form_submissions_summary",
            self.get_intake_form_submissions_summary,
            responses={200: {"model": IntakeFormSubmissionsSummaryResponse}},
            methods=["POST"],
        )

    @require_permissions({"intakeForm:create"})
    async def save_submission_draft(self, request: Request, save_submission_draft_request: SaveSubmissionDraftRequest) -> SubmissionResponse:
        try:
            save_submission_draft_request.request_body.request_payload.created_by = getattr(request.state.auth, "name", "Unknown")
            submission_response_payload: SubmissionResponsePayload = await self.g2p_intake_form_controller_service.save_submission_draft(save_submission_draft_request)
            submission_response: SubmissionResponse = self.helper.construct_submission_success_response(
                submission_response_payload=submission_response_payload, g2p_request=save_submission_draft_request
            )
            return submission_response
        except Exception as error_exception:
            _logger.error(f"Error in save_submission_draft: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, save_submission_draft_request)
            return error_response

    @require_permissions({"intakeForm:create"})
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

    @require_permissions({"intakeForm:approve"})
    async def approve_submission(self, request: Request, approve_submission_request: ApproveRejectSubmissionRequest) -> SubmissionResponse:
        try:
            approve_submission_request.request_body.request_payload.approved_by = getattr(request.state.auth, "name", "Unknown")
            submission_response_payload: SubmissionResponsePayload = await self.g2p_intake_form_controller_service.approve_submission(approve_submission_request)
            submission_response: SubmissionResponse = self.helper.construct_submission_success_response(
                submission_response_payload=submission_response_payload, g2p_request=approve_submission_request
            )
            return submission_response
        except Exception as error_exception:
            _logger.error(f"Error in approve_submission: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, approve_submission_request)
            return error_response

    @require_permissions({"intakeForm:approve"})
    async def reject_submission(self, request: Request, reject_submission_request: ApproveRejectSubmissionRequest) -> SubmissionResponse:
        try:
            reject_submission_request.request_body.request_payload.approved_by = getattr(request.state.auth, "name", "Unknown")
            submission_response_payload: SubmissionResponsePayload = await self.g2p_intake_form_controller_service.reject_submission(reject_submission_request)
            submission_response: SubmissionResponse = self.helper.construct_submission_success_response(
                submission_response_payload=submission_response_payload, g2p_request=reject_submission_request
            )
            return submission_response
        except Exception as error_exception:
            _logger.error(f"Error in reject_submission: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(error_exception, reject_submission_request)
            return error_response

    @require_permissions({"intakeForm:view"})
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

    @require_permissions({"intakeForm:view"})
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

    @require_permissions({"changeRequest:view"})
    async def get_change_requests_for_submission(
        self, get_change_requests_for_submission_request: GetChangeRequestsForSubmissionRequest
    ) -> ChangeRequestFlattenedDataResponse:
        try:
            change_requests_list, total_items, number_of_pages = (
                await self.g2p_intake_form_controller_service.get_change_requests_for_submission(
                    get_change_requests_for_submission_request
                )
            )
            response: ChangeRequestFlattenedDataResponse = (
                self.helper.construct_change_requests_success_response(
                    change_requests_list=change_requests_list,
                    g2p_request=get_change_requests_for_submission_request,
                    number_of_items=total_items,
                    number_of_pages=number_of_pages,
                )
            )
            return response
        except Exception as error_exception:
            _logger.error(f"Error in get_change_requests_for_submission: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(
                error_exception, get_change_requests_for_submission_request
            )
            return error_response

    @require_permissions({"changeRequest:view"})
    async def get_number_of_pending_change_requests_for_submission(
        self,
        get_number_of_pending_change_requests_for_submission_request: GetNumberOfPendingChangeRequestsForSubmissionRequest
    ) -> NumberOfPendingChangeRequestsForSubmissionResponse:
        try:
            pending_count_data: NumberOfPendingChangeRequestsForSubmissionData = (
                await self.g2p_intake_form_controller_service.get_number_of_pending_change_requests_for_submission(
                    get_number_of_pending_change_requests_for_submission_request
                )
            )
            response: NumberOfPendingChangeRequestsForSubmissionResponse = (
                self.helper.construct_number_of_pending_change_requests_for_submission_success_response(
                    number_of_pending_change_requests_for_submission_data=pending_count_data,
                    g2p_request=get_number_of_pending_change_requests_for_submission_request,
                )
            )
            return response
        except Exception as error_exception:
            _logger.error(
                f"Error in get_number_of_pending_change_requests_for_submission: {str(error_exception)}"
            )
            error_response: G2PResponse = self.helper.construct_error_response(
                error_exception, get_number_of_pending_change_requests_for_submission_request
            )
            return error_response

    @require_permissions({})
    async def get_intake_form_submissions_summary(
        self, get_intake_form_submissions_summary_request: GetIntakeFormSubmissionsSummaryRequest
    ) -> IntakeFormSubmissionsSummaryResponse:
        try:
            summary_data: IntakeFormSubmissionsSummaryData = await self.g2p_intake_form_controller_service.get_intake_form_submissions_summary(
                get_intake_form_submissions_summary_request
            )
            summary_response: IntakeFormSubmissionsSummaryResponse = self.helper.construct_intake_form_submissions_summary_success_response(
                summary_data=summary_data,
                g2p_request=get_intake_form_submissions_summary_request,
            )
            return summary_response
        except Exception as error_exception:
            _logger.error(f"Error in get_intake_form_submissions_summary: {str(error_exception)}")
            error_response: G2PResponse = self.helper.construct_error_response(
                error_exception, get_intake_form_submissions_summary_request
            )
            return error_response
