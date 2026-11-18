#!/bin/sh
# Run only after the parent operator has published and released the prepared pilot.
set -eu
OP=/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/operator/ablation/2026-11-18/repair-protocol
nohup /home/zshan011/apps/aideal/venv/bin/python "$OP/start_repair_pilot.py" > "$OP/pilot-console.log" 2>&1 < /dev/null &
printf '%s\n' "$!"
