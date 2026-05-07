import pytest
from services.router import AStarRouter
from services.worker import get_escape_point

def test_astar_simple_path():
    router = AStarRouter(width=200, height=200, grid_size=10)
    
    start = (10, 10)
    end = (100, 10)
    
    path = router.find_path(start, end, start, end)
    assert path is not None
    assert path[0] == start
    assert path[-1] == end
    # Путь по прямой не должен иметь лишних поворотов
    assert len(path) == 2 or (len(path) > 2 and all(p[1] == 10 for p in path))

def test_astar_obstacle_avoidance():
    router = AStarRouter(width=200, height=200, grid_size=10)
    
    start = (10, 50)
    end = (100, 50)
    
    # Добавляем препятствие прямо на пути
    router.add_obstacle(40, 30, 20, 40, padding=10)
    
    path = router.find_path(start, end, start, end)
    assert path is not None
    
    # Проверяем, что путь не проходит через препятствие
    for x, y in path:
        # С учетом паддинга препятствие занимает X от 30 до 70, Y от 20 до 80
        in_obstacle = (30 <= x <= 70) and (20 <= y <= 80)
        assert not in_obstacle, f"Point {x},{y} is inside obstacle!"

def test_get_escape_point(mock_components_snapshot):
    tank = mock_components_snapshot["tank"]
    port_in = mock_components_snapshot["port_in"]
    
    # Тест для обычного компонента (бак). Порт сверху.
    # get_escape_point должно отвести трубу вверх
    port_pos = tank["ports"]["water_lt_in"] # (490, 130) при x=400, y=150
    exact, safe = get_escape_point(tank, port_pos, is_external=False)
    
    assert exact == (490, 130)
    assert safe == (490, 110) # Должно отступить на 20px вверх (y-20)
    
    # Тест для внешнего порта (всегда влево)
    port_pos = port_in["ports"]["in"] # (800, 150)
    exact, safe = get_escape_point(port_in, port_pos, is_external=True)
    
    assert exact == (800, 150)
    assert safe == (780, 150)

def test_router_register_path_avoidance():
    router = AStarRouter(width=200, height=200, grid_size=10)
    
    start = (10, 10)
    end = (100, 10)
    
    # Первая труба
    path1 = router.find_path(start, end, start, end)
    assert path1 is not None
    
    # Регистрируем первую трубу как препятствие (чтобы следующая на неё не легла)
    router.register_path(path1)
    
    # Вторая труба (из той же точки в ту же)
    path2 = router.find_path(start, end, start, end)
    assert path2 is not None
    
    # Пути должны отличаться, так как вторая труба должна "обходить" первую
    # (кроме точек старта и финиша)
    assert path1 != path2
    
    # Проверяем, что хотя бы одна промежуточная точка отличается
    mid_points1 = set(path1[1:-1])
    mid_points2 = set(path2[1:-1])
    assert mid_points1 != mid_points2

def test_router_smooth_path():
    router = AStarRouter(width=200, height=200, grid_size=10)
    
    # Искусственно создаем извилистый путь (лесенкой)
    zig_zag_path = [
        (10, 10),
        (10, 20),
        (20, 20),
        (20, 30),
        (30, 30)
    ]
    
    smoothed = router._smooth_path(zig_zag_path)
    
    # Сглаженный путь должен иметь меньше точек (изломов), чем исходная "лесенка"
    assert len(smoothed) < len(zig_zag_path)
    # Старт и конец должны сохраниться
    assert smoothed[0] == (10, 10)
    assert smoothed[-1] == (30, 30)
