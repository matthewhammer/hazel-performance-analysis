#!/bin/sh
# Regenerate ^report(31) and run the series tools on it, in order.
set -e
cd "$(dirname "$0")/../.."
python3 031/drivers/gen031.py
python3 tools/report_refs.py 031/index.html
python3 tools/link_prs.py 031/index.html
python3 tools/add_theme.py 031/index.html
python3 tools/add_listen.py 031/index.html
python3 tools/report_data.py 031
python3 tools/add_anchors.py 031/index.html
