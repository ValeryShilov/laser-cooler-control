import pytest
from services.label_placer import LabelPlacer

def test_label_placer_basic(mock_components_snapshot):
    # Пустой сет труб
    drawn_cells = set()
    view_w, view_h = 1000, 600
    
    placer = LabelPlacer(mock_components_snapshot, drawn_cells, view_w, view_h)
    result = placer.compute()
    
    # По умолчанию предпочтение отдается "bottom" (если нет препятствий)
    assert result["tank"] == "bottom"
    assert result["pump"] == "bottom"
    
    # Внешние порты пропускаются
    assert "port_in" not in result

def test_label_placer_avoid_pipes(mock_components_snapshot):
    # Имитируем, что под насосом проходит труба
    drawn_cells = set()
    pump = mock_components_snapshot["pump"]
    x, y, w, h = pump["x"], pump["y"], pump["width"], pump["height"]
    
    # Забиваем клетками область под насосом (bottom)
    for px in range(x - 20, x + w + 20, 10):
        for py in range(y + h, y + h + 40, 10):
            drawn_cells.add((px, py))
            
    view_w, view_h = 1000, 600
    placer = LabelPlacer(mock_components_snapshot, drawn_cells, view_w, view_h)
    result = placer.compute()
    
    # Поскольку bottom занят, алгоритм должен выбрать следующую предпочтительную позицию (top)
    assert result["pump"] == "top"

def test_label_placer_avoid_pipes_right(mock_components_snapshot):
    # Имитируем, что под насосом и над ним проходят трубы
    drawn_cells = set()
    pump = mock_components_snapshot["pump"]
    x, y, w, h = pump["x"], pump["y"], pump["width"], pump["height"]
    
    # Забиваем bottom
    for px in range(x - 20, x + w + 20, 10):
        for py in range(y + h, y + h + 40, 10):
            drawn_cells.add((px, py))
            
    # Забиваем top
    for px in range(x - 20, x + w + 20, 10):
        for py in range(y - 30, y, 10):
            drawn_cells.add((px, py))
            
    view_w, view_h = 1000, 600
    placer = LabelPlacer(mock_components_snapshot, drawn_cells, view_w, view_h)
    result = placer.compute()
    
    # Поскольку bottom и top заняты, алгоритм должен выбрать right
    assert result["pump"] == "right"

def test_label_placer_avoid_pipes_left(mock_components_snapshot):
    # Имитируем, что bottom, top и right заняты трубами
    drawn_cells = set()
    pump = mock_components_snapshot["pump"]
    x, y, w, h = pump["x"], pump["y"], pump["width"], pump["height"]
    
    # Забиваем bottom
    for px in range(x - 20, x + w + 20, 10):
        for py in range(y + h, y + h + 40, 10):
            drawn_cells.add((px, py))
            
    # Забиваем top
    for px in range(x - 20, x + w + 20, 10):
        for py in range(y - 30, y, 10):
            drawn_cells.add((px, py))
            
    # Забиваем right
    for px in range(x + w, x + w + 90, 10):
        for py in range(int(y + h / 2 - 20), int(y + h / 2 + 20), 10):
            drawn_cells.add((px, py))
            
    view_w, view_h = 1000, 600
    placer = LabelPlacer(mock_components_snapshot, drawn_cells, view_w, view_h)
    result = placer.compute()
    
    # Поскольку bottom, top и right заняты, алгоритм должен выбрать left
    assert result["pump"] == "left"
