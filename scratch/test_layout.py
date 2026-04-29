import yaml
from collections import defaultdict
import math

class FakeComp:
    def __init__(self, id, ctype, w, h):
        self.id = id
        self.type = ctype
        self.width = w
        self.height = h
        self.x = 0
        self.y = 0

def get_dimensions(ctype):
    # approximated sizes
    sizes = {
        "Compressor": (60, 60),
        "Condenser": (60, 160),
        "Fan": (40, 40),
        "Throttle": (60, 40),
        "Valve": (60, 40),
        "Tank": (100, 200),
        "Pump": (50, 50),
        "Heater": (40, 80),
        "ExternalPort": (150, 30)
    }
    return sizes.get(ctype, (50, 50))

with open("scheme.yaml", "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

comps = {}
for c in data['components']:
    w, h = get_dimensions(c['type'])
    comps[c['id']] = FakeComp(c['id'], c['type'], w, h)

connections = data['connections']

# Build graph
adj = defaultdict(list)
in_degree = defaultdict(int)

# To avoid trivial single-edge backloops, we can manually or algorithmically break cycles
for conn in connections:
    src, src_port = (conn['source'].split('.') + [None])[:2]
    tgt, tgt_port = (conn['target'].split('.') + [None])[:2]
    
    if src == tgt: continue
    
    # Heuristic: break cycles by identifying "freon_out" to "in" for tank->comp, and bypass out to in
    is_backedge = False
    if src == "tank_evaporator" and tgt == "compressor_main": is_backedge = True
    if src == "valve_bypass" and tgt == "compressor_main": is_backedge = True
    
    if not is_backedge:
        adj[src].append((tgt, conn['type']))
        in_degree[tgt] += 1

# topological assign levels
levels = {}
queue = []
for cid in comps:
    if in_degree[cid] == 0:
        queue.append(cid)
        levels[cid] = 0

while queue:
    curr = queue.pop(0)
    for nxt, ctype in adj[curr]:
        if nxt not in levels or levels[nxt] < levels[curr] + 1:
            levels[nxt] = levels[curr] + 1
        in_degree[nxt] -= 1
        if in_degree[nxt] == 0:
            queue.append(nxt)

from pprint import pprint
print("Levels:")
pprint(levels)

# Group by level
by_level = defaultdict(list)
for cid, lv in levels.items():
    by_level[lv].append(cid)

print("\nBy Level:")
pprint(dict(by_level))
