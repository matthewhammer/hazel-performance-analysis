# The sampled profile's live bytes, by the innermost Reason source file on each stack.
import json, re, sys, collections
prof, bundle = sys.argv[1], sys.argv[2]
rx = re.compile(r"/\*<<(src/[^>:]+)")
src_at=[]; last="?"
with open(bundle, encoding="utf-8", errors="replace") as f:
    for line in f:
        m = rx.findall(line)
        if m: last = m[-1]
        src_at.append(last)
p = json.load(open(prof))
by = collections.Counter(); byfn = collections.Counter()
def walk(node, path):
    fr = node["callFrame"]; l = fr["lineNumber"]
    s = src_at[l] if 0 <= l < len(src_at) and fr.get("url","").endswith(".js") else None
    here = path + [(fr["functionName"], s)]
    if node.get("selfSize"):
        named = [x for x in here if x[1] and x[1] != "?" and not x[0].startswith("caml_")]
        key = named[-1][1] if named else "(no src frame: " + here[-1][0] + ")"
        by[key] += node["selfSize"]
    for c in node.get("children", []): walk(c, here)
walk(p["head"], [])
tot = sum(by.values())
print("total %.1f MB" % (tot/2**20))
for k, b in by.most_common(40): print("%7.1f MB  %s" % (b/2**20, k))
