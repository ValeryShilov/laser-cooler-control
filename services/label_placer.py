"""
Алгоритм автоматического размещения надписей компонентов.

Проверяет 4 слота (bottom/top/left/right) для каждого компонента
и выбирает лучший по scoring-системе: минимум пересечений с трубами,
компонентами и краями экрана.
"""
from PySide6.QtCore import QRectF


class LabelPlacer:
    """Вычисляет оптимальные позиции надписей для компонентов схемы."""

    def __init__(self, comp_snapshot, drawn_cells, view_width, view_height):
        """
        Args:
            comp_snapshot: dict {comp_id: {x, y, width, height, class_name, ...}}
            drawn_cells: set of (x, y) — клетки, занятые трубами
            view_width: ширина области отрисовки
            view_height: высота области отрисовки
        """
        self._comps = comp_snapshot
        self._drawn_cells = drawn_cells
        self._view_w = view_width
        self._view_h = view_height

    def compute(self) -> dict:
        """Возвращает {comp_id: 'bottom'|'top'|'left'|'right'}."""
        occupied_rects = []

        # 1. Заносим в занятые зоны габариты самих компонентов
        for cid, data in self._comps.items():
            occupied_rects.append(QRectF(data['x'], data['y'], data['width'], data['height']))

        result = {}

        for cid, data in self._comps.items():
            # Внешние порты — пропускаем (у них жёсткая отрисовка)
            if data['class_name'] == 'ExternalPort':
                continue

            x, y, w, h = data['x'], data['y'], data['width'], data['height']
            comp_rect = QRectF(x, y, w, h)

            # 2. Зоны для каждого из 4-х слотов
            areas = {
                "bottom": QRectF(x - 20, y + h + 2, w + 40, 30),
                "top":    QRectF(x - 20, y - 28, w + 40, 26),
                "left":   QRectF(x - 85, y + h / 2 - 15, 80, 30),
                "right":  QRectF(x + w + 3, y + h / 2 - 15, 80, 30),
            }

            best_pos = "bottom"
            min_score = float('inf')
            best_rect = areas["bottom"]

            for pos, rect in areas.items():
                score = 0

                # Штраф за наложение на оборудование или другие надписи
                for occ_rect in occupied_rects:
                    if occ_rect == comp_rect:
                        continue  # Пропускаем свой же компонент
                    if rect.intersects(occ_rect):
                        score += 500

                # Штраф за наложение на трубы
                for cell in self._drawn_cells:
                    if rect.contains(cell[0], cell[1]):
                        score += 50

                # Штраф за выход за края экрана
                if (rect.left() < 0 or rect.right() > self._view_w or
                        rect.top() < 0 or rect.bottom() > self._view_h):
                    score += 1000

                # Приоритет позиций (эстетика)
                preference = {"bottom": 0, "top": 1, "right": 2, "left": 3}
                score += preference[pos]

                if score < min_score:
                    min_score = score
                    best_pos = pos
                    best_rect = rect

            result[cid] = best_pos

            # 3. Добавляем выбранное место в занятые зоны
            occupied_rects.append(best_rect)

        return result
