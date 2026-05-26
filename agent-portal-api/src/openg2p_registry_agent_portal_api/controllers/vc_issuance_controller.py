import logging

from openg2p_fastapi_common.controller import BaseController

from ..config import Settings
from ..helpers import RequestResponseHelper
from ..schemas import IssueVcRequest, IssueVcResponse
from ..services import (
    CertifyIssuanceService,
    PdfRenderService,
    RegistryLookupService,
)
from ..services.certify_issuance_service import CertifyIssuanceError
from ..services.registry_lookup_service import RegistryLookupError

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class VcIssuanceController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["Agent Portal - VC Issuance"]
        self.router.prefix = "/agent_portal"

        self.registry_lookup_service = RegistryLookupService.get_component()
        self.certify_issuance_service = CertifyIssuanceService.get_component()
        self.pdf_render_service = PdfRenderService.get_component()
        self.request_response_helper = RequestResponseHelper.get_component()

        self.router.add_api_route(
            "/issue_vc",
            self.issue_vc,
            responses={200: {"model": IssueVcResponse}},
            methods=["POST"],
        )

    async def issue_vc(self, request: IssueVcRequest) -> IssueVcResponse:
        phone = request.request_body.request_payload.phone
        _logger.debug("Issue VC request for phone: %s", phone)
        try:
            claims = await self.registry_lookup_service.get_claims_by_phone(phone)
            credential = await self.certify_issuance_service.issue(claims)
            pdf_path = self.pdf_render_service.render(claims, credential)
            return self.request_response_helper.construct_success_response(
                claims, credential, pdf_path, request
            )
        except (RegistryLookupError, CertifyIssuanceError) as e:
            _logger.error("Issuance failed: %s", e.message)
            return self.request_response_helper.construct_error_response(
                e.code, e.message, request
            )
        except Exception as e:
            _logger.exception("Unexpected issuance error")
            return self.request_response_helper.construct_error_response(
                "500", str(e), request
            )
