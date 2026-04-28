import logging

from fastapi import Request
from iam_core.user_auth.helpers import require_permissions
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.schemas import G2PPaginationResponse, G2PResponse
from openg2p_registry_core.controller_services import G2PIntakeFormDataControllerService
from openg2p_registry_core.schemas import (
    ApproveRejectSubmissionRequest,
    SaveIntakeFormSubmissionRequest,
    DeleteIntakeFormSubmissionRequest,
    FinalizeSubmissionRequest,
    GetSubmissionRequest,
    GetDeduplicationIntakeFormRegisterResultsRequest,
    GetDeduplicationIntakeFormIntakeFormResultsRequest,
    DeduplicationIntakeFormRegisterResultsResponse,
    DeduplicationIntakeFormRegisterResultsResponseBody,
    DeduplicationIntakeFormIntakeFormResultsResponse,
    DeduplicationIntakeFormIntakeFormResultsResponseBody,
    SearchInSubmissionRequest,
    SubmissionResponse,
    SubmissionResponseBody,
    SubmissionResponsePayload,
    SubmissionSearchResultsResponse,
    SubmissionSearchResultsResponseBody,
)

from ..config import Settings
from ..helpers import RequestResponseHelper

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class G2PIntakeFormDataController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["/intake-form-data"]
        self.service = G2PIntakeFormDataControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/intake-form-data"

        self.router.add_api_route(
            "/save_intake_form_submission",
            self.save_intake_form_submission,
            responses={200: {"model": SubmissionResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/finalize_intake_form_submission",
            self.finalize_intake_form_submission,
            responses={200: {"model": SubmissionResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/delete_intake_form_submission",
            self.delete_intake_form_submission,
            responses={200: {"model": SubmissionResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/approve_intake_form_submission",
            self.approve_intake_form_submission,
            responses={200: {"model": SubmissionResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/reject_intake_form_submission",
            self.reject_intake_form_submission,
            responses={200: {"model": SubmissionResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_intake_form_submission",
            self.get_intake_form_submission,
            responses={200: {"model": SubmissionResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/search_in_intake_form_submissions",
            self.search_in_intake_form_submissions,
            responses={200: {"model": SubmissionSearchResultsResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_deduplication_intake_form_register_results",
            self.get_deduplication_intake_form_register_results,
            responses={200: {"model": DeduplicationIntakeFormRegisterResultsResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_deduplication_intake_form_intake_form_results",
            self.get_deduplication_intake_form_intake_form_results,
            responses={200: {"model": DeduplicationIntakeFormIntakeFormResultsResponse}},
            methods=["POST"],
        )

    @require_permissions({"intakeForm:create"})
    async def save_intake_form_submission(
        self,
        request: Request,
        g2p_request: SaveIntakeFormSubmissionRequest,
    ) -> SubmissionResponse:
        try:
            g2p_request.request_body.request_payload.created_by = getattr(request.state.auth, "name", "Unknown")
            payload: SubmissionResponsePayload = await self.service.save_intake_form_submission(
                g2p_request
            )
            return self.helper.construct_success_response(
                SubmissionResponseBody(response_payload=payload),
                g2p_request,
            )
        except Exception as error_exception:
            _logger.error("Error in save_intake_form_submission: %s", error_exception)
            return self.helper.construct_error_response(error_exception, g2p_request)

    @require_permissions({"intakeForm:create"})
    async def finalize_intake_form_submission(
        self,
        g2p_request: FinalizeSubmissionRequest,
    ) -> SubmissionResponse:
        try:
            payload: SubmissionResponsePayload = await self.service.finalize_intake_form_submission(
                g2p_request
            )
            return self.helper.construct_success_response(
                SubmissionResponseBody(response_payload=payload),
                g2p_request,
            )
        except Exception as error_exception:
            _logger.error("Error in finalize_intake_form_submission: %s", error_exception)
            return self.helper.construct_error_response(error_exception, g2p_request)

    @require_permissions({"intakeForm:create"})
    async def delete_intake_form_submission(
        self,
        g2p_request: DeleteIntakeFormSubmissionRequest,
    ) -> SubmissionResponse:
        try:
            payload: SubmissionResponsePayload = await self.service.delete_intake_form_submission(
                g2p_request
            )
            return self.helper.construct_success_response(
                SubmissionResponseBody(response_payload=payload),
                g2p_request,
            )
        except Exception as error_exception:
            _logger.error("Error in delete_intake_form_submission: %s", error_exception)
            return self.helper.construct_error_response(error_exception, g2p_request)

    @require_permissions({"intakeForm:approve"})
    async def approve_intake_form_submission(
        self,
        request: Request,
        g2p_request: ApproveRejectSubmissionRequest,
    ) -> SubmissionResponse:
        try:
            g2p_request.request_body.request_payload.approved_by = getattr(request.state.auth, "name", "Unknown")
            payload: SubmissionResponsePayload = await self.service.approve_intake_form_submission(
                g2p_request
            )
            return self.helper.construct_success_response(
                SubmissionResponseBody(response_payload=payload),
                g2p_request,
            )
        except Exception as error_exception:
            _logger.error("Error in approve_intake_form_submission: %s", error_exception)
            return self.helper.construct_error_response(error_exception, g2p_request)

    @require_permissions({"intakeForm:approve"})
    async def reject_intake_form_submission(
        self,
        request: Request,
        g2p_request: ApproveRejectSubmissionRequest,
    ) -> SubmissionResponse:
        try:
            g2p_request.request_body.request_payload.approved_by = getattr(request.state.auth, "name", "Unknown")
            payload: SubmissionResponsePayload = await self.service.reject_intake_form_submission(
                g2p_request
            )
            return self.helper.construct_success_response(
                SubmissionResponseBody(response_payload=payload),
                g2p_request,
            )
        except Exception as error_exception:
            _logger.error("Error in reject_intake_form_submission: %s", error_exception)
            return self.helper.construct_error_response(error_exception, g2p_request)

    @require_permissions({"intakeForm:view"})
    async def get_intake_form_submission(
        self,
        g2p_request: GetSubmissionRequest,
    ) -> SubmissionResponse:
        try:
            payload: SubmissionResponsePayload = await self.service.get_intake_form_submission(
                g2p_request
            )
            return self.helper.construct_success_response(
                SubmissionResponseBody(response_payload=payload),
                g2p_request,
            )
        except Exception as error_exception:
            _logger.error("Error in get_intake_form_submission: %s", error_exception)
            return self.helper.construct_error_response(error_exception, g2p_request)

    @require_permissions({"intakeForm:view"})
    async def search_in_intake_form_submissions(
        self,
        g2p_request: SearchInSubmissionRequest,
    ) -> SubmissionSearchResultsResponse:
        try:
            payloads, total_items, number_of_pages = await self.service.search_in_intake_form_submissions(
                g2p_request
            )
            return self.helper.construct_success_response(
                SubmissionSearchResultsResponseBody(response_payload=payloads),
                g2p_request,
                G2PPaginationResponse(
                    number_of_items=total_items,
                    number_of_pages=number_of_pages,
                ),
            )
        except Exception as error_exception:
            _logger.error("Error in search_in_intake_form_submissions: %s", error_exception)
            return self.helper.construct_error_response(error_exception, g2p_request)

    @require_permissions({"register:view"})
    async def get_deduplication_intake_form_register_results(
        self,
        g2p_request: GetDeduplicationIntakeFormRegisterResultsRequest,
    ) -> DeduplicationIntakeFormRegisterResultsResponse:
        try:
            results, total_items, number_of_pages = await self.service.get_deduplication_intake_form_register_results(
                g2p_request
            )
            return self.helper.construct_success_response(
                DeduplicationIntakeFormRegisterResultsResponseBody(
                    response_payload=results,
                    number_of_items=total_items,
                    number_of_pages=number_of_pages,
                ),
                g2p_request,
            )
        except Exception as error_exception:
            _logger.error("Error in get_deduplication_intake_form_register_results: %s", error_exception)
            return self.helper.construct_error_response(error_exception, g2p_request)

    @require_permissions({"register:view"})
    async def get_deduplication_intake_form_intake_form_results(
        self,
        g2p_request: GetDeduplicationIntakeFormIntakeFormResultsRequest,
    ) -> DeduplicationIntakeFormIntakeFormResultsResponse:
        try:
            results, total_items, number_of_pages = await self.service.get_deduplication_intake_form_intake_form_results(
                g2p_request
            )
            return self.helper.construct_success_response(
                DeduplicationIntakeFormIntakeFormResultsResponseBody(
                    response_payload=results,
                    number_of_items=total_items,
                    number_of_pages=number_of_pages,
                ),
                g2p_request,
            )
        except Exception as error_exception:
            _logger.error("Error in get_deduplication_intake_form_intake_form_results: %s", error_exception)
            return self.helper.construct_error_response(error_exception, g2p_request)
