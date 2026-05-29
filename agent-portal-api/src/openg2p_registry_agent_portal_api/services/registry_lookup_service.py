import logging
from typing import Any

from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.service import BaseService
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..config import Settings, VcDefinition

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class RegistryLookupError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class RegistryLookupService(BaseService):
    """Resolves a registrant's VC claims from a Registry read-only view.

    Each VC definition names its own view + claim columns (config-driven), so
    different VC types read different views/fields. Views are phone-keyed and
    active-only; the matching row's columns become the credential claims.
    """

    async def get_claims_by_phone(
        self, phone: str, vc: VcDefinition
    ) -> tuple[dict[str, Any], Any]:
        """Return (claims, photo_key) for the registrant.

        claims = the configured VC claim columns; photo_key = the MINIO object
        key from vc.photo_key_column (None if not configured).
        """
        # Identifiers are config (not user input): view/column come from the
        # VC definition, phone is a bound parameter.
        query = f'SELECT * FROM {vc.view} WHERE "{vc.phone_column}" = :phone'  # noqa: S608
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            result = await session.execute(text(query), {"phone": phone})
            rows = result.mappings().all()

        if not rows:
            raise RegistryLookupError(
                "NO_ELIGIBLE_RECORD",
                f"No active registrant found for phone {phone} in {vc.view}",
            )
        if len(rows) > 1:
            _logger.warning(
                "Multiple rows for phone %s in %s; using the first (enforce 1:1)",
                phone,
                vc.view,
            )

        row: dict[str, Any] = dict(rows[0])
        skip = {vc.phone_column, vc.photo_key_column}
        wanted = vc.claim_columns or [k for k in row if k not in skip]
        claims = {
            key: ("" if row.get(key) is None else row.get(key)) for key in wanted
        }
        photo_key = row.get(vc.photo_key_column) if vc.photo_key_column else None
        _logger.debug(
            "Resolved claims for phone %s (%s): %s; photo=%s",
            phone, vc.config_id, list(claims.keys()), bool(photo_key),
        )
        return claims, photo_key
