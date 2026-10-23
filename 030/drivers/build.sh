#!/bin/sh
# Regenerate ^report(30) and run the series tools on it, in order.
set -e
cd "$(dirname "$0")/../.."
python3 030/drivers/gen030.py
python3 tools/report_refs.py 030/index.html
python3 tools/link_prs.py 030/index.html
python3 tools/add_steps.py 030/index.html
python3 tools/add_theme.py 030/index.html
python3 tools/add_listen.py 030/index.html
python3 tools/report_data.py 030
python3 tools/add_anchors.py 030/index.html
