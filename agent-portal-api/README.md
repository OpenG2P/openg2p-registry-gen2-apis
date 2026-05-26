# OpenG2P Registry Agent Portal API

FastAPI service for the **agent-assisted Phase-1 Verifiable Credential issuance**
flow. An agent (having verified the citizen out-of-band) looks up the registrant
in the Registry and pushes their claims into **MOSIP Inji Certify** to obtain a
signed credential — no wallet and no citizen device required.

> Design documentation lives in the `openg2p-documentation` repo under
> `platform/platform-services/vc-issuance/`.

## How it works

1. Agent calls `POST /agent_portal/issue_vc` with the registrant's `phone`.
2. The service resolves the claims from the Registry's read-only
   `beneficiary_vc_view` (phone-keyed, active-only).
3. It pushes those claims into Certify via the OpenID4VCI **pre-authorized-code**
   flow (consumed by Certify's stock `PreAuthDataProviderPlugin`):
   `pre-authorized-data` → `credential-offer-data` → `oauth/token` →
   `issuance/credential` (with a generated proof-of-possession JWT).
4. The signed credential is returned to the agent (to be rendered as a printed
   signed QR/PDF — the Phase-1 paper credential).

## Configuration

Environment variables use the prefix `registry_agent_portal_api_`. Key settings
(see `config.py`):

| Setting | Default | Purpose |
|---|---|---|
| `db_hostname` / `db_port` / `db_dbname` / `db_username` / `db_password` | localhost / 5432 / registrydb / postgres | Registry DB (read the view) |
| `registry_vc_view` | `beneficiary_vc_view` | Phone-keyed claims view |
| `certify_base_url` | `http://localhost:8090/v1/certify` | Inji Certify base URL |
| `certify_audience` | `http://localhost:8090` | Proof JWT audience (== Certify issuer) |
| `certify_credential_config_id` | `FarmerCredential` | Certify credential config |
| `certify_tx_code` | `12345` | Pre-authorized-code tx_code |

## Run (dev)

```bash
pip install -e .
python -m openg2p_registry_agent_portal_api.main
```

## Example request

```bash
curl -X POST http://localhost:8000/agent_portal/issue_vc \
  -H 'Content-Type: application/json' \
  -d '{
    "request_header": {
      "sender_app_mnemonic": "agent-portal-ui",
      "sender_app_url": "http://localhost",
      "request_id": "req-1",
      "request_timestamp": "2026-05-26T00:00:00Z"
    },
    "request_body": { "request_payload": { "phone": "+919812345678" } }
  }'
```
