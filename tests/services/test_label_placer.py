from services.label_placer import LabelPlacer

def test_label_placer_basic(mock_components_snapshot, test_log):
    drawn_cells = set()
    view_w, view_h = 1000, 600

    placer = LabelPlacer(mock_components_snapshot, drawn_cells, view_w, view_h)
    result = placer.compute()

    test_log.check("Позиция надписи бака", result["tank"], "bottom")
    test_log.check("Позиция надписи насоса", result["pump"], "bottom")
    test_log.check("Внешний порт исключён", "port_in" in result, False, op="is")

def test_label_placer_avoid_pipes(mock_components_snapshot, test_log):
    drawn_cells = set()
    pump = mock_components_snapshot["pump"]
    x, y, w, h = pump["x"], pump["y"], pump["width"], pump["height"]

    for px in range(x - 20, x + w + 20, 10):
        for py in range(y + h, y + h + 40, 10):
            drawn_cells.add((px, py))

    view_w, view_h = 1000, 600
    placer = LabelPlacer(mock_components_snapshot, drawn_cells, view_w, view_h)
    result = placer.compute()

    test_log.check("Надпись насоса (bottom занят)", result["pump"], "top")

def test_label_placer_avoid_pipes_right(mock_components_snapshot, test_log):
    drawn_cells = set()
    pump = mock_components_snapshot["pump"]
    x, y, w, h = pump["x"], pump["y"], pump["width"], pump["height"]

    for px in range(x - 20, x + w + 20, 10):
        for py in range(y + h, y + h + 40, 10):
            drawn_cells.add((px, py))

    for px in range(x - 20, x + w + 20, 10):
        for py in range(y - 30, y, 10):
            drawn_cells.add((px, py))

    view_w, view_h = 1000, 600
    placer = LabelPlacer(mock_components_snapshot, drawn_cells, view_w, view_h)
    result = placer.compute()

    test_log.check("Надпись насоса (bottom+top заняты)", result["pump"], "right")

def test_label_placer_avoid_pipes_left(mock_components_snapshot, test_log):
    drawn_cells = set()
    pump = mock_components_snapshot["pump"]
    x, y, w, h = pump["x"], pump["y"], pump["width"], pump["height"]

    for px in range(x - 20, x + w + 20, 10):
        for py in range(y + h, y + h + 40, 10):
            drawn_cells.add((px, py))

    for px in range(x - 20, x + w + 20, 10):
        for py in range(y - 30, y, 10):
            drawn_cells.add((px, py))

    for px in range(x + w, x + w + 90, 10):
        for py in range(int(y + h / 2 - 20), int(y + h / 2 + 20), 10):
            drawn_cells.add((px, py))

    view_w, view_h = 1000, 600
    placer = LabelPlacer(mock_components_snapshot, drawn_cells, view_w, view_h)
    result = placer.compute()

    test_log.check("Надпись насоса (bottom+top+right заняты)", result["pump"], "left")
