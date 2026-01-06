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
    DocumentLabelsForSectionResponse, DocumentLabelsForSectionData,
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
            "/upload",
            self.upload_documents,
            responses={200: {"model": UploadDocumentsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_document_labels_for_section",
            self.get_document_labels_for_section,
            responses={200: {"model": DocumentLabelsForSectionResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_section_documents",
            self.get_section_documents,
            responses={200: {"model": SectionDocumentsResponse}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/get_section_documents_for_change_request",
            self.get_section_documents_for_change_request,
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
        section_id: str = Form(..., description="Section ID to validate document labels against"),
        document_label_ids: List[str] = Form(..., description="List of document label IDs (one per file)"),
        files: List[UploadFile] = File(..., description="List of files to upload")
    ) -> UploadDocumentsResponse:
        """
        Upload documents for a change request to MinIO storage.

        Files are uploaded and stored in MinIO. Returns document_store_ids that can be
        used when creating a change request with documents.

        The number of document_label_ids must match the number of files.
        """
        try:
            if len(document_label_ids) != len(files):
                raise ValueError(f"Number of document_label_ids ({len(document_label_ids)}) must match number of files ({len(files)})")

            # Pair each file with its document_label_id
            files_with_labels = list(zip(document_label_ids, files))

            upload_response_data: UploadDocumentsResponseData = await self.g2p_document_controller_service.upload_documents(
                section_id=section_id,
                files=files_with_labels
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
        section_id: str = Form(..., description="Section ID for organizing storage path"),
        file: UploadFile = File(..., description="The image file to upload")
    ) -> UploadRecordImageResponse:
        """
        Upload a record image to MinIO storage.

        The image is uploaded with a hardcoded RECORD_IMAGE label.
        Returns the document_store_id that can be used when creating a change request.
        """
        try:
            upload_response_data: UploadRecordImageData = await self.g2p_document_controller_service.upload_record_image(
                section_id=section_id,
                file=file
            )
            upload_response: UploadRecordImageResponse = self.helper.construct_upload_record_image_success_response(
                upload_record_image_data=upload_response_data
            )
            return upload_response
        except Exception as error_exception:
            _logger.error(f"Error in upload_record_image: {str(error_exception)}")
            error_response: UploadRecordImageResponse = self.helper.construct_upload_record_image_error_response(error_exception)
            return error_response

    async def get_document_labels_for_section(
        self,
        request: GetDocumentLabelsForSectionRequest
    ) -> DocumentLabelsForSectionResponse:
        """
        Get document labels for a section.

        Returns the list of document labels configured for the specified section.
        """
        try:
            document_labels_data: DocumentLabelsForSectionData = await self.g2p_document_controller_service.get_document_labels_for_section(request)
            response: DocumentLabelsForSectionResponse = self.helper.construct_document_labels_for_section_success_response(
                document_labels_data=document_labels_data,
                g2p_request=request
            )
            return response
        except Exception as error_exception:
            _logger.error(f"Error in get_document_labels_for_section: {str(error_exception)}")
            error_response: DocumentLabelsForSectionResponse = self.helper.construct_document_labels_for_section_error_response(error_exception)
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

    async def get_section_documents_for_change_request(
        self,
        request: GetSectionDocumentsForChangeRequestRequest
    ) -> ChangeRequestDocumentsResponse:
        """
        Get documents for a change request.

        Returns the list of documents (label, document_store_id) attached to the specified change request.
        """
        try:
            change_request_documents_data: ChangeRequestDocumentsData = await self.g2p_document_controller_service.get_section_documents_for_change_request(request)
            response: ChangeRequestDocumentsResponse = self.helper.construct_change_request_documents_success_response(
                change_request_documents_data=change_request_documents_data,
                g2p_request=request
            )
            return response
        except Exception as error_exception:
            _logger.error(f"Error in get_section_documents_for_change_request: {str(error_exception)}")
            error_response: ChangeRequestDocumentsResponse = self.helper.construct_change_request_documents_error_response(error_exception)
            return error_response
