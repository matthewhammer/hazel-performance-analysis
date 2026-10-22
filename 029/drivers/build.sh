#!/bin/sh
# Regenerate ^report(29) and run the series tools on it, in order.
set -e
cd "$(dirname "$0")/../.."
python3 029/drivers/gen029.py
python3 tools/report_refs.py 029/index.html
python3 tools/link_prs.py 029/index.html
python3 tools/add_steps.py 029/index.html
python3 tools/add_theme.py 029/index.html
python3 tools/report_data.py 029
python3 tools/add_anchors.py 029/index.html
