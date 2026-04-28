"""
Трассирует все трубы с новой escape-point логикой.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)

from parser import SchemeParser
from layout import TopologyLayoutEngine
from router import AStarRouter

parser = SchemeParser("scheme.yaml")
components, connections = parser.parse()

engine = TopologyLayoutEngine(padding=80)
engine.width = 1000
engine.height = 500
engine.layout(components, connections)

# Print port positions
print("=== Key port positions ===")
for cid in ['tank_1', 'pump_1', 'heater_1']:
    comp = components[cid]
    print(f"  {cid}: pos=({comp.x},{comp.y}) size={comp.width}x{comp.height}")
    for pname, ppos in comp.ports.items():
        print(f"    .{pname} = ({ppos[0]}, {ppos[1]})")

# Trace routing
print("\n=== Pipe routing ===")
router = AStarRouter(width=1000, height=500, grid_size=10)
for comp in components.values():
    if "ext_" not in comp.id:
        router.add_obstacle(comp.x, comp.y, comp.width, comp.height, padding=10)

def get_escape_point(obj, port_pos, is_external=False):
    grid_px = round(port_pos[0] / 10) * 10
    grid_py = round(port_pos[1] / 10) * 10
    safe_dist = 30
    if is_external:
        return (grid_px, grid_py), (grid_px - safe_dist, grid_py)

    dist_left   = abs(port_pos[0] - obj.x)
    dist_right  = abs(port_pos[0] - (obj.x + obj.width))
    dist_top    = abs(port_pos[1] - obj.y)
    dist_bottom = abs(port_pos[1] - (obj.y + obj.height))
    min_dist = min(dist_left, dist_right, dist_top, dist_bottom)

    if min_dist == dist_left:
        return (grid_px, grid_py), (grid_px - safe_dist, grid_py)
    elif min_dist == dist_right:
        return (grid_px, grid_py), (grid_px + safe_dist, grid_py)
    elif min_dist == dist_top:
        return (grid_px, grid_py), (grid_px, grid_py - safe_dist)
    else:
        return (grid_px, grid_py), (grid_px, grid_py + safe_dist)

type_priority = {'freon': 0, 'freon_bypass': 1, 'water_lt': 2, 'water_ht': 3, 'drain': 4, 'mechanical': 99}
sorted_connections = sorted(connections, key=lambda c: type_priority.get(c['type'], 5))

for conn in sorted_connections:
    if conn['type'] == 'mechanical':
        continue
    src_obj = components.get(conn['source_id'])
    tgt_obj = components.get(conn['target_id'])
    if not src_obj or not tgt_obj:
        continue

    src_port_name = conn.get('source_port', 'out')
    tgt_port_name = conn.get('target_port', 'in')
    start_pos = src_obj.ports.get(src_port_name, (src_obj.x, src_obj.y))
    end_pos = tgt_obj.ports.get(tgt_port_name, (tgt_obj.x, tgt_obj.y))

    exact_start, safe_start = get_escape_point(src_obj, start_pos, "ext_" in src_obj.id)
    exact_end, safe_end = get_escape_point(tgt_obj, end_pos, "ext_" in tgt_obj.id)

    path_pts = router.find_path(exact_start, exact_end, safe_start, safe_end, waypoints=[])

    label = f"{conn['source_id']}.{src_port_name} -> {conn['target_id']}.{tgt_port_name} ({conn['type']})"
    print(f"\n  {label}")
    print(f"    exact: {exact_start} -> {exact_end}")
    print(f"    safe:  {safe_start} -> {safe_end}")
    if path_pts:
        turns = 0
        for i in range(2, len(path_pts)):
            d1 = (path_pts[i-1][0] - path_pts[i-2][0], path_pts[i-1][1] - path_pts[i-2][1])
            d2 = (path_pts[i][0] - path_pts[i-1][0], path_pts[i][1] - path_pts[i-1][1])
            if d1 != d2: turns += 1
        print(f"    path ({len(path_pts)} pts, {turns} turns): {path_pts}")
    else:
        print(f"    *** NO PATH FOUND! ***")

# Compare with SVG reference paths
print("\n=== SVG Reference (with +120 offset) ===")
svg_pipes = {
    "comp_1->cond_1 (freon)": "vertical UP: (210,280)->(210,210)",
    "cond_1->throttle_1 (freon)": "UP+RIGHT: (210,50)->(210,30)->(330,30)",
    "throttle_1->tank_1 (freon)": "RIGHT+DOWN+RIGHT: (370,30)->(420,30)->(420,180)->(460,180)",
    "tank_1->comp_1 (freon)": "LEFT+DOWN: (460,350)->(250,350)->(250,320)",
    "comp_1->valve_bp (bypass)": "RIGHT: (210,230)->(300,230)",
    "valve_bp->comp_1 (bypass)": "RIGHT: (340,230)->(420,230)",
    "tank_1->pump_1 (water_lt)": "RIGHT: (560,320)->(620,320)",
    "pump_1->ext_laser_out": "RIGHT: (680,320)->(870,320)",
    "ext_laser_in->tank_1": "LEFT+DOWN: (870,60)->(540,60)->(540,160)",
    "ext_optics_in->tank_1": "LEFT+DOWN: (870,120)->(500,120)->(500,160)",
    "pump_1->heater_1": "UP+RIGHT: (700,320)->(700,200)->(730,200)",
    "heater_1->ext_optics_out": "RIGHT: (770,200)->(870,200)",
    "tank_1.drain->ext_drain": "DOWN+RIGHT: (520,360)->(520,400)->(870,400)",
}
for name, desc in svg_pipes.items():
    print(f"  {name}: {desc}")
