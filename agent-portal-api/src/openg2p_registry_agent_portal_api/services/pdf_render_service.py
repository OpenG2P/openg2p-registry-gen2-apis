import base64
import gzip
import io
import json
import logging
import os
import uuid
from typing import Any, Optional

import qrcode
from openg2p_fastapi_common.service import BaseService

from ..config import Settings, VcDefinition

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class PdfRenderService(BaseService):
    """Renders the printable paper credential.

    Primary path (Inji-aligned): fill an **SVG design template** (mounted from a
    ConfigMap, named by the VC definition) with the claim fields, the photo and
    the **claim-169 signed QR**, then convert SVG → PDF (cairosvg). The SVG is
    the design surface (logo, layout, branding) owned by the module/designer.

    Fallback (no svg_template configured): a minimal fpdf2 layout.
    """

    def render(
        self,
        claims: dict[str, Any],
        credential: Any,
        vc: VcDefinition,
        photo_bytes: Optional[bytes] = None,
    ) -> str:
        os.makedirs(_config.pdf_output_dir, exist_ok=True)
        vc_obj = credential.get("credential", credential) if isinstance(credential, dict) else credential
        qr_payload = self._qr_payload(vc_obj, vc)
        out_path = os.path.abspath(
            os.path.join(
                _config.pdf_output_dir,
                f"vc-{claims.get('functionalRecordId', uuid.uuid4().hex)}.pdf",
            )
        )
        if vc.svg_template:
            self._render_svg(out_path, claims, vc_obj, qr_payload, photo_bytes, vc)
        else:
            self._render_fpdf(out_path, claims, vc_obj, qr_payload, photo_bytes)
        _logger.info("Rendered credential PDF to %s", out_path)
        return out_path

    # ----- claim-169 QR payload (signed compact QR) -----
    def _qr_payload(self, vc_obj: Any, vc: VcDefinition) -> str:
        if vc.qr_claim_path and isinstance(vc_obj, dict):
            node: Any = vc_obj.get("credentialSubject", {})
            for part in vc.qr_claim_path.split("."):
                node = node.get(part) if isinstance(node, dict) else None
            if isinstance(node, str) and node:
                return node
            _logger.warning("claim-169 QR not found at '%s'; falling back to full-VC QR", vc.qr_claim_path)
        # Fallback: gzip+base64url of the whole VC.
        raw = json.dumps(vc_obj, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(gzip.compress(raw)).decode()

    def _qr_png_data_uri(self, payload: str) -> str:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=6, border=2)
        qr.add_data(payload)
        qr.make(fit=True)
        buf = io.BytesIO()
        qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    # ----- SVG path -----
    def _render_svg(self, out_path, claims, vc_obj, qr_payload, photo_bytes, vc):
        import cairosvg

        tmpl_path = os.path.join(_config.svg_template_dir, vc.svg_template)
        with open(tmpl_path, encoding="utf-8") as f:
            svg = f.read()

        subs = {
            "title": _config.pdf_title,
            "issuerName": _config.pdf_issuer_name,
            "issuer": str(vc_obj.get("issuer", "")) if isinstance(vc_obj, dict) else "",
            "qr": self._qr_png_data_uri(qr_payload),
            "photo": (
                "data:image/jpeg;base64," + base64.b64encode(photo_bytes).decode()
                if photo_bytes else ""
            ),
        }
        subs.update({k: str(v) for k, v in claims.items()})
        for key, val in subs.items():
            svg = svg.replace("{{" + key + "}}", val).replace("{{ " + key + " }}", val)
        cairosvg.svg2pdf(bytestring=svg.encode("utf-8"), write_to=out_path)

    # ----- fpdf2 fallback -----
    def _render_fpdf(self, out_path, claims, vc_obj, qr_payload, photo_bytes):
        from fpdf import FPDF

        pdf = FPDF(format="A4")
        pdf.add_page()
        pdf.set_margins(20, 20, 20)
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, _config.pdf_title, ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Issued by {_config.pdf_issuer_name}", ln=True)
        pdf.ln(4)
        if photo_bytes:
            try:
                pdf.image(io.BytesIO(photo_bytes), w=35)
                pdf.ln(2)
            except Exception:  # noqa: BLE001
                _logger.warning("could not place photo on fallback PDF")
        pdf.set_font("Helvetica", "", 11)
        for key, value in claims.items():
            pdf.cell(0, 8, f"{key}: {value}", ln=True)
        pdf.ln(4)
        qr_png = base64.b64decode(self._qr_png_data_uri(qr_payload).split(",", 1)[1])
        pdf.image(io.BytesIO(qr_png), w=70)
        pdf.output(out_path)
