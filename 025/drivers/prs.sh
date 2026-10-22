#!/bin/sh
# ^report(25), before and after the performance PRs: r25.mjs on three builds of hazel-lib.js,
# GitHub's Deploy builds (hazelgrove/build), in two interleaved rounds, one node process at a time
# (this laptop crashes under load: pinned to two threads and niced).
#   base  js-library-embed at 0d66c36618 (#2719 on #2711 on dev 962a7cb009: 1 of the 14 PRs, #2679)
#   a     trial/r25-2681: base + #2681 (with #2661)
#   b     trial/r25-all-perf: base + all 13 open speed PRs
# Writes data_<build>_<round>.json and compile_<build>_<round>.json into 025/data/prs/.
set -e
LIBS=${LIBS:-$HOME/.cache/hazel-r25/libs}
OUT="$(dirname "$0")/../data/prs"
mkdir -p "$OUT"; cd "$OUT"
for round in 1 2; do
  for b in base a b; do
    echo "== $b round $round"
    taskset -c 0-1 nice -n 10 node --stack-size=8000 ../../drivers/r25.mjs "$LIBS/$b/hazel-lib.js" "${SIZES:-3,4,6,8,12,16,24}" "${b}_$round"
  done
done
