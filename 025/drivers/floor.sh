#!/bin/sh
# ^ticket(535): #2681's floor. Three builds of hazel-lib.js (GitHub's Deploy builds), one node process at a time,
# pinned and niced (this laptop crashes under load):
#   base   js-library-embed at 0d66c36618 (before #2681)
#   a      trial/r25-2681: + #2681 (with #2661)
#   d      trial/r25-2681-depth: #2681 asked and told only at depth 0 and 1 (Ascriptions.memo_depth)
# 1. floor2681.mjs count on a and d: the memo's lookups and writes per call
# 2. floor2681.mjs plain, three interleaved rounds: idA, noann, shipped at 16x16 and 24x24, with GC time per call
# 3. r25.mjs, two interleaved rounds, all sizes: comparable with the report's before-and-after runs
set -e
LIBS=${LIBS:-$HOME/.cache/hazel-r25/libs}
D="$(cd "$(dirname "$0")" && pwd)"
RUN="taskset -c 0-1 nice -n 10 node --stack-size=8000"
mkdir -p "$D/../data/floor" "$D/../data/prs"
cd "$D/../data/floor"
for b in a d; do $RUN "$D/floor2681.mjs" "$LIBS/$b/hazel-lib.js" count 16,24 "$b"; done
for round in 1 2 3; do for b in base a d; do echo "== floor $b round $round"; $RUN "$D/floor2681.mjs" "$LIBS/$b/hazel-lib.js" plain 16,24 "${b}_$round"; done; done
cd "$D/../data/prs"
for round in 1 2; do echo "== r25 d round $round"; $RUN "$D/r25.mjs" "$LIBS/d/hazel-lib.js" "3,4,6,8,12,16,24" "d_$round"; done
