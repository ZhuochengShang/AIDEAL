#!/bin/sh
# Three reviewed conditions, one worker, fresh R0; no automatic expansion.
set -eu
OP=/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/operator/ablation/2026-11-18/repair-protocol
RELEASE=/home/zshan011/apps/aideal/releases/2026-11-18-compact-ablation-authoring-82c60d34f332
nohup env AIDEAL_GOOGLE_REQUEST_TIMEOUT_S=300 AIDEAL_GOOGLE_MAX_RETRIES=2 AIDEAL_GOOGLE_MIN_INTERVAL_S=1.0 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1 KERAS_BACKEND=torch CUDA_VISIBLE_DEVICES= /home/zshan011/apps/aideal/venv/bin/python "$RELEASE/scripts/run_cluster_experiment.py" --plan "$OP/FULL_MIR_QUEUE.json" --key-file /home/zshan011/gemini-apikey-aideal.txt --workers 1 > "$OP/full-mir-console.log" 2>&1 < /dev/null &
printf '%s\n' "$!"
