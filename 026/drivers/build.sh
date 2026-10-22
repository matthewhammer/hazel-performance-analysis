#!/bin/sh
# Regenerate ^report(26) and run the series tools on it, in order.
set -e
cd "$(dirname "$0")/../.."
python3 026/drivers/gen026.py
python3 tools/report_refs.py 026/index.html
python3 tools/link_prs.py 026/index.html
python3 tools/add_theme.py 026/index.html
python3 tools/report_data.py 026
python3 tools/add_anchors.py 026/index.html
