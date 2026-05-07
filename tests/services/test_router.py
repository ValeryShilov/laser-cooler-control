from services.router import AStarRouter
from services.worker import get_escape_point

def test_astar_simple_path(test_log):
    router = AStarRouter(width=200, height=200, grid_size=10)

    start = (10, 10)
    end = (100, 10)

    path = router.find_path(start, end, start, end)
    test_log.check("Путь найден", path is not None, True, op="is")
    test_log.check("Начальная точка", path[0], start)
    test_log.check("Конечная точка", path[-1], end)

    is_straight = len(path) == 2 or (len(path) > 2 and all(p[1] == 10 for p in path))
    test_log.check("Путь прямой (без зигзагов)", is_straight, True, op="is")

def test_astar_obstacle_avoidance(test_log):
    router = AStarRouter(width=200, height=200, grid_size=10)

    start = (10, 50)
    end = (100, 50)

    router.add_obstacle(40, 30, 20, 40, padding=10)

    path = router.find_path(start, end, start, end)
    test_log.check("Путь найден (с препятствием)", path is not None, True, op="is")

    collision = False
    for x, y in path:
        in_obstacle = (30 <= x <= 70) and (20 <= y <= 80)
        if in_obstacle:
            collision = True
            break
    test_log.check("Путь не пересекает препятствие", collision, False, op="is")

def test_get_escape_point(mock_components_snapshot, test_log):
    tank = mock_components_snapshot["tank"]
    port_in = mock_components_snapshot["port_in"]

    port_pos = tank["ports"]["water_lt_in"]
    exact, safe = get_escape_point(tank, port_pos, is_external=False)

    test_log.check("exact точка (бак)", exact, (490, 130))
    test_log.check("safe точка (бак, y-20)", safe, (490, 110))

    port_pos = port_in["ports"]["in"]
    exact, safe = get_escape_point(port_in, port_pos, is_external=True)

    test_log.check("exact точка (внешний порт)", exact, (800, 150))
    test_log.check("safe точка (внешний порт, x-20)", safe, (780, 150))

def test_router_register_path_avoidance(test_log):
    router = AStarRouter(width=200, height=200, grid_size=10)

    start = (10, 10)
    end = (100, 10)

    path1 = router.find_path(start, end, start, end)
    test_log.check("Первая труба найдена", path1 is not None, True, op="is")

    router.register_path(path1)

    path2 = router.find_path(start, end, start, end)
    test_log.check("Вторая труба найдена", path2 is not None, True, op="is")

    test_log.check("Маршруты отличаются", path1 != path2, True, op="is")

    mid1 = set(path1[1:-1])
    mid2 = set(path2[1:-1])
    test_log.check("Промежуточные точки различны", mid1 != mid2, True, op="is")

def test_router_smooth_path(test_log):
    router = AStarRouter(width=200, height=200, grid_size=10)

    zig_zag_path = [
        (10, 10),
        (10, 20),
        (20, 20),
        (20, 30),
        (30, 30)
    ]

    smoothed = router._smooth_path(zig_zag_path)

    test_log.check("Точек стало меньше", len(smoothed), len(zig_zag_path), op="lt")
    test_log.check("Начальная точка сохранена", smoothed[0], (10, 10))
    test_log.check("Конечная точка сохранена", smoothed[-1], (30, 30))
