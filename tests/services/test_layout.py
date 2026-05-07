from services.layout import TopologyLayoutEngine
from ui.equipment import Tank, Pump, ExternalPort, Heater, Compressor, Condenser, Throttle, Valve

def test_layout_external_ports(test_log):
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

    max_main_x = max(components["tank"].x + components["tank"].width,
                     components["pump"].x + components["pump"].width)

    test_log.check("port_in правее основных", components["port_in"].x, max_main_x, op="gt")
    test_log.check("port_out правее основных", components["port_out"].x, max_main_x, op="gt")
    test_log.check("port_in выровнен по Y",
                   components["port_in"].y,
                   components["tank"].ports["water_lt_in"][1] - 20,
                   op="approx", abs=20)
    test_log.check("port_out выровнен по Y",
                   components["port_out"].y,
                   components["pump"].ports["out"][1] - 20,
                   op="approx", abs=20)

def test_layout_place_downstream(test_log):
    engine = TopologyLayoutEngine(padding=50)
    engine.width = 1000
    engine.height = 600

    tank = Tank(0, 0)
    pump = Pump(0, 0)
    tank.id = "tank"
    pump.id = "pump"
    tank.x = 400
    tank.y = 200
    tank.update_ports()

    safe_w = engine.width - 2 * engine.padding
    safe_h = engine.height - 2 * engine.padding

    engine._place_downstream(pump, tank, "water_lt", safe_w, safe_h)
    test_log.check("Насос правее бака", pump.x, tank.x + tank.width, op="gt")

    port_y = tank.ports["water_out"][1]
    test_log.check("Насос на уровне water_out", pump.y, port_y, op="approx", abs=20)

    heater = Heater(0, 0)
    heater.id = "heater"
    engine._place_downstream(heater, pump, "water_ht", safe_w, safe_h)

    expected_y = round((engine.padding + safe_h * 0.50 - heater.height / 2) / 10) * 10
    test_log.check("ТЭН на 50% высоты", heater.y, expected_y)

def test_layout_nudge_to_free(test_log):
    engine = TopologyLayoutEngine(padding=50)
    engine.width = 1000
    engine.height = 600

    main_comps = {
        "pump1": Pump(300, 300),
        "pump2": Pump(300, 300)
    }
    main_comps["pump1"].id = "pump1"
    main_comps["pump2"].id = "pump2"

    positioned = {"pump1"}

    test_log.check("Пересечение до сдвига",
                   engine._overlaps_any(main_comps["pump2"], main_comps, positioned, exclude_id="pump2"),
                   True, op="is")

    engine._nudge_to_free(main_comps["pump2"], main_comps, positioned, "pump2")

    test_log.check("Нет пересечения после сдвига",
                   engine._overlaps_any(main_comps["pump2"], main_comps, positioned, exclude_id="pump2"),
                   False, op="is")

    moved = main_comps["pump2"].x != 300 or main_comps["pump2"].y != 300
    test_log.check("pump2 сдвинулся с (300,300)", moved, True, op="is")

def test_layout_find_cycle(test_log):
    engine = TopologyLayoutEngine()

    adj = {
        "comp": ["cond"],
        "cond": ["thr"],
        "thr": ["evap"],
        "evap": ["comp"],
        "other": ["comp"]
    }
    valid = {"comp", "cond", "thr", "evap", "other"}

    cycle = engine._find_cycle(adj, valid)

    test_log.check("Длина цикла", len(cycle), 4)
    test_log.check("comp в цикле", "comp", cycle, op="in")
    test_log.check("cond в цикле", "cond", cycle, op="in")
    test_log.check("thr в цикле", "thr", cycle, op="in")
    test_log.check("evap в цикле", "evap", cycle, op="in")

def test_layout_cycle_rect_positions(test_log):
    engine = TopologyLayoutEngine()

    pts = engine._cycle_rect_positions(4)
    test_log.check("Количество позиций (n=4)", len(pts), 4)
    test_log.check("Позиция 0 (bottom-left)", pts[0], (0.12, 0.82))
    test_log.check("Позиция 1 (top-left)", pts[1], (0.12, 0.22))
    test_log.check("Позиция 2 (top-center)", pts[2], (0.32, 0.12))
    test_log.check("Позиция 3 (center)", pts[3], (0.50, 0.50))

    pts_5 = engine._cycle_rect_positions(5)
    test_log.check("Количество позиций (n=5)", len(pts_5), 5)
    test_log.check("5-я позиция уникальна", pts_5[4] != pts_5[0], True, op="is")

def test_layout_place_bypass(test_log):
    engine = TopologyLayoutEngine(padding=50)
    engine.width = 1000
    engine.height = 600

    comp = Compressor(300, 400)
    cond = Condenser(300, 100)
    valve = Valve(0, 0)

    main_comps = {"comp": comp, "cond": cond, "valve": valve}
    cycle = ["comp", "cond"]

    engine._place_bypass(valve, anchor=comp, cycle=cycle, main_comps=main_comps, safe_w=900, safe_h=500)

    expected_x = round((comp.x + comp.width + 80) / 10) * 10
    expected_y = round((cond.y + cond.height + 30 - valve.height / 2) / 10) * 10
    test_log.check("X клапана байпаса", valve.x, expected_x)
    test_log.check("Y клапана байпаса", valve.y, expected_y)

def test_layout_freon_cycle_integration(test_log):
    engine = TopologyLayoutEngine(padding=50)

    components = {
        "comp": Compressor(0, 0),
        "cond": Condenser(0, 0),
        "thr": Throttle(0, 0),
        "evap": Tank(0, 0)
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

    for cid, c in components.items():
        moved = c.x != 0 or c.y != 0
        test_log.check(f"Компонент {cid} размещён", moved, True, op="is")

    test_log.check("Компрессор левее бака", components["comp"].x, components["evap"].x, op="lt")
    test_log.check("Компрессор ниже конденсатора", components["comp"].y, components["cond"].y, op="gt")
