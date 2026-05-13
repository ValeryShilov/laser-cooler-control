import logging
"""
Фоновый рабочий поток для тяжёлых вычислений схемы.

Выполняет маршрутизацию A* и размещение надписей в отдельном потоке,
чтобы UI-поток не блокировался при перерасчёте труб.
"""
from PySide6.QtCore import QThread, Signal

from core.models import RenderData
from services.router import AStarRouter
from services.label_placer import LabelPlacer


def get_escape_point(comp_data, port_pos, is_external=False):
    """
    Определяет направление «убегания» трубы от порта.

    Работает с snapshot-словарём компонента (потокобезопасно).
    Обе точки (exact и safe) привязаны к сетке для ортогональности.

    Args:
        comp_data: dict с ключами x, y, width, height
        port_pos: (x, y) координаты порта
        is_external: True для внешних портов (убегание влево)
    """
    gs = 10
    grid_px = round(port_pos[0] / gs) * gs
    grid_py = round(port_pos[1] / gs) * gs
    exact = (grid_px, grid_py)

    safe_dist = 20
    if is_external:
        return exact, (grid_px - safe_dist, grid_py)

    x, y = comp_data['x'], comp_data['y']
    w, h = comp_data['width'], comp_data['height']

    dist_left   = abs(port_pos[0] - x)
    dist_right  = abs(port_pos[0] - (x + w))
    dist_top    = abs(port_pos[1] - y)
    dist_bottom = abs(port_pos[1] - (y + h))

    min_dist = min(dist_left, dist_right, dist_top, dist_bottom)

    if min_dist == dist_left:
        return exact, (grid_px - safe_dist, grid_py)
    elif min_dist == dist_right:
        return exact, (grid_px + safe_dist, grid_py)
    elif min_dist == dist_top:
        return exact, (grid_px, grid_py - safe_dist)
    else:
        return exact, (grid_px, grid_py + safe_dist)


# Приоритет маршрутизации: сначала простые трубы, потом сложные
_TYPE_PRIORITY = {
    'freon': 0,
    'freon_bypass': 1,
    'water_lt': 2,
    'water_ht': 3,
    'drain': 4,
    'mechanical': 99,
}


logger = logging.getLogger(__name__)


def compute_routes_and_labels(comp_snapshot, connections, width, height):
    """
    Оркестратор: синхронный расчёт маршрутов и надписей.

    Args:
        comp_snapshot: dict {id: {x, y, width, height, ports, id, class_name}}
        connections: list of connection dicts
        width, height: размеры области

    Returns:
        RenderData с маршрутами труб и позициями надписей
    """
    router = _create_router(comp_snapshot, width, height)
    obstacle_count = len(router.obstacles)
    logger.debug("Step: create_router", extra={"journal_entry": {
        "step": "create_router",
        "context": {},
        "input": {"comp_count": len(comp_snapshot), "width": width, "height": height},
        "output": {"obstacles": obstacle_count},
        "decision": None,
    }})

    pipe_paths = _route_all_pipes(router, comp_snapshot, connections)
    logger.debug("Step: route_pipes", extra={"journal_entry": {
        "step": "route_pipes",
        "context": {},
        "input": {"connections_count": len(connections)},
        "output": {"routed_pipes": len(pipe_paths),
                   "pipe_types": [t for _, t in pipe_paths]},
        "decision": None,
    }})

    label_positions = _compute_labels(comp_snapshot, router.drawn_cells, width, height)
    logger.debug("Step: compute_labels", extra={"journal_entry": {
        "step": "compute_labels",
        "context": {},
        "input": {"drawn_cells_count": len(router.drawn_cells)},
        "output": {"labels": dict(label_positions)},
        "decision": None,
    }})

    result = RenderData(
        pipe_paths=pipe_paths, 
        label_positions=label_positions,
        obstacles=list(router.obstacles)
    )
    return result


def _create_router(comp_snapshot, width, height):
    """Создаёт роутер и добавляет компоненты как препятствия."""
    router = AStarRouter(width=width, height=height, grid_size=10)
    for cid, data in comp_snapshot.items():
        if data['class_name'] != 'ExternalPort':
            router.add_obstacle(data['x'], data['y'], data['width'], data['height'], padding=10)
    return router


def _route_all_pipes(router, comp_snapshot, connections):
    """Маршрутизация всех труб в порядке приоритета типов."""
    sorted_conns = sorted(connections, key=lambda c: _TYPE_PRIORITY.get(c['type'], 5))
    pipe_paths = []

    for conn in sorted_conns:
        if conn['type'] == 'mechanical':
            continue

        path_pts = _route_single_pipe(router, comp_snapshot, conn)
        if path_pts:
            pipe_paths.append((path_pts, conn['type']))

    return pipe_paths


def _route_single_pipe(router, comp_snapshot, conn):
    """Маршрутизация одной трубы между двумя компонентами."""
    src_data = comp_snapshot.get(conn['source_id'])
    tgt_data = comp_snapshot.get(conn['target_id'])
    if not src_data or not tgt_data:
        return None

    src_port_name = conn.get('source_port', 'out')
    tgt_port_name = conn.get('target_port', 'in')

    start_pos = src_data['ports'].get(src_port_name, (src_data['x'], src_data['y']))
    end_pos   = tgt_data['ports'].get(tgt_port_name, (tgt_data['x'], tgt_data['y']))

    is_src_ext = 'port_' in src_data['id']
    is_tgt_ext = 'port_' in tgt_data['id']

    exact_start, safe_start = get_escape_point(src_data, start_pos, is_src_ext)
    exact_end,   safe_end   = get_escape_point(tgt_data, end_pos,   is_tgt_ext)

    path_pts = router.find_path(exact_start, exact_end, safe_start, safe_end, waypoints=[])
    return path_pts if path_pts else None


def _compute_labels(comp_snapshot, drawn_cells, width, height):
    """Вычисляет оптимальные позиции надписей."""
    placer = LabelPlacer(comp_snapshot, drawn_cells, width, height)
    return placer.compute()


def make_comp_snapshot(components):
    """Создаёт потокобезопасный снимок позиций компонентов.

    Args:
        components: dict {id: BaseEquipment}

    Returns:
        dict {id: {x, y, width, height, ports, id, class_name}}
    """
    snapshot = {}
    for cid, comp in components.items():
        snapshot[cid] = {
            'x': comp.x,
            'y': comp.y,
            'width': comp.width,
            'height': comp.height,
            'ports': dict(comp.ports),
            'id': comp.id,
            'class_name': type(comp).__name__,
        }
    return snapshot


class SchemeWorker(QThread):
    """Фоновый поток: вычисляет маршруты труб и позиции надписей."""

    render_ready = Signal(object, int)  # (RenderData, generation)

    def __init__(self, comp_snapshot, connections, width, height, generation, parent=None):
        super().__init__(parent)
        self._snapshot = comp_snapshot
        self._connections = connections
        self._width = width
        self._height = height
        self._generation = generation

    def run(self):
        """Точка входа потока."""
        result = compute_routes_and_labels(
            self._snapshot, self._connections, self._width, self._height
        )
        result.generation = self._generation
        self.render_ready.emit(result, self._generation)
