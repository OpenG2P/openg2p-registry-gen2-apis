#!/usr/bin/env python3
"""
Generate OpenAPI JSON for each portal API and write to docs/openapi/.
If one API fails (import or openapi()), it is skipped and the rest are generated.
Usage: python scripts/generate_openapi.py [output_dir]
Default output_dir: docs/openapi
"""
import json
import sys
import traceback
from pathlib import Path


def generate_openapi(module_name: str, app_attr: str, out_path: Path) -> None:
    mod = __import__(module_name, fromlist=[app_attr])
    app = getattr(mod, app_attr)
    schema = app.openapi()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(schema, f, indent=2)


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/openapi")
    apis = [
        ("openg2p_registry_bene_portal_api.main", "app", "openapi-bene-portal.json"),
        ("openg2p_registry_staff_portal_api.main", "app", "openapi-staff-portal.json"),
        ("openg2p_registry_partner_api.main", "app", "openapi-partner.json"),
    ]
    for module_name, app_attr, filename in apis:
        out_path = out_dir / filename
        try:
            generate_openapi(module_name, app_attr, out_path)
            print(f"Wrote {out_path}")
        except Exception as e:
            print(f"Skipped {filename}: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    main()
