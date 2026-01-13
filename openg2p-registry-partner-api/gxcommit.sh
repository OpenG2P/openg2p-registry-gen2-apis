#!/bin/bash

set -e

git add openg2p-registry-staff-portal-api/src/openg2p_registry_staff_portal_api/app.py
git commit -m "feat: add G2PIngestionDataController"

git add openg2p-registry-staff-portal-api/src/openg2p_registry_staff_portal_api/helpers/request_response_helper.py
git commit -m "feat: add ingestion summary and data payload response construction"

