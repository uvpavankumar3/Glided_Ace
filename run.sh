#!/usr/bin/env bash
# Rebuilds build/index.html from the challenge data.
# Usage: ./run.sh /path/to/dashboard-royale   (the cloned challenge repo)
set -euo pipefail
DATA="${1:?path to the dashboard-royale repo}"
mkdir -p build
python3 pipeline/01_machine_day.py "$DATA" > build/01_log.txt
python3 pipeline/02_model.py "$DATA"       > build/02_log.txt
python3 pipeline/03_build_data.py "$DATA" build/data.json
python3 pipeline/04_classify.py build/data.json > build/04_log.txt
python3 pipeline/05_plan.py build/data.json > build/05_log.txt
python3 pipeline/06_assemble.py pipeline/template.html build/data.json build/index.html
python3 pipeline/07_docs.py build/data.json APPENDIX.md
echo "Done: build/index.html and APPENDIX.md"
