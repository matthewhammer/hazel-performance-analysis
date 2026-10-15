#!/bin/sh
# with_chromium.sh <tag> <command...>: a fresh headless Chromium with debug
# port 9333 (gc exposed, precise memory), the command, then Browser.close
# (a snap's processes refuse a plain kill).
PROF=$HOME/snap/chromium/common/r58-$1; shift; rm -rf "$PROF"; mkdir -p "$PROF"
chromium --headless=new --remote-debugging-port=9333 --user-data-dir="$PROF" --enable-precise-memory-info \
  --js-flags=--expose-gc --window-size=1600,1100 --no-first-run --no-default-browser-check about:blank >/dev/null 2>&1 &
for i in $(seq 1 60); do sleep 0.5; python3 -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:9333/json/version',timeout=1)" 2>/dev/null && break; done
"$@"; RC=$?
node $HOME/.cache/hazel-diag/r58/close_browser.mjs 9333 >/dev/null 2>&1; sleep 2; rm -rf "$PROF"
exit $RC
