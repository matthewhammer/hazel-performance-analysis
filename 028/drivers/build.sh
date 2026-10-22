#!/bin/sh
# Regenerate ^report(28) and run the series tools on it, in order.
set -e
cd "$(dirname "$0")/../.."
python3 028/drivers/gen028.py
python3 tools/report_refs.py 028/index.html
python3 tools/link_prs.py 028/index.html
python3 tools/add_theme.py 028/index.html
python3 tools/report_data.py 028
python3 tools/add_anchors.py 028/index.html
