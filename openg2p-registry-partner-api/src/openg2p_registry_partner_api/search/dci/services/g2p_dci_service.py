import logging
import uuid
import io
from datetime import datetime
from fastapi import UploadFile
from typing import Optional, List, Dict, Any, Tuple
import httpx

from openg2p_registry_core.schemas import DeepSearchResultData
from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.context import dbengine

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select

from openg2p_registry_core.services import G2PRegisterService
from openg2p_registry_core.helpers import TemplateHelper, MinioClient
from openg2p_registry_core.models import G2PRegisterDefinition, DataModel, OutgoingTemplate

from ..schemas import (
    DciSearchResponseItem,
    DciSearchCriteria,
    DciRequestHeader,
    DciSearchRequest,
    DciSearchResultData,
    DciPagination,
    DciSearchResultPagination,
    DciStatusCode,
)
from ....config import Settings

_logger = logging.getLogger("g2p-dci-service")
_config = Settings.get_config()
_engine = dbengine.get()

class G2PDciService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_service = G2PRegisterService.get_component()

    async def search(self, signature: str, header: DciRequestHeader, message: DciSearchRequest) -> List[DciSearchResponseItem]:
        
        dci_search_response_items: List[DciSearchResponseItem] = []
        for search_request_item in message.search_request:
            search_criteria: DciSearchCriteria = search_request_item.search_criteria

            register_id: str = await self._get_register_id(search_criteria.reg_type)
            data_model_id: str = await self._get_data_model_id()
            template_file_id: str = await self._get_template_file_id(register_id, data_model_id)

            search_text, current_page, page_size, sort_by = self._get_registry_search_parameters(search_criteria)
            
            deep_search_result_data, total_count = await self.register_service.deep_search_in_a_register(
                register_id=register_id,
                search_text=search_text,
                current_page=current_page,
                page_size=page_size,
                sort_by=sort_by,
            )
            dci_deep_search_result_data = DciSearchResultData(
                reg_type = search_criteria.reg_type,
                reg_record_type = search_criteria.reg_record_type,
                reg_records = [
                    self._render_reg_record_with_template(deep_search_result_datum, template_file_id) 
                    for deep_search_result_datum in deep_search_result_data
                ]
            )
            pagination = DciSearchResultPagination(
                page_number = current_page,
                page_size = page_size,
                total_count = total_count
            )
            dci_search_response_item = DciSearchResponseItem(
                reference_id = search_request_item.reference_id,
                timestamp = datetime.now().isoformat(),
                status = DciStatusCode.SUCCESS.value,
                data = dci_deep_search_result_data,
                pagination = pagination,
                locale="en"
            )
            dci_search_response_items.append(dci_search_response_item)
            
            _logger.info(f"Search completed for reference_id: {search_request_item.reference_id}, found {total_count} items")
        
        _logger.info(f"Search completed for transaction_id: {message.transaction_id}, found {len(dci_search_response_items)} items")
        return dci_search_response_items
        

    def _render_reg_record_with_template(
        self,
        deep_search_result_data: DeepSearchResultData,
        template_file_id: str
    ) -> Dict[str, Any]:
        """
        Render a template using the DeepSearchResultData object (may include Farmer extension fields).
        """
        template_helper = TemplateHelper.get_component()
        minio_client = MinioClient.get_component()

        # Always use _deep_search_result_data_to_dict for extracting data
        search_result_dict: Dict[str, Any] = self._deep_search_result_data_to_dict(deep_search_result_data)

        reg_record: Dict[str, Any] = template_helper.render_with_template(
            minio_client=minio_client,
            template_file_id=template_file_id,
            data=search_result_dict,
            expand_data=False
        )

        return reg_record

    def _deep_search_result_data_to_dict(
        self,
        deep_search_result_data: DeepSearchResultData
    ) -> Dict[str, Any]:
        """
        Convert DeepSearchResultData (including all extension/extra fields) into a dict for template rendering.
        Uses pydantic's model_dump()/dict() to ensure all fields (Farmer, etc) are dumped.
        """
        if hasattr(deep_search_result_data, "model_dump"):
            data_dict = deep_search_result_data.model_dump(exclude_unset=False, by_alias=False)
        else:
            data_dict = deep_search_result_data.dict(exclude_unset=False, by_alias=False)

        return data_dict

    
    def _get_registry_search_parameters(
        self,
        search_criteria: DciSearchCriteria
    ) -> Tuple[str, int, int, Optional[str]]:
        # Search text
        search_text: str = search_criteria.query.value
        
        # Pagination
        current_page: int = 1
        page_size: int = 10
        if search_criteria.pagination:
            current_page = search_criteria.pagination.page_number
            page_size = search_criteria.pagination.page_size

        # Sorting
        sort_by = None
        if search_criteria.sort and len(search_criteria.sort) > 0:
            first_sort = search_criteria.sort[0]
            if first_sort.sort_order == "desc":
                sort_by = f"-{first_sort.attribute_name}"
            else:
                sort_by = first_sort.attribute_name

        return search_text, current_page, page_size, sort_by

    async def _get_register_id(self, register_mnemonic: str) -> str:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            register_id: str = (
                await session.execute(
                    select(G2PRegisterDefinition.register_id)
                    .where(G2PRegisterDefinition.register_mnemonic == register_mnemonic)
                )
            ).scalar_one_or_none()
            return register_id
    
    async def _get_data_model_id(self) -> str:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            data_model_id: str = (
                await session.execute(
                    select(DataModel.data_model_id)
                    .where(DataModel.data_model_mnemonic == "g2p_register")
                )
            ).scalar_one_or_none()
            return data_model_id

    async def _get_template_file_id(self, register_id: str, data_model_id: str) -> str:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            template_file_id: str = (
                await session.execute(
                    select(OutgoingTemplate.template_file_id)
                    .where(OutgoingTemplate.register_id == register_id)
                    .where(OutgoingTemplate.data_model_id == data_model_id)
                )
            ).scalar_one_or_none()
            return template_file_id
        