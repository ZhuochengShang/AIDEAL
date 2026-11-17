#!/bin/bash
set -u
cd /home/zshan011/apps/aideal/releases/2026-11-17-canonical-api-a6e8bb84fe32
export AIDEAL_GOOGLE_REQUEST_TIMEOUT_S=300
export AIDEAL_GOOGLE_MAX_RETRIES=2
export AIDEAL_GOOGLE_MIN_INTERVAL_S=1.0
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMBA_NUM_THREADS=1
export KERAS_BACKEND=torch
export CUDA_VISIBLE_DEVICES=''
export AIDEAL_ENV_FINGERPRINT=6efd31cfc003ee5e506f85a094b7ceee92c428ed4fdd87139b045d5ff133f403
/home/zshan011/apps/aideal/venv/bin/python -c 'import json,hashlib;from pathlib import Path;r=Path('"'"'/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical'"'"');d=json.loads((r/'"'"'PRELAUNCH_CHECKS.json'"'"').read_text());a=json.loads((r/'"'"'USER_REVIEW_APPROVAL.json'"'"').read_text());assert d['"'"'status'"'"']=='"'"'ready'"'"';assert d['"'"'release'"'"']=='"'"'/home/zshan011/apps/aideal/releases/2026-11-17-canonical-api-a6e8bb84fe32'"'"';assert a['"'"'approved'"'"'] is True;assert a['"'"'plan_sha256'"'"']==hashlib.sha256((r/'"'"'plan.json'"'"').read_bytes()).hexdigest()' || exit 2
/home/zshan011/apps/aideal/venv/bin/python -u /home/zshan011/apps/aideal/releases/2026-11-17-canonical-api-a6e8bb84fe32/scripts/run_cluster_experiment.py --plan /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/plan.json --key-file /home/zshan011/gemini-apikey-aideal.txt --workers 2 > /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/supervisor_console.log 2>&1 &
worker_pid=$!
echo "$worker_pid" > /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/supervisor.pid
wait "$worker_pid"
queue_status=$?
/home/zshan011/apps/aideal/venv/bin/python -c 'import hashlib;from pathlib import Path;p=Path('"'"'/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/scripts/finalize_all_readmes.py'"'"');assert hashlib.sha256(p.read_bytes()).hexdigest()=='"'"'35e2c94bf409c260a85a3d257f921a27f70b8393272180a91163e4654cf1e221'"'"'' || exit 2
/home/zshan011/apps/aideal/venv/bin/python /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/scripts/finalize_all_readmes.py /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical > /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/installation_console.log 2>&1
install_status=$?
/home/zshan011/apps/aideal/venv/bin/python /home/zshan011/apps/aideal/releases/2026-11-17-canonical-api-a6e8bb84fe32/scripts/report_experiment_costs.py --r0-root /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/runs/original --readme-root /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/authoring --plan /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/plan.json --output-json /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/COSTS.json --output-md /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/COSTS.md > /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/cost_refresh_console.log 2>&1
if [ "$queue_status" -ne 0 ]; then exit "$queue_status"; fi
exit "$install_status"
