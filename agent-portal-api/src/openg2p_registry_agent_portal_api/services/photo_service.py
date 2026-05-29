import base64
import io
import logging

from minio import Minio
from openg2p_fastapi_common.service import BaseService
from PIL import Image

from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class PhotoService(BaseService):
    """Fetches a registrant's photo from MINIO by object key and prepares it.

    The Registry stores the photo in MINIO and exposes only the OBJECT KEY in
    the view (not the bytes). This service GETs the object, and produces:
      • a tiny base64 JPEG thumbnail for the claim-169 QR (a QR holds ~2.9 KB),
      • a base64 data-URI of the (full) image for the printed card.
    """

    _client: Minio | None = None

    def _minio(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                _config.minio_endpoint,
                access_key=_config.minio_access_key,
                secret_key=_config.minio_secret_key,
                secure=_config.minio_secure,
            )
        return self._client

    def fetch(self, object_key: str) -> bytes:
        resp = self._minio().get_object(_config.minio_bucket, object_key)
        try:
            return resp.read()
        finally:
            resp.close()
            resp.release_conn()

    def thumbnail_b64(self, image_bytes: bytes) -> str:
        """Small base64 JPEG (no data-URI prefix) for the claim-169 `face` claim."""
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((_config.photo_thumbnail_max_px, _config.photo_thumbnail_max_px))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=_config.photo_thumbnail_quality, optimize=True)
        return base64.b64encode(buf.getvalue()).decode()

    @staticmethod
    def data_uri(image_bytes: bytes, mime: str = "image/jpeg") -> str:
        """Full-quality base64 data-URI for embedding in the SVG/PDF card."""
        return f"data:{mime};base64,{base64.b64encode(image_bytes).decode()}"
