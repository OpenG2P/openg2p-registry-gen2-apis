from typing import List, Optional, Literal, Dict, Any, Union
from pydantic import BaseModel, Field


# ----------------------------
# Query models
# ----------------------------

class DciQueryValue(BaseModel):
    expression: str


class DciQuery(BaseModel):
    type: str
    value: str


# ----------------------------
# Sort & Pagination
# ----------------------------

class DciSortItem(BaseModel):
    attribute_name: str
    sort_order: Literal["asc", "desc"]


class DciPagination(BaseModel):
    page_size: int = Field(..., ge=1)
    page_number: int = Field(..., ge=1)


# ----------------------------
# Purpose (PERMISSIVE BY DESIGN)
# Accepts schema-like objects:
# { "type": "string" }, etc.
# ----------------------------

class DciPurpose(BaseModel):
    text: Optional[Any] = None
    code: Optional[Any] = None
    ref_uri: Optional[Any] = None

    class Config:
        extra = "allow"


# ----------------------------
# Consent / Authorize (JSON-LD friendly)
# Allows:
# ts = string OR { "$ref": ... }
# ----------------------------

class DciConsent(BaseModel):
    context: Optional[str] = Field(None, alias="@context")
    type_: Optional[str] = Field(None, alias="@type")
    ts: Optional[Union[str, Dict[str, Any]]] = None
    purpose: Optional[DciPurpose] = None

    class Config:
        validate_by_name = True
        extra = "allow"


class DciAuthorize(BaseModel):
    context: Optional[str] = Field(None, alias="@context")
    type_: Optional[str] = Field(None, alias="@type")
    ts: Optional[Union[str, Dict[str, Any]]] = None
    purpose: Optional[DciPurpose] = None

    class Config:
        validate_by_name = True
        extra = "allow"


# ----------------------------
# Search Criteria
# NOTE:
# - reg_event_type intentionally NOT required
# - extra fields allowed
# ----------------------------

class DciSearchCriteria(BaseModel):
    version: str = "1.0.0"
    reg_type: str
    reg_record_type: str
    query_type: str
    query: DciQuery
    sort: Optional[List[DciSortItem]] = None
    pagination: Optional[DciPagination] = None
    consent: Optional[DciConsent] = None
    authorize: Optional[DciAuthorize] = None

    class Config:
        extra = "allow"


# ----------------------------
# Search Request Item
# ----------------------------

class DciSearchRequestItem(BaseModel):
    reference_id: str = Field(..., max_length=99)
    timestamp: Optional[str] = None
    search_criteria: DciSearchCriteria
    locale: Optional[str] = "eng"


# ----------------------------
# Message Body
# ----------------------------

class DciSearchRequest(BaseModel):
    transaction_id: str = Field(..., max_length=99)
    search_request: List[DciSearchRequestItem]


# ----------------------------
# Header
# ----------------------------

class DciRequestHeader(BaseModel):
    version: str
    message_id: str
    message_ts: str
    action: str
    sender_id: str
    sender_uri: Optional[str] = None
    receiver_id: str
    total_count: Optional[int] = None
    is_msg_encrypted: bool = False
    meta: Optional[Dict[str, Any]] = None


# ----------------------------
# Envelope
# ----------------------------

class DciSearchRequestEnvelope(BaseModel):
    signature: str
    header: DciRequestHeader
    message: DciSearchRequest

    class Config:
        extra = "allow"
