"""Quick trace test — verifies pipe routing after fixes."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

from services.parser import SchemeParser
from services.layout import TopologyLayoutEngine
from services.router import AStarRouter

parser = SchemeParser("scheme.yaml")
components, connections = parser.parse()

engine = TopologyLayoutEngine(padding=80)
engine.width = 1000
engine.height = 500
engine.layout(components, connections)

router = AStarRouter(width=1000, height=500, grid_size=10)
for comp in components.values():
    if "ext_" not in comp.id:
        router.add_obstacle(comp.x, comp.y, comp.width, comp.height, padding=10)

def get_escape_point(obj, port_pos, is_external=False):
    gs = 10
    grid_px = round(port_pos[0] / gs) * gs
    grid_py = round(port_pos[1] / gs) * gs
    exact = (grid_px, grid_py)
    safe_dist = 20
    if is_external:
        return exact, (grid_px - safe_dist, grid_py)
    dist_left   = abs(port_pos[0] - obj.x)
    dist_right  = abs(port_pos[0] - (obj.x + obj.width))
    dist_top    = abs(port_pos[1] - obj.y)
    dist_bottom = abs(port_pos[1] - (obj.y + obj.height))
    min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
    if min_dist == dist_left:
        return exact, (grid_px - safe_dist, grid_py)
    elif min_dist == dist_right:
        return exact, (grid_px + safe_dist, grid_py)
    elif min_dist == dist_top:
        return exact, (grid_px, grid_py - safe_dist)
    else:
        return exact, (grid_px, grid_py + safe_dist)

type_priority = {'freon': 0, 'freon_bypass': 1, 'water_lt': 2, 'water_ht': 3, 'drain': 4, 'mechanical': 99}
sorted_connections = sorted(connections, key=lambda c: type_priority.get(c['type'], 5))

print("=== Pipe routing results ===")
total_turns = 0
for conn in sorted_connections:
    if conn['type'] == 'mechanical':
        continue
    src_obj = components.get(conn['source_id'])
    tgt_obj = components.get(conn['target_id'])
    if not src_obj or not tgt_obj:
        continue
    src_port_name = conn.get('source_port', 'out')
    tgt_port_name = conn.get('target_port', 'in')
    start_pos = src_obj.ports.get(src_port_name)
    end_pos = tgt_obj.ports.get(tgt_port_name)
    
    if not start_pos:
        print(f"  *** MISSING PORT: {conn['source_id']}.{src_port_name}")
        continue
    if not end_pos:
        print(f"  *** MISSING PORT: {conn['target_id']}.{tgt_port_name}")
        continue

    exact_start, safe_start = get_escape_point(src_obj, start_pos, "port_" in src_obj.id)
    exact_end, safe_end = get_escape_point(tgt_obj, end_pos, "port_" in tgt_obj.id)
    path_pts = router.find_path(exact_start, exact_end, safe_start, safe_end, waypoints=[])

    label = f"{conn['source_id']}.{src_port_name} -> {conn['target_id']}.{tgt_port_name} ({conn['type']})"
    if path_pts:
        turns = 0
        for i in range(2, len(path_pts)):
            d1 = (path_pts[i-1][0] - path_pts[i-2][0], path_pts[i-1][1] - path_pts[i-2][1])
            d2 = (path_pts[i][0] - path_pts[i-1][0], path_pts[i][1] - path_pts[i-1][1])
            if d1 != d2: turns += 1
        total_turns += turns
        status = "OK" if turns <= 3 else "HIGH"
        print(f"  [{status}] {label}: {turns} turns, {len(path_pts)} pts")
        print(f"       path: {path_pts}")
    else:
        print(f"  [FAIL] {label}: NO PATH FOUND!")

print(f"\nTotal turns across all pipes: {total_turns}")
