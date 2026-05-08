import logging
from services.router import AStarRouter
from services.worker import get_escape_point


# ══════════════════════════════════════
#  Существующие тесты
# ══════════════════════════════════════

def test_astar_simple_path(test_log):
    router = AStarRouter(width=200, height=200, grid_size=10)

    start = (10, 10)
    end = (100, 10)

    path = router.find_path(start, end, start, end)
    test_log.check("Путь найден", len(path), 0, op="gt")
    test_log.check("Начало пути", path[0], start)
    test_log.check("Конец пути", path[-1], end)

def test_astar_obstacle_avoidance(test_log):
    router = AStarRouter(width=200, height=200, grid_size=10)
    router.add_obstacle(50, 70, 10, 60, padding=5)

    start = (10, 100)
    end = (100, 100)

    path = router.find_path(start, end, start, end)
    test_log.check("Путь найден с обходом", len(path), 0, op="gt")
    test_log.check("Путь не прямой (> 2 точек)", len(path), 2, op="gt")
    test_log.check("Начало пути", path[0], start)
    test_log.check("Конец пути", path[-1], end)

    for pt in path[1:-1]:
        blocked = router._is_blocked(pt[0], pt[1])
        test_log.check(f"Точка {pt} не заблокирована", blocked, False, op="is")

def test_get_escape_point(test_log):
    comp_data = {"x": 100, "y": 100, "width": 80, "height": 60}
    port_pos = (100, 130)

    exact, safe = get_escape_point(comp_data, port_pos, is_external=False)

    test_log.check("Exact на сетке", exact[0] % 10, 0)
    test_log.check("Safe левее exact (левая грань)", safe[0], exact[0], op="lt")
    test_log.check("Safe.y == Exact.y", safe[1], exact[1])

def test_router_register_path_avoidance(test_log):
    router = AStarRouter(width=300, height=300, grid_size=10)

    path1 = [(10, 10), (100, 10)]
    router.register_path(path1)

    test_log.check("(50, 10) в drawn_cells", (50, 10), router.drawn_cells, op="in")

def test_router_smooth_path(test_log):
    router = AStarRouter(width=200, height=200, grid_size=10)

    zigzag = [(10, 10), (50, 10), (50, 50), (100, 50)]
    smooth = router._smooth_path(zigzag)

    test_log.check("Сглаженный путь не длиннее", len(smooth), len(zigzag), op="le")
    test_log.check("Начало сохранено", smooth[0], zigzag[0])
    test_log.check("Конец сохранён", smooth[-1], zigzag[-1])


# ══════════════════════════════════════
#  Unit-тесты для новых подметодов
# ══════════════════════════════════════

def test_build_waypoint_chain(test_log):
    router = AStarRouter(width=200, height=200, grid_size=10)

    chain = router._build_waypoint_chain((10, 10), (100, 100), None)
    test_log.check("Без waypoints — 2 точки", len(chain), 2)
    test_log.check("Первая = safe_start", chain[0], (10, 10))
    test_log.check("Последняя = safe_end", chain[-1], (100, 100))

    chain2 = router._build_waypoint_chain((10, 10), (100, 100), [(55, 55)])
    test_log.check("С waypoint — 3 точки", len(chain2), 3)
    test_log.check("Waypoint привязан к сетке", chain2[1], (60, 60))

def test_route_through_points(test_log):
    router = AStarRouter(width=200, height=200, grid_size=10)
    points = [(10, 10), (100, 10)]
    path = router._route_through_points(points)
    test_log.check("Путь найден", len(path), 0, op="gt")
    test_log.check("Начало", path[0], (10, 10))
    test_log.check("Конец", path[-1], (100, 10))

def test_build_exempt_set(test_log):
    router = AStarRouter(width=200, height=200, grid_size=10)
    exempt = router._build_exempt_set((10, 10), (100, 10), (20, 10), (90, 10))
    test_log.check("exact_start в exempt", (10, 10), exempt, op="in")
    test_log.check("exact_end в exempt", (100, 10), exempt, op="in")
    test_log.check("safe_start в exempt", (20, 10), exempt, op="in")
    test_log.check("safe_end в exempt", (90, 10), exempt, op="in")

def test_cleanup_path(test_log):
    router = AStarRouter(width=200, height=200, grid_size=10)
    # Дубликаты
    path = [(10, 10), (10, 10), (50, 10)]
    clean = router._cleanup_path(path)
    test_log.check("Дубликат удалён", len(clean), 2)

    # Коллинеарные
    path2 = [(10, 10), (30, 10), (50, 10)]
    clean2 = router._cleanup_path(path2)
    test_log.check("Коллинеарная точка удалена", len(clean2), 2)
    test_log.check("Сохранены крайние", clean2, [(10, 10), (50, 10)])

def test_line_clear(test_log):
    router = AStarRouter(width=200, height=200, grid_size=10)
    # Горизонтальная линия без препятствий
    test_log.check("Свободная линия", router._line_clear((10, 10), (50, 10)), True, op="is")

    # С препятствием
    router.add_obstacle(30, 0, 10, 20, padding=0)
    test_log.check("Заблокированная линия", router._line_clear((10, 10), (50, 10)), False, op="is")


# ══════════════════════════════════════
#  Интеграционный тест с журналом
# ══════════════════════════════════════

def test_find_path_journal(test_log, caplog):
    caplog.set_level(logging.DEBUG)
    router = AStarRouter(width=200, height=200, grid_size=10)

    start = (10, 10)
    end = (100, 10)

    path = router.find_path(start, end, start, end)
    journal = [r.journal_entry for r in caplog.records if hasattr(r, "journal_entry")]

    test_log.check("Путь найден", len(path), 0, op="gt")
    test_log.check("Журнал не пустой", len(journal), 0, op="gt")

    steps = [e["step"] for e in journal]
    test_log.check("build_waypoints в журнале", "build_waypoints", steps, op="in")
    test_log.check("route_segments в журнале", "route_segments", steps, op="in")
    test_log.check("smooth_path в журнале", "smooth_path", steps, op="in")
    test_log.check("final_path в журнале", "final_path", steps, op="in")

    # Проверяем структуру записей
    for entry in journal:
        test_log.check(f"[{entry['step']}] имеет context", "context" in entry, True, op="is")
        test_log.check(f"[{entry['step']}] имеет input", "input" in entry, True, op="is")
        test_log.check(f"[{entry['step']}] имеет output", "output" in entry, True, op="is")
        test_log.check(f"[{entry['step']}] имеет decision", "decision" in entry, True, op="is")

    # final_path содержит итоговый путь
    final = [e for e in journal if e["step"] == "final_path"][0]
    test_log.check("final_path.output.total_points", final["output"]["total_points"], len(path))

    # Результат совпадает с обычным вызовом
    router2 = AStarRouter(width=200, height=200, grid_size=10)
    path_normal = router2.find_path(start, end, start, end)
    test_log.check("Результат с журналом = без", path, path_normal)


def test_find_path_journal_no_path(test_log, caplog):
    """Проверяет журнал когда путь не найден."""
    caplog.set_level(logging.DEBUG)
    router = AStarRouter(width=50, height=50, grid_size=10)
    # Полностью заблокированная область
    router.add_obstacle(0, 0, 50, 50, padding=0)

    path = router.find_path((0, 0), (40, 40), (0, 0), (40, 40))
    journal = [r.journal_entry for r in caplog.records if hasattr(r, "journal_entry")]

    test_log.check("Путь пустой", len(path), 0)
    test_log.check("Журнал не пустой", len(journal), 0, op="gt")

    route_entry = [e for e in journal if e["step"] == "route_segments"][0]
    test_log.check("raw_path_length = 0", route_entry["output"]["raw_path_length"], 0)
    test_log.check("decision = no_path_found",
                   route_entry["decision"]["result"], "no_path_found")
