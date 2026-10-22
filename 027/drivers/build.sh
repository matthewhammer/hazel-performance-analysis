#!/bin/sh
# Regenerate ^report(27) and run the series tools on it, in order.
set -e
cd "$(dirname "$0")/../.."
python3 027/drivers/gen027.py
python3 tools/report_refs.py 027/index.html
python3 tools/link_prs.py 027/index.html
python3 tools/add_steps.py 027/index.html
python3 tools/add_theme.py 027/index.html
python3 tools/report_data.py 027
python3 tools/add_anchors.py 027/index.html
