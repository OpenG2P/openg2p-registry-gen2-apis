from datetime import datetime
from typing import Any, Optional

from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PResponseStatus,
)
from openg2p_fastapi_common.service import BaseService

from ..schemas import (
    IssueVcResponse,
    IssueVcResponseBody,
    IssueVcResponsePayload,
)


class RequestResponseHelper(BaseService):
    def construct_success_response(
        self,
        claims: dict[str, Any],
        credential: Any,
        pdf_path: Optional[str] = None,
        g2p_request: Optional[G2PRequest] = None,
    ) -> IssueVcResponse:
        request_id = (
            g2p_request.request_header.request_id if g2p_request else ""
        )
        return IssueVcResponse(
            response_header={
                "request_id": request_id,
                "response_status": G2PResponseStatus.SUCCESS,
                "response_error_code": "",
                "response_error_message": "",
                "response_timestamp": datetime.now(),
            },
            response_body=IssueVcResponseBody(
                response_payload=IssueVcResponsePayload(
                    claims=claims, credential=credential, pdf_path=pdf_path
                )
            ),
        )

    def construct_error_response(
        self,
        error_code: str,
        error_message: str,
        g2p_request: Optional[G2PRequest] = None,
    ) -> IssueVcResponse:
        request_id = (
            g2p_request.request_header.request_id if g2p_request else ""
        )
        return IssueVcResponse(
            response_header={
                "request_id": request_id,
                "response_status": G2PResponseStatus.ERROR,
                "response_error_code": error_code,
                "response_error_message": error_message,
                "response_timestamp": datetime.now(),
            },
            response_body=IssueVcResponseBody(response_payload=None),
        )
