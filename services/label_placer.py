"""
Алгоритм автоматического размещения надписей компонентов.

Проверяет 4 слота (bottom/top/left/right) для каждого компонента
и выбирает лучший по scoring-системе: минимум пересечений с трубами,
компонентами и краями экрана.
"""
import logging
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QFontMetrics

logger = logging.getLogger(__name__)

class LabelPlacer:
    """Вычисляет оптимальные позиции надписей для компонентов схемы."""

    def __init__(self, comp_snapshot, drawn_cells, view_width, view_height):
        self._comps = comp_snapshot
        self._drawn_cells = drawn_cells
        self._view_w = view_width
        self._view_h = view_height
        
        # Для точного расчета габаритов текста
        self._font = QFont("Arial", 10, QFont.Bold)
        # Поскольку QGuiApplication обычно запущен в main.py, QFontMetrics доступен
        self._metrics = QFontMetrics(self._font)

    def compute(self):
        """Оркестратор: возвращает словарь с информацией о позиции и габаритах надписи."""
        occupied_rects = self._init_occupied_zones()

        logger.debug("Step: init_zones", extra={"journal_entry": {
            "step": "init_zones",
            "context": {},
            "input": {"comp_count": len(self._comps)},
            "output": {"occupied_rects_count": len(occupied_rects)},
            "decision": None,
        }})

        result = {}
        for cid, data in self._comps.items():
            if data['class_name'] == 'ExternalPort':
                continue

            best_cand, best_rect, min_score = self._select_best_slot(data, occupied_rects)
            
            # Сохраняем относительное смещение, чтобы текст двигался вместе с компонентом
            result[cid] = {
                "dx": best_cand['text_rect'].x() - data['x'],
                "dy": best_cand['text_rect'].y() - data['y'],
                "w": best_cand['text_rect'].width(),
                "h": best_cand['text_rect'].height(),
                "max_w": best_cand["max_w"],
                "align": best_cand["align"]
            }
            occupied_rects.append(best_rect)

            logger.debug("Step: select_slot", extra={"journal_entry": {
                "step": "select_slot",
                "context": {"comp_id": cid},
                "input": {"x": data['x'], "y": data['y'],
                          "w": data['width'], "h": data['height']},
                "output": {"best_cand_id": best_cand["id"]},
                "decision": {"min_score": min_score},
            }})

        return result

    def _init_occupied_zones(self):
        """Инициализирует занятые зоны габаритами самих компонентов."""
        occupied = []
        for cid, data in self._comps.items():
            occupied.append(QRectF(data['x'], data['y'], data['width'], data['height']))
        return occupied

    def _build_candidate_areas(self, data):
        """Генерирует до 24 кандидатов для размещения надписи."""
        x, y, w, h = data['x'], data['y'], data['width'], data['height']
        name = data.get('name', 'Unknown')
        
        widths = [
            ("wide", max(110, w + 40), 0),   # Однострочный (без штрафа)
            ("narrow", 90, 10)               # Многострочный (штраф 10)
        ]
        
        # (pos_name, anchor_x, anchor_y, growth_dir, align, pos_penalty)
        positions = [
            # BOTTOM (ty = ay)
            ('bottom_center', x + w/2, y + h + 5, 'center_top', Qt.AlignCenter, 0),
            ('bottom_left',   x,       y + h + 5, 'left_top',   Qt.AlignLeft,   2),
            ('bottom_right',  x + w,   y + h + 5, 'right_top',  Qt.AlignRight,  2),
            
            # TOP (ty = ay - th)
            ('top_center',    x + w/2, y - 5,     'center_bottom', Qt.AlignCenter, 1),
            ('top_left',      x,       y - 5,     'left_bottom',   Qt.AlignLeft,   3),
            ('top_right',     x + w,   y - 5,     'right_bottom',  Qt.AlignRight,  3),
            
            # LEFT (tx = ax - tw)
            ('left_center',   x - 5,   y + h/2,   'right_center', Qt.AlignRight, 4),
            ('left_top',      x - 5,   y,         'right_top',    Qt.AlignRight, 5),
            ('left_bottom',   x - 5,   y + h,     'right_bottom', Qt.AlignRight, 5),
            
            # RIGHT (tx = ax)
            ('right_center',  x + w + 5, y + h/2, 'left_center',  Qt.AlignLeft,  2),
            ('right_top',     x + w + 5, y,       'left_top',     Qt.AlignLeft,  4),
            ('right_bottom',  x + w + 5, y + h,   'left_bottom',  Qt.AlignLeft,  4),
        ]
        
        candidates = []
        for pos_name, ax, ay, growth, align, pos_penalty in positions:
            for w_name, max_w, w_penalty in widths:
                br = self._metrics.boundingRect(0, 0, int(max_w), 1000, align | Qt.TextWordWrap, name)
                tw, th = br.width(), br.height()
                
                # Вычисление X
                if 'center' in growth.split('_')[0]: tx = ax - tw/2
                elif 'left' in growth.split('_')[0]: tx = ax
                else: tx = ax - tw # right
                
                # Вычисление Y
                if 'center' in growth.split('_')[1]: ty = ay - th/2
                elif 'top' in growth.split('_')[1]: ty = ay
                else: ty = ay - th # bottom
                
                rect = QRectF(tx, ty, tw, th)
                padded_rect = rect.adjusted(-2, -2, 2, 2)
                
                candidates.append({
                    "id": f"{pos_name}_{w_name}",
                    "rect": padded_rect,
                    "text_rect": rect,
                    "align": align | Qt.TextWordWrap,
                    "max_w": max_w,
                    "penalty": pos_penalty + w_penalty
                })
        return candidates

    def _score_slot(self, cand, comp_rect, occupied_rects):
        """Вычисляет штрафной балл для кандидата."""
        score = cand['penalty']
        rect = cand['rect']
        
        # Штраф за наложение на оборудование или другие надписи
        for occ_rect in occupied_rects:
            if occ_rect == comp_rect:
                continue
            if rect.intersects(occ_rect):
                score += 500
                
        # Штраф за наложение на трубы
        pipe_intersections = 0
        for cell in self._drawn_cells:
            if rect.contains(cell[0], cell[1]):
                pipe_intersections += 1
        score += pipe_intersections * 50
        
        # Выход за края экрана
        if rect.left() < 0 or rect.right() > self._view_w or rect.top() < 0 or rect.bottom() > self._view_h:
            score += 1000
            
        return score

    def _select_best_slot(self, data, occupied_rects):
        """Выбирает лучшего кандидата с минимальным штрафом."""
        x, y, w, h = data['x'], data['y'], data['width'], data['height']
        comp_rect = QRectF(x, y, w, h)
        candidates = self._build_candidate_areas(data)
        
        best_cand = candidates[0]
        min_score = float('inf')
        
        for cand in candidates:
            score = self._score_slot(cand, comp_rect, occupied_rects)
            if score < min_score:
                min_score = score
                best_cand = cand
                
        return best_cand, best_cand['rect'], min_score
