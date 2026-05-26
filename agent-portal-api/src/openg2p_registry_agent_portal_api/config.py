from openg2p_registry_extensions.config import Settings as ExtSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(ExtSettings):
    model_config = SettingsConfigDict(
        env_prefix="registry_agent_portal_api_", env_file=".env", extra="allow"
    )

    openapi_title: str = "OpenG2P Registry Agent Portal API"
    openapi_description: str = """
        FastAPI Service for the OpenG2P Registry Agent Portal.

        Phase-1 Verifiable Credential issuance: an agent looks up a registrant
        in the Registry and pushes their claims into MOSIP Inji Certify
        (pre-authorized-code flow) to obtain a signed credential.
        ***********************************
        """
    openapi_version: str = __version__

    # Registry Database (read by the beneficiary_vc_view lookup)
    db_username: str = "postgres"
    db_password: str = "password"
    db_hostname: str = "localhost"
    db_port: int = 5432
    db_dbname: str = "registrydb"

    # Registry view that exposes the VC claims, keyed by phone number.
    registry_vc_view: str = "beneficiary_vc_view"

    # Inji Certify (issuer) settings
    certify_base_url: str = "http://localhost:8090/v1/certify"
    # The audience the proof JWT must carry == Certify's issuer / domain url.
    certify_audience: str = "http://localhost:8090"
    certify_credential_config_id: str = "OpenG2PBeneficiaryCredential"
    # Transaction code used by the pre-authorized-code grant (Phase-1 demo).
    certify_tx_code: str = "12345"
    certify_offer_expires_in: int = 600
    certify_credential_format: str = "ldp_vc"
    certify_credential_context: list[str] = [
        "https://www.w3.org/2018/credentials/v1"
    ]
    certify_credential_types: list[str] = [
        "VerifiableCredential",
        "OpenG2PBeneficiaryCredential",
    ]
    certify_http_timeout: int = 60

    # Paper-credential PDF output
    pdf_output_dir: str = "./out"
    pdf_issuer_name: str = "OpenG2P Registry"
    pdf_title: str = "Beneficiary Verifiable Credential"
