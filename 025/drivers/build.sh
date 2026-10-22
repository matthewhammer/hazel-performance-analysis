#!/bin/sh
# Regenerate ^report(25) and run the series tools on it, in order.
set -e
cd "$(dirname "$0")/../.."
python3 025/drivers/gen025.py
python3 tools/report_refs.py 025/index.html
python3 tools/link_prs.py 025/index.html
python3 tools/add_steps.py 025/index.html
python3 tools/add_theme.py 025/index.html
python3 tools/report_data.py 025
python3 tools/add_anchors.py 025/index.html
