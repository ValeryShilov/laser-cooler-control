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

    def compute(self, return_journal=False):
        """Оркестратор: возвращает {comp_id: 'bottom'|'top'|'left'|'right'}.

        Args:
            return_journal: если True, возвращает (result, journal).
        """
        journal = []
        occupied_rects = self._init_occupied_zones()

        journal.append({
            "step": "init_zones",
            "context": {},
            "input": {"comp_count": len(self._comps)},
            "output": {"occupied_rects_count": len(occupied_rects)},
            "decision": None,
        })

        result = {}
        for cid, data in self._comps.items():
            if data['class_name'] == 'ExternalPort':
                continue

            best_pos, best_rect, scores = self._select_best_slot(data, occupied_rects)
            result[cid] = best_pos
            occupied_rects.append(best_rect)

            journal.append({
                "step": "select_slot",
                "context": {"comp_id": cid},
                "input": {"x": data['x'], "y": data['y'],
                          "w": data['width'], "h": data['height']},
                "output": {"scores": scores},
                "decision": {"chosen": best_pos,
                             "reason": f"min_score={scores[best_pos]}"},
            })

        if return_journal:
            return result, journal
        return result

    def _init_occupied_zones(self):
        """Инициализирует занятые зоны габаритами самих компонентов."""
        occupied = []
        for cid, data in self._comps.items():
            occupied.append(QRectF(data['x'], data['y'], data['width'], data['height']))
        return occupied

    def _build_candidate_areas(self, data):
        """Генерирует 4 прямоугольника-кандидата для размещения надписи."""
        x, y, w, h = data['x'], data['y'], data['width'], data['height']
        return {
            "bottom": QRectF(x - 20, y + h + 2, w + 40, 30),
            "top":    QRectF(x - 20, y - 28, w + 40, 26),
            "left":   QRectF(x - 85, y + h / 2 - 15, 80, 30),
            "right":  QRectF(x + w + 3, y + h / 2 - 15, 80, 30),
        }

    def _score_slot(self, rect, comp_rect, occupied_rects, pos):
        """Вычисляет штрафной балл для одного слота."""
        score = 0

        # Штраф за наложение на оборудование или другие надписи
        for occ_rect in occupied_rects:
            if occ_rect == comp_rect:
                continue
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

        return score

    def _select_best_slot(self, data, occupied_rects):
        """Выбирает лучший слот для надписи из 4 кандидатов.

        Returns:
            (best_pos, best_rect, scores) — scores: dict {pos: int}
        """
        x, y, w, h = data['x'], data['y'], data['width'], data['height']
        comp_rect = QRectF(x, y, w, h)
        areas = self._build_candidate_areas(data)

        scores = {}
        best_pos = "bottom"
        min_score = float('inf')
        best_rect = areas["bottom"]

        for pos, rect in areas.items():
            score = self._score_slot(rect, comp_rect, occupied_rects, pos)
            scores[pos] = score
            if score < min_score:
                min_score = score
                best_pos = pos
                best_rect = rect

        return best_pos, best_rect, scores
