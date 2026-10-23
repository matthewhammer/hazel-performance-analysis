#!/bin/sh
# Regenerate ^report(24) and run the series tools on it, in order.
set -e
cd "$(dirname "$0")/../.."
python3 024/drivers/gen024.py
python3 tools/report_refs.py 024/index.html
python3 tools/link_prs.py 024/index.html
python3 tools/add_steps.py 024/index.html
python3 tools/add_theme.py 024/index.html
python3 tools/add_listen.py 024/index.html
python3 tools/report_data.py 024
