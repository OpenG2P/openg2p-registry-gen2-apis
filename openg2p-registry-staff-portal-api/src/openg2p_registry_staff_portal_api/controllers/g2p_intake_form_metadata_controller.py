import logging

from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PIntakeFormControllerService
from openg2p_registry_core.schemas import (
    G2PResponse
)
from openg2p_fastapi_common.schemas import G2PResponse

from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)

class G2PIntakeFormMetadataController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["/intake-form-metadata"]
        self.g2p_intake_form_controller_service = G2PIntakeFormControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/intake-form-metadata"

