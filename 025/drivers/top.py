import json,sys,collections
p=json.load(open(sys.argv[1])); nodes={n['id']:n for n in p['nodes']}
parent={}
for n in p['nodes']:
  for c in n.get('children',[]): parent[c]=n['id']
self=collections.Counter(); 
for s in p['samples']: self[s]+=1
tot=sum(self.values())
fs=collections.Counter(); incl=collections.Counter()
name=lambda n:(n['callFrame']['functionName'] or '(anon)')+':'+str(n['callFrame']['lineNumber'])
for nid,c in self.items():
  fs[name(nodes[nid])]+=c
  seen=set(); x=nid
  while x in nodes:
    k=name(nodes[x])
    if k not in seen: incl[k]+=c; seen.add(k)
    x=parent.get(x)
print("SELF");[print(f"{100*c/tot:5.1f}% {k}") for k,c in fs.most_common(20)]
print("INCL");[print(f"{100*c/tot:5.1f}% {k}") for k,c in incl.most_common(45)]
