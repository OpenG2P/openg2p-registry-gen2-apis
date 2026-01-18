import logging
from typing import List
from fastapi import UploadFile, File, Form

from openg2p_fastapi_common.controller import BaseController

from openg2p_registry_core.controller_services import G2PDocumentControllerService
from openg2p_registry_core.schemas import (
    UploadDocumentsResponse, UploadDocumentsResponseData,
    UploadRecordImageResponse, UploadRecordImageData,
    GetDocumentLabelsForSectionRequest,
    GetSectionDocumentsRequest,
    GetSectionDocumentsForChangeRequestRequest,
    SectionDocumentsResponse, SectionDocumentsData,
    ChangeRequestDocumentsResponse, ChangeRequestDocumentsData
)

from ..helpers import RequestResponseHelper
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class G2PDocumentController(BaseController):
    """
    Controller for handling document-related operations.
    Provides endpoints for uploading and managing documents for change requests.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["G2P Documents"]
        self.g2p_document_controller_service = G2PDocumentControllerService.get_component()
        self.helper = RequestResponseHelper.get_component()
        self.router.prefix = "/documents"

        self.router.add_api_route(
            "/upload_documents",
            self.upload_documents,
            responses={200: {"model": UploadDocumentsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/upload",
            self.upload_documents,
            responses={200: {"model": UploadDocumentsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_section_documents",
            self.get_section_documents,
            responses={200: {"model": SectionDocumentsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_change_request_documents",
            self.get_change_request_documents,
            responses={200: {"model": ChangeRequestDocumentsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/upload_record_image",
            self.upload_record_image,
            responses={200: {"model": UploadRecordImageResponse}},
            methods=["POST"],
        )

    async def upload_documents(
        self,
        document_label: str = Form(..., description="Document label for the files"),
        documents: List[UploadFile] = File(..., description="List of documents to upload")
    ) -> UploadDocumentsResponse:
        """
        Upload multiple documents to MinIO storage with the specified document label.
        """
        try:
            upload_response_data: UploadDocumentsResponseData = await self.g2p_document_controller_service.upload_documents(
                document_label=document_label,
                documents=documents,
            )
            upload_response: UploadDocumentsResponse = self.helper.construct_upload_documents_success_response(
                upload_response_data=upload_response_data
            )
            return upload_response
        except Exception as error_exception:
            _logger.error(f"Error in upload_documents: {str(error_exception)}")
            error_response: UploadDocumentsResponse = self.helper.construct_upload_documents_error_response(error_exception)
            return error_response

    async def upload_record_image(
        self,
        document: UploadFile = File(..., description="The image file to upload")
    ) -> UploadRecordImageResponse:
        """
        Upload a record image to MinIO storage.

        The image is uploaded with a hardcoded RECORD_IMAGE label.
        Returns the document_store_id that can be used when creating a change request.
        """
        try:
            upload_response_data: UploadDocumentsResponseData = await self.g2p_document_controller_service.upload_documents(
                document_label="RECORD_IMAGE",
                documents=[document],
            )
            upload_response: UploadRecordImageResponse = self.helper.construct_upload_record_image_success_response(
                upload_record_image_data=upload_response_data[0]
            )
            return upload_response
        except Exception as error_exception:
            _logger.error(f"Error in upload_record_image: {str(error_exception)}")
            error_response: UploadRecordImageResponse = self.helper.construct_upload_record_image_error_response(error_exception)
            return error_response

    async def get_section_documents(
        self,
        request: GetSectionDocumentsRequest
    ) -> SectionDocumentsResponse:
        """
        Get documents for a section record.

        Returns the list of documents (label, document_store_id) for the specified record and section.
        """
        try:
            section_documents_data: SectionDocumentsData = await self.g2p_document_controller_service.get_section_documents(request)
            response: SectionDocumentsResponse = self.helper.construct_section_documents_success_response(
                section_documents_data=section_documents_data,
                g2p_request=request
            )
            return response
        except Exception as error_exception:
            _logger.error(f"Error in get_section_documents: {str(error_exception)}")
            error_response: SectionDocumentsResponse = self.helper.construct_section_documents_error_response(error_exception)
            return error_response

    async def get_change_request_documents(
        self,
        request: GetSectionDocumentsForChangeRequestRequest
    ) -> ChangeRequestDocumentsResponse:
        """
        Get documents for a change request.

        Returns the list of documents (label, document_store_id) attached to the specified change request.
        """
        try:
            change_request_documents_data: ChangeRequestDocumentsData = await self.g2p_document_controller_service.get_change_request_documents(request)
            response: ChangeRequestDocumentsResponse = self.helper.construct_change_request_documents_success_response(
                change_request_documents_data=change_request_documents_data,
                g2p_request=request
            )
            return response
        except Exception as error_exception:
            _logger.error(f"Error in get_section_documents_for_change_request: {str(error_exception)}")
            error_response: ChangeRequestDocumentsResponse = self.helper.construct_change_request_documents_error_response(error_exception)
            return error_response
