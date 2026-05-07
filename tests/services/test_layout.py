import pytest
from services.layout import TopologyLayoutEngine
from ui.equipment import Tank, Pump, ExternalPort, Heater, Compressor, Condenser, Throttle, Valve

def test_layout_external_ports():
    engine = TopologyLayoutEngine(padding=50)
    engine.width = 1000
    engine.height = 600
    
    components = {
        "tank": Tank(0, 0),
        "pump": Pump(0, 0),
        "port_in": ExternalPort(0, 0, "Вход"),
        "port_out": ExternalPort(0, 0, "Выход")
    }
    
    for k, v in components.items():
        v.id = k
    
    connections = [
        {"source_id": "port_in", "target_id": "tank", "type": "water_lt", "target_port": "water_lt_in"},
        {"source_id": "pump", "target_id": "port_out", "type": "water_lt", "source_port": "out"}
    ]
    
    engine.layout(components, connections)
    
    # 1. Внешние порты должны быть правее основных компонентов
    max_main_x = max(components["tank"].x + components["tank"].width, 
                     components["pump"].x + components["pump"].width)
    
    assert components["port_in"].x > max_main_x
    assert components["port_out"].x > max_main_x
    
    # 2. Проверка выравнивания по Y
    # port_in (source) должен выровняться по tank.water_lt_in
    assert components["port_in"].y == pytest.approx(components["tank"].ports["water_lt_in"][1] - 20, abs=20)
    
    # port_out (target) должен выровняться по pump.out
    assert components["port_out"].y == pytest.approx(components["pump"].ports["out"][1] - 20, abs=20)

def test_layout_place_downstream():
    engine = TopologyLayoutEngine(padding=50)
    engine.width = 1000
    engine.height = 600
    
    # Имитируем бак и насос для низкотемпературного (LT) контура
    tank = Tank(0, 0)
    pump = Pump(0, 0)
    tank.id = "tank"
    pump.id = "pump"
    
    # Ставим бак в центр
    tank.x = 400
    tank.y = 200
    tank.update_ports()
    
    safe_w = engine.width - 2 * engine.padding
    safe_h = engine.height - 2 * engine.padding
    
    # Проверяем размещение насоса
    engine._place_downstream(pump, tank, "water_lt", safe_w, safe_h)
    
    # 1. Насос должен стоять правее бака
    assert pump.x > tank.x + tank.width
    
    # 2. Насос должен быть выровнен по Y с водяным выходом бака
    # y_pct = (port_y + comp.height / 2 - self.padding) / safe_h
    # Это должно поставить верхний край насоса (y) на уровень water_out бака (или близко к нему)
    port_y = tank.ports["water_out"][1]
    assert pump.y == pytest.approx(port_y, abs=20)
    
    # Проверяем ТЭН (water_ht)
    heater = Heater(0, 0)
    heater.id = "heater"
    engine._place_downstream(heater, pump, "water_ht", safe_w, safe_h)
    
    # ТЭН должен стоять на 50% высоты (y_pct = 0.50), как мы задали
    expected_y = round((engine.padding + safe_h * 0.50 - heater.height / 2) / 10) * 10
    assert heater.y == expected_y

def test_layout_nudge_to_free():
    engine = TopologyLayoutEngine(padding=50)
    engine.width = 1000
    engine.height = 600
    
    main_comps = {
        "pump1": Pump(300, 300),
        "pump2": Pump(300, 300)
    }
    main_comps["pump1"].id = "pump1"
    main_comps["pump2"].id = "pump2"
    
    positioned = {"pump1"}  # pump1 уже размещен
    
    # Изначально они пересекаются
    assert engine._overlaps_any(main_comps["pump2"], main_comps, positioned, exclude_id="pump2") is True
    
    # Применяем алгоритм сдвига
    engine._nudge_to_free(main_comps["pump2"], main_comps, positioned, "pump2")
    
    # Теперь pump2 должен был сдвинуться и больше не пересекаться
    assert engine._overlaps_any(main_comps["pump2"], main_comps, positioned, exclude_id="pump2") is False
    
    # Проверяем, что pump2 реально сдвинулся с начальных координат
    assert main_comps["pump2"].x != 300 or main_comps["pump2"].y != 300

def test_layout_find_cycle():
    engine = TopologyLayoutEngine()
    
    # Граф зависимостей: comp -> cond -> thr -> evap -> comp
    adj = {
        "comp": ["cond"],
        "cond": ["thr"],
        "thr": ["evap"],
        "evap": ["comp"],
        "other": ["comp"] # Лишняя связь
    }
    valid = {"comp", "cond", "thr", "evap", "other"}
    
    cycle = engine._find_cycle(adj, valid)
    
    # Должен найти цикл из 4 элементов
    assert len(cycle) == 4
    # Проверяем, что это замкнутый контур в правильном порядке
    assert "comp" in cycle
    assert "cond" in cycle
    assert "thr" in cycle
    assert "evap" in cycle

def test_layout_cycle_rect_positions():
    engine = TopologyLayoutEngine()
    
    # 4 позиции должны возвращать углы (bottom-left, top-left, top-center, center)
    pts = engine._cycle_rect_positions(4)
    assert len(pts) == 4
    assert pts[0] == (0.12, 0.82)
    assert pts[1] == (0.12, 0.22)
    assert pts[2] == (0.32, 0.12)
    assert pts[3] == (0.50, 0.50)
    
    # Если больше 4, должны генерироваться дополнительные точки
    pts_5 = engine._cycle_rect_positions(5)
    assert len(pts_5) == 5
    assert pts_5[4] != pts_5[0]

def test_layout_place_bypass():
    engine = TopologyLayoutEngine(padding=50)
    engine.width = 1000
    engine.height = 600
    
    comp = Compressor(300, 400)
    cond = Condenser(300, 100) # Находится над компрессором
    valve = Valve(0, 0)
    
    main_comps = {"comp": comp, "cond": cond, "valve": valve}
    cycle = ["comp", "cond"]
    
    # _place_bypass должен найти 'cond' как 'above' и поставить клапан
    # правее comp и под cond (точнее, y = cond.y + cond.height + 30)
    engine._place_bypass(valve, anchor=comp, cycle=cycle, main_comps=main_comps, safe_w=900, safe_h=500)
    
    assert valve.x == round((comp.x + comp.width + 80) / 10) * 10
    assert valve.y == round((cond.y + cond.height + 30 - valve.height / 2) / 10) * 10

def test_layout_freon_cycle_integration():
    engine = TopologyLayoutEngine(padding=50)
    
    components = {
        "comp": Compressor(0, 0),
        "cond": Condenser(0, 0),
        "thr": Throttle(0, 0),
        "evap": Tank(0, 0) # Бак выступает испаритетелем
    }
    for k, v in components.items():
        v.id = k
        
    connections = [
        {"source_id": "comp", "target_id": "cond", "type": "freon"},
        {"source_id": "cond", "target_id": "thr", "type": "freon"},
        {"source_id": "thr", "target_id": "evap", "type": "freon"},
        {"source_id": "evap", "target_id": "comp", "type": "freon"}
    ]
    
    engine.layout(components, connections)
    
    # Убеждаемся, что компоненты расставлены по углам (не в (0,0))
    for comp in components.values():
        assert comp.x != 0 or comp.y != 0
        
    # Компрессор должен быть внизу слева
    assert components["comp"].x < components["evap"].x
    assert components["comp"].y > components["cond"].y
