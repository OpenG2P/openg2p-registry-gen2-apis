from typing import Any, Optional

from openg2p_fastapi_common.schemas import G2PRequest, G2PResponse
from pydantic import BaseModel


class IssueVcRequestPayload(BaseModel):
    """Identifies the registrant the agent wants to issue a credential for.

    Phase-1 lookup key is the registrant's phone number (matched against the
    Registry's beneficiary_vc_view). The agent has already verified the
    citizen's identity out-of-band (LoA1 physical-card check).
    """

    phone: str
    # Which VC to issue (a vc_definitions config_id). Defaults to the first
    # configured definition when omitted.
    vc_type: Optional[str] = None


class IssueVcRequestBody(BaseModel):
    request_payload: IssueVcRequestPayload


class IssueVcRequest(G2PRequest):
    request_body: IssueVcRequestBody


class IssueVcResponsePayload(BaseModel):
    # The claims that were resolved from the Registry and pushed to Certify.
    claims: dict[str, Any]
    # The signed Verifiable Credential as returned by Inji Certify.
    credential: Optional[Any] = None
    # Absolute path to the printable PDF (signed QR + human-readable fields).
    pdf_path: Optional[str] = None


class IssueVcResponseBody(BaseModel):
    response_payload: Optional[IssueVcResponsePayload] = None


class IssueVcResponse(G2PResponse):
    response_body: Optional[IssueVcResponseBody] = None
