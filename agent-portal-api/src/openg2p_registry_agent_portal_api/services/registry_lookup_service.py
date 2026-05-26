import logging
from typing import Any, Optional

from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.service import BaseService
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class RegistryLookupError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class RegistryLookupService(BaseService):
    """Resolves a registrant's VC claims from the Registry's read-only view.

    The view (default: ``beneficiary_vc_view``) is phone-keyed and active-only;
    each row's columns become the credential claims. Phase-1 binds the lookup
    key to the registrant's phone number.
    """

    async def get_claims_by_phone(self, phone: str) -> dict[str, Any]:
        view = _config.registry_vc_view
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(
                text(f'SELECT * FROM {view} WHERE phone = :phone'),  # noqa: S608
                {"phone": phone},
            )
            rows = result.mappings().all()

        if not rows:
            raise RegistryLookupError(
                "NO_ELIGIBLE_RECORD",
                f"No active registrant found for phone {phone}",
            )
        if len(rows) > 1:
            _logger.warning(
                "Multiple rows for phone %s; using the first (enforce 1:1)", phone
            )

        row: dict[str, Any] = dict(rows[0])
        # Drop the lookup key from the claim set; keep only VC columns.
        claims = {
            key: ("" if value is None else value)
            for key, value in row.items()
            if key != "phone"
        }
        _logger.debug("Resolved claims for phone %s: %s", phone, list(claims.keys()))
        return claims

    @staticmethod
    def normalize_optional(value: Optional[Any]) -> Any:
        return "" if value is None else value
