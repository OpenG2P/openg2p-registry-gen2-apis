import base64
import gzip
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any

import qrcode
from fpdf import FPDF
from openg2p_fastapi_common.service import BaseService

from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class PdfRenderService(BaseService):
    """Renders an issued credential into a printable A4 PDF carrying a signed QR.

    Phase-1 (paper) custody: the citizen needs no device. The QR encodes the
    full Ed25519-signed Verifiable Credential (gzip + base64url) so a verifier
    (e.g. Inji Verify) can validate it offline; the human-readable fields are
    printed alongside for eyeballing.
    """

    def render(self, claims: dict[str, Any], credential: Any) -> str:
        os.makedirs(_config.pdf_output_dir, exist_ok=True)

        vc = credential.get("credential", credential) if isinstance(credential, dict) else credential
        qr_payload = self._compact_vc(vc)
        qr_img_path = self._make_qr(qr_payload)

        pdf = FPDF(format="A4")
        pdf.add_page()
        pdf.set_margins(20, 20, 20)

        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, _config.pdf_title, ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(90, 90, 90)
        pdf.cell(0, 6, f"Issued by {_config.pdf_issuer_name} on {datetime.now():%Y-%m-%d %H:%M}", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(6)

        # Human-readable claim fields.
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Credential details", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for label, key in (
            ("Full Name", "fullName"),
            ("Functional Record ID", "functionalRecordId"),
            ("Date of Birth", "dateOfBirth"),
        ):
            value = str(claims.get(key, "") or "")
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(55, 8, f"{label}:")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 8, value, ln=True)

        # Issuer / proof summary.
        pdf.ln(2)
        issuer = vc.get("issuer", "") if isinstance(vc, dict) else ""
        vc_type = ", ".join(vc.get("type", [])) if isinstance(vc, dict) else ""
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(0, 5, f"Type: {vc_type}\nIssuer: {issuer}")
        pdf.set_text_color(0, 0, 0)

        # QR code.
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Scan to verify", ln=True)
        pdf.image(qr_img_path, w=70)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(0, 4, "QR contains the Ed25519-signed Verifiable Credential (gzip+base64url). "
                             "Verify offline against the issuer's published key.")

        out_path = os.path.abspath(
            os.path.join(_config.pdf_output_dir, f"vc-{claims.get('functionalRecordId', uuid.uuid4().hex)}.pdf")
        )
        pdf.output(out_path)
        _logger.info("Rendered credential PDF to %s", out_path)
        try:
            os.remove(qr_img_path)
        except OSError:
            pass
        return out_path

    @staticmethod
    def _compact_vc(vc: Any) -> str:
        raw = json.dumps(vc, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(gzip.compress(raw)).decode()

    def _make_qr(self, payload: str) -> str:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=4, border=2)
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        tmp = os.path.join(_config.pdf_output_dir, f"qr-{uuid.uuid4().hex}.png")
        img.save(tmp)
        return tmp
