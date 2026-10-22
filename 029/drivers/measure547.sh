#!/bin/sh
# ^ticket(547) (and 551, stacked on it): the counter build against trial/r25-closures, alternating, one node process at a
# time; then 540's tree on both, and the handles driver on trial/r25-handles. Rows to data/fixes/.
cd $(dirname "$0"); D=../data/fixes; L=~/.cache/hazel-r25/libs
run() { taskset -c 0-1 nice -n 10 timeout 900 node --stack-size=8000 "$@" 2>&1 | grep -v WARNING; }
for r in 1 2; do for lib in stats closures; do
  KERNELS=h_id,h_ref,h_walk,count run kernels.mjs hazel $L/$lib/hazel-lib.js $D/k547_${lib}_$r.json | sed "s/^/$lib r$r /" | grep -E "h_ref|h_walk"
done; done
run inside.mjs $L/closures/hazel-lib.js | tee $D/inside_closures.jsonl
for lib in stats closures; do run tree540.mjs $L/$lib/hazel-lib.js 8,16,32,64 $lib && mv tree_$lib.json $D/tree_$lib.json; done
run handles551.mjs $L/handles/hazel-lib.js 8,16,32,64 $D/handles_handles.json
