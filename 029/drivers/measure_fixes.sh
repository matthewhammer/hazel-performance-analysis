#!/bin/sh
# ^ticket(547), 548, 551: one trial library at a time, one node process at a time, niced and pinned.
#   measure_fixes.sh closures|handles|asc|stats
L=~/.cache/hazel-r25/libs/$1/hazel-lib.js; D=$(dirname "$0")/../data/fixes; mkdir -p $D; cd $(dirname "$0")
run() { taskset -c 0-1 nice -n 10 timeout 900 node --stack-size=8000 "$@" 2>&1 | grep -v WARNING; }
case $1 in
  closures|stats)
    KERNELS=h_id,h_ref,h_walk,count,fib run kernels.mjs hazel $L $D/kernels_$1.json
    run inside.mjs $L | tee $D/inside_$1.jsonl
    run tree540.mjs $L 8,16,32,64 $1 && mv tree_$1.json $D/tree_$1.json ;;
  handles)
    run handles551.mjs $L 8,16,32,64 $D/handles_$1.json ;;
  asc)
    KERNELS=sumbuild,mapinc,count run kernels.mjs hazel $L $D/kernels_$1.json ;;
esac
