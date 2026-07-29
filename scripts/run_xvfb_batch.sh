#!/usr/bin/env bash
# Batch entry: Xvfb + dual workers (register_workers=2 in config.json)
set -euo pipefail
cd "$(dirname "$0")"
COUNT="${1:-10}"
# update count only
python3 - << PY
import json
from pathlib import Path
p=Path("config.json")
c=json.loads(p.read_text())
c["register_count"]=int("${COUNT}")
c["register_workers"]=2
p.write_text(json.dumps(c, ensure_ascii=False, indent=2)+"\n")
print("batch count", c["register_count"], "workers", c["register_workers"])
PY
exec ./run_xvfb_smoke.sh "$COUNT"
