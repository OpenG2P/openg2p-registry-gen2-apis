from typing import Any, Dict

from openg2p_registry_core.errors import G2PRegistryException

from ..schemas import DciSearchCriteria, DciSearchStatusReasonCode


class DciQueryHelper:
    SUPPORTED_QUERY_TYPES = {"expression", "idtype-value"}

    @classmethod
    def get_search_text(cls, search_criteria: DciSearchCriteria) -> str:
        query_type = search_criteria.query_type
        if query_type not in cls.SUPPORTED_QUERY_TYPES:
            cls._raise_invalid_request(
                f"Unsupported query_type '{query_type}'. Supported query types are: expression, idtype-value."
            )

        query_value = search_criteria.query.value
        if query_type == "expression":
            return cls._get_expression_search_text(query_value)
        return cls._get_idtype_value_search_text(query_value)

    @classmethod
    def _get_expression_search_text(cls, query_value: Dict[str, Any]) -> str:
        search_text = (
            query_value.get("expression", {})
            .get("query", {})
            .get("search_text", {})
            .get("$eq")
        )
        return cls._validate_search_text(search_text, "query.value.expression.query.search_text.$eq")

    @classmethod
    def _get_idtype_value_search_text(cls, query_value: Dict[str, Any]) -> str:
        id_type = query_value.get("id_type")
        if not isinstance(id_type, str) or not id_type.strip():
            cls._raise_invalid_request("query.value.id_type is required for idtype-value queries.")

        return cls._validate_search_text(query_value.get("id_value"), "query.value.id_value")

    @classmethod
    def _validate_search_text(cls, value: Any, field_path: str) -> str:
        if not isinstance(value, str) or not value.strip():
            cls._raise_invalid_request(f"{field_path} must be a non-empty string.")
        return value.strip()

    @staticmethod
    def _raise_invalid_request(message: str):
        raise G2PRegistryException(
            code=DciSearchStatusReasonCode.SEARCH_CRITERIA_INVALID.value,
            message=message,
        )
