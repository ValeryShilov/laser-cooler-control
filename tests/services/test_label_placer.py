import json
import os
from services.label_placer import LabelPlacer
from PySide6.QtCore import QRectF

GOLDEN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "reports", "golden")



def test_label_placer_init_occupied_zones(test_log):
    snapshot = {
        "a": {"x": 10, "y": 20, "width": 100, "height": 50, "class_name": "Tank"},
        "b": {"x": 200, "y": 20, "width": 80, "height": 40, "class_name": "Pump"},
    }
    placer = LabelPlacer(snapshot, set(), 1000, 600)
    zones = placer._init_occupied_zones()

    test_log.check("Количество зон", len(zones), 2)
    test_log.check("Тип элемента", type(zones[0]).__name__, "QRectF")


def test_label_placer_build_candidate_areas(test_log):
    snapshot = {
        "a": {"x": 100, "y": 100, "width": 80, "height": 60, "class_name": "Tank"},
    }
    placer = LabelPlacer(snapshot, set(), 1000, 600)
    areas = placer._build_candidate_areas(snapshot["a"])

    test_log.check("Количество слотов", len(areas), 4)
    test_log.check("Наличие bottom", "bottom" in areas, True, op="is")
    test_log.check("Наличие top", "top" in areas, True, op="is")
    test_log.check("Наличие left", "left" in areas, True, op="is")
    test_log.check("Наличие right", "right" in areas, True, op="is")

    # bottom должен быть ниже компонента
    test_log.check("bottom.top > comp.bottom",
                   areas["bottom"].top(), 100 + 60 + 2, op="approx", abs=1)


def test_label_placer_score_slot_empty(test_log):
    snapshot = {
        "a": {"x": 100, "y": 100, "width": 80, "height": 60, "class_name": "Tank"},
    }
    placer = LabelPlacer(snapshot, set(), 1000, 600)
    areas = placer._build_candidate_areas(snapshot["a"])
    comp_rect = QRectF(100, 100, 80, 60)
    occupied = [comp_rect]

    score_bottom = placer._score_slot(areas["bottom"], comp_rect, occupied, "bottom")
    score_top = placer._score_slot(areas["top"], comp_rect, occupied, "top")

    test_log.check("bottom score (пустое поле)", score_bottom, 0)
    test_log.check("top score (пустое поле)", score_top, 1)  # preference = 1


def test_label_placer_score_slot_with_pipes(test_log):
    snapshot = {
        "a": {"x": 100, "y": 100, "width": 80, "height": 60, "class_name": "Tank"},
    }
    # Заполняем зону bottom трубами
    drawn_cells = set()
    for px in range(80, 220, 10):
        for py in range(162, 192, 10):
            drawn_cells.add((px, py))

    placer = LabelPlacer(snapshot, drawn_cells, 1000, 600)
    areas = placer._build_candidate_areas(snapshot["a"])
    comp_rect = QRectF(100, 100, 80, 60)
    occupied = [comp_rect]

    score_bottom = placer._score_slot(areas["bottom"], comp_rect, occupied, "bottom")
    score_top = placer._score_slot(areas["top"], comp_rect, occupied, "top")

    test_log.check("bottom score > top score (трубы внизу)",
                   score_bottom, score_top, op="gt")


def test_label_placer_select_best_slot(test_log):
    snapshot = {
        "a": {"x": 100, "y": 100, "width": 80, "height": 60, "class_name": "Tank"},
    }
    placer = LabelPlacer(snapshot, set(), 1000, 600)
    occupied = [QRectF(100, 100, 80, 60)]

    best_pos, best_rect, scores = placer._select_best_slot(snapshot["a"], occupied)

    test_log.check("Лучший слот (пустое поле)", best_pos, "bottom")
    test_log.check("Scores содержит 4 слота", len(scores), 4)
    test_log.check("bottom score минимален", scores["bottom"], min(scores.values()))


# ══════════════════════════════════════
#  Существующие тесты (без изменений)
# ══════════════════════════════════════

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


# ══════════════════════════════════════
#  Интеграционный тест с журналом
# ══════════════════════════════════════

def test_label_placer_journal(mock_components_snapshot, test_log):
    placer = LabelPlacer(mock_components_snapshot, set(), 1000, 600)
    result, journal = placer.compute(return_journal=True)

    # Структура журнала
    test_log.check("Журнал не пустой", len(journal), 0, op="gt")

    # Первая запись — init_zones
    init_entry = journal[0]
    test_log.check("Первый шаг", init_entry["step"], "init_zones")
    test_log.check("init_zones.input.comp_count", init_entry["input"]["comp_count"], 3)
    test_log.check("init_zones.output.occupied_rects_count",
                   init_entry["output"]["occupied_rects_count"], 3)

    # Записи select_slot (только tank и pump, port_in — ExternalPort)
    slot_entries = [e for e in journal if e["step"] == "select_slot"]
    test_log.check("Количество select_slot записей", len(slot_entries), 2)

    # Проверяем структуру записи
    tank_entry = [e for e in slot_entries if e["context"]["comp_id"] == "tank"][0]
    test_log.check("tank entry имеет scores", "scores" in tank_entry["output"], True, op="is")
    test_log.check("tank scores имеет 4 слота", len(tank_entry["output"]["scores"]), 4)
    test_log.check("tank decision.chosen", tank_entry["decision"]["chosen"], result["tank"])

    # Проверяем что выбранный слот действительно имеет минимальный score
    scores = tank_entry["output"]["scores"]
    chosen = tank_entry["decision"]["chosen"]
    min_score = min(scores.values())
    test_log.check("Выбранный слот = минимальный score", scores[chosen], min_score)

    # Результат совпадает с обычным вызовом
    result_normal = placer.compute()
    test_log.check("Результат с журналом = результат без", result, result_normal)


# ══════════════════════════════════════
#  Регрессионный тест (эталон)
# ══════════════════════════════════════

def test_label_placer_regression(mock_components_snapshot, test_log):
    placer = LabelPlacer(mock_components_snapshot, set(), 1000, 600)
    result, journal = placer.compute(return_journal=True)

    golden_path = os.path.join(GOLDEN_DIR, "label_placer.json")

    if not os.path.exists(golden_path):
        # Первый запуск — сохраняем эталон
        os.makedirs(GOLDEN_DIR, exist_ok=True)
        with open(golden_path, "w", encoding="utf-8") as f:
            json.dump({"result": result, "journal": journal}, f,
                      ensure_ascii=False, indent=2)
        test_log.check("Эталон создан", True, True, op="is")
        return

    with open(golden_path, "r", encoding="utf-8") as f:
        golden = json.load(f)

    test_log.check("Результат совпадает с эталоном", result, golden["result"])
    test_log.check("Количество записей журнала",
                   len(journal), len(golden["journal"]))

    for i, (entry, golden_entry) in enumerate(zip(journal, golden["journal"])):
        test_log.check(f"Шаг [{i}] совпадает", entry["step"], golden_entry["step"])
        if entry["step"] == "select_slot":
            test_log.check(
                f"Решение [{i}] совпадает",
                entry["decision"]["chosen"], golden_entry["decision"]["chosen"])
