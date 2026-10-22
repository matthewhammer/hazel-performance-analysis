#!/bin/sh
# ^ticket(535): the library's floor at memo depths 1, 2 and 3, beside before and #2681 (floor2681.mjs plain, three
# interleaved rounds, one node process at a time, pinned and niced; counts first).
#   base, a (#2681), d (depth 1), d2, d3: GitHub's Deploy builds in ~/.cache/hazel-r25/libs/<key>/hazel-lib.js
set -e
LIBS=${LIBS:-$HOME/.cache/hazel-r25/libs}
D="$(cd "$(dirname "$0")" && pwd)"
RUN="taskset -c 0-1 nice -n 10 node --stack-size=8000"
cd "$D/../data/floor"
for b in d2 d3; do $RUN "$D/floor2681.mjs" "$LIBS/$b/hazel-lib.js" count 16,24 "$b"; done
for round in 1 2 3; do for b in base a d d2 d3; do echo "== floor $b round $round"; $RUN "$D/floor2681.mjs" "$LIBS/$b/hazel-lib.js" plain 16,24 "depths_${b}_$round"; done; done
