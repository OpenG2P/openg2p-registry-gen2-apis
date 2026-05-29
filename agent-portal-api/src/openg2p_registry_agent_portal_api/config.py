from openg2p_registry_extensions.config import Settings as ExtSettings
from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict

from . import __version__


class VcDefinition(BaseModel):
    """One issuable VC type — config-driven, so a module can offer several.

    `config_id` is the agent-selected key AND the Certify
    credential_configuration_id pushed to. `view` + `claim_columns` say which
    Registry view/columns feed the claims (phone-keyed). The Registry/NSR Helm
    chart supplies this list; the source views live in the registry extension.
    """

    config_id: str
    credential_types: list[str]
    view: str = "beneficiary_vc_view"
    phone_column: str = "phone"
    # Empty => use every non-phone column from the view as a claim.
    claim_columns: list[str] = []
    # Photo (optional): the view column holding the MINIO object KEY of the
    # registrant's photo. The API fetches it, thumbnails it for the claim-169 QR
    # (pushed as `face_claim`), and places it on the printed card.
    photo_key_column: str = ""
    face_claim: str = "face"
    # Path (dot-notation) within the issued VC's credentialSubject to the signed
    # claim-169 base45 QR string to print. Empty => fall back to a QR of the VC.
    qr_claim_path: str = "claim169.qrCode"
    # SVG design template filename (under svg_template_dir) for the printed card.
    svg_template: str = ""


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

    # VC definitions this deployment can issue (supplied via Helm as JSON in
    # REGISTRY_AGENT_PORTAL_API_VC_DEFINITIONS). Multiple = multiple VC types
    # per registry (e.g. an ID card vs ID + socio-economic). The default is the
    # single beneficiary ID credential.
    vc_definitions: list[VcDefinition] = [
        VcDefinition(
            config_id="OpenG2PBeneficiaryCredential",
            credential_types=["VerifiableCredential", "OpenG2PBeneficiaryCredential"],
            view="beneficiary_vc_view",
            claim_columns=["functionalRecordId", "fullName", "dateOfBirth"],
        )
    ]

    # Inji Certify (issuer) settings
    certify_base_url: str = "http://localhost:8090/v1/certify"
    # The audience the proof JWT must carry == Certify's issuer / domain url.
    certify_audience: str = "http://localhost:8090"
    # Transaction code used by the pre-authorized-code grant (Phase-1 demo).
    certify_tx_code: str = "12345"
    certify_offer_expires_in: int = 600
    certify_credential_format: str = "ldp_vc"
    certify_credential_context: list[str] = [
        "https://www.w3.org/2018/credentials/v1"
    ]
    certify_http_timeout: int = 60

    def get_vc_definition(self, vc_type: str | None) -> VcDefinition:
        """Resolve a VC definition by config_id; default to the first."""
        if not self.vc_definitions:
            raise ValueError("No vc_definitions configured")
        if vc_type:
            for d in self.vc_definitions:
                if d.config_id == vc_type:
                    return d
            raise ValueError(f"Unknown vc_type '{vc_type}'")
        return self.vc_definitions[0]

    # Paper-credential PDF output
    pdf_output_dir: str = "./out"
    pdf_issuer_name: str = "OpenG2P Registry"
    pdf_title: str = "Beneficiary Verifiable Credential"
    # Directory where SVG design templates are mounted (ConfigMap).
    svg_template_dir: str = "./pdf-templates"

    # MINIO (for fetching registrant photos by object key)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "registry"
    minio_secure: bool = True
    # Face thumbnail for the claim-169 QR (tiny — a QR holds ~2.9 KB total).
    photo_thumbnail_max_px: int = 160
    photo_thumbnail_quality: int = 50
