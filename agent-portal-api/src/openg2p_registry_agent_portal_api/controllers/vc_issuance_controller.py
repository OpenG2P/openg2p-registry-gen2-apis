import logging

from openg2p_fastapi_common.controller import BaseController

from ..config import Settings
from ..helpers import RequestResponseHelper
from ..schemas import IssueVcRequest, IssueVcResponse
from ..services import (
    CertifyIssuanceService,
    PdfRenderService,
    PhotoService,
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
        self.photo_service = PhotoService.get_component()
        self.pdf_render_service = PdfRenderService.get_component()
        self.request_response_helper = RequestResponseHelper.get_component()

        self.router.add_api_route(
            "/issue_vc",
            self.issue_vc,
            responses={200: {"model": IssueVcResponse}},
            methods=["POST"],
        )

    async def issue_vc(self, request: IssueVcRequest) -> IssueVcResponse:
        payload = request.request_body.request_payload
        phone, vc_type = payload.phone, payload.vc_type
        _logger.debug("Issue VC request for phone %s (vc_type=%s)", phone, vc_type)
        try:
            vc = _config.get_vc_definition(vc_type)
            claims, photo_key = await self.registry_lookup_service.get_claims_by_phone(
                phone, vc
            )
            # Fetch the photo from MINIO (by key) → thumbnail → push as the
            # `face` claim so Certify embeds it in the signed claim-169 QR.
            photo_bytes = None
            if vc.photo_key_column and photo_key:
                photo_bytes = self.photo_service.fetch(photo_key)
                if vc.face_claim:
                    claims[vc.face_claim] = self.photo_service.thumbnail_b64(photo_bytes)
            credential = await self.certify_issuance_service.issue(
                claims, vc.config_id, vc.credential_types
            )
            pdf_path = self.pdf_render_service.render(claims, credential, vc, photo_bytes)
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
