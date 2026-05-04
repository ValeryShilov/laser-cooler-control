from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
from PySide6.QtCore import Qt, QRectF

from parser import SchemeParser
from layout import TopologyLayoutEngine
from router import AStarRouter

class ChillerMnemonic(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(500)
        
        # 1. Читаем YAML
        self.parser = SchemeParser("scheme.yaml")
        self.components, self.connections = self.parser.parse()
        
        # 2. Инициализируем движок компоновки
        self.layout_engine = TopologyLayoutEngine(padding=80)
        self.layout_engine.layout(self.components, self.connections)
        
        self.is_running = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.layout_engine.width = self.width()
        self.layout_engine.height = self.height()
        self.layout_engine.layout(self.components, self.connections)
        self.update()

    def set_states(self, running, heater, solenoid):
        self.is_running = running
        state_str = "on" if running else "off"
        
        for cid, comp in self.components.items():
            if "heater" in cid:
                comp.set_state("on" if heater else "off")
            elif "valve" in cid:
                comp.set_state("on" if solenoid else "off")
            else:
                comp.set_state(state_str)
        self.update()

    def get_pen_by_type(self, conn_type):
        idle_c = QColor(180, 180, 180)
        colors = {
            "freon": QColor(0, 188, 212),       
            "freon_bypass": QColor(0, 188, 212),
            "water_lt": QColor(33, 150, 243),    
            "water_ht": QColor(255, 152, 0),     
            "drain": QColor(150, 150, 150)       
        }
        
        color = colors.get(conn_type, idle_c) if self.is_running else idle_c
        width = 4 if "water" in conn_type else 3
        style = Qt.DashLine if conn_type == "drain" else Qt.SolidLine
        
        return QPen(color, width, style, Qt.RoundCap, Qt.RoundJoin)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor(245, 247, 250))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 6, 6)

        from router import AStarRouter

        router = AStarRouter(width=self.width(), height=self.height(), grid_size=10)

        for comp in self.components.values():
            if "ext_" not in comp.id:
                router.add_obstacle(comp.x, comp.y, comp.width, comp.height, padding=10)

        def get_escape_point(obj, port_pos, is_external=False):
            """
            Определяет направление «убегания» трубы от порта.
            Оба точки (exact и safe) привязаны к сетке для ортогональности.
            """
            gs = 10
            grid_px = round(port_pos[0] / gs) * gs
            grid_py = round(port_pos[1] / gs) * gs
            exact = (grid_px, grid_py)

            safe_dist = 30
            if is_external:
                return exact, (grid_px - safe_dist, grid_py)

            dist_left   = abs(port_pos[0] - obj.x)
            dist_right  = abs(port_pos[0] - (obj.x + obj.width))
            dist_top    = abs(port_pos[1] - obj.y)
            dist_bottom = abs(port_pos[1] - (obj.y + obj.height))

            min_dist = min(dist_left, dist_right, dist_top, dist_bottom)

            if min_dist == dist_left:
                return exact, (grid_px - safe_dist, grid_py)
            elif min_dist == dist_right:
                return exact, (grid_px + safe_dist, grid_py)
            elif min_dist == dist_top:
                return exact, (grid_px, grid_py - safe_dist)
            else:
                return exact, (grid_px, grid_py + safe_dist)

        # Приоритет маршрутизации: сначала простые трубы, потом сложные
        type_priority = {
            'freon': 0,
            'freon_bypass': 1,
            'water_lt': 2,
            'water_ht': 3,
            'drain': 4,
            'mechanical': 99,
        }
        sorted_connections = sorted(
            self.connections,
            key=lambda c: type_priority.get(c['type'], 5)
        )

        for conn in sorted_connections:
            if conn['type'] == "mechanical": continue

            src_obj = self.components.get(conn['source_id'])
            tgt_obj = self.components.get(conn['target_id'])
            if not src_obj or not tgt_obj: continue

            src_port_name = conn.get('source_port', 'out')
            tgt_port_name = conn.get('target_port', 'in')

            start_pos = src_obj.ports.get(src_port_name, (src_obj.x, src_obj.y))
            end_pos = tgt_obj.ports.get(tgt_port_name, (tgt_obj.x, tgt_obj.y))

            exact_start, safe_start = get_escape_point(src_obj, start_pos, "port_" in src_obj.id)
            exact_end, safe_end = get_escape_point(tgt_obj, end_pos, "port_" in tgt_obj.id)

            path_pts = router.find_path(exact_start, exact_end, safe_start, safe_end, waypoints=[])

            if path_pts:
                path = QPainterPath()
                path.moveTo(path_pts[0][0], path_pts[0][1])
                for pt in path_pts[1:]:
                    path.lineTo(pt[0], pt[1])

                painter.setPen(self.get_pen_by_type(conn['type']))
                painter.drawPath(path)

        # === АЛГОРИТМ УМНОГО РАЗМЕЩЕНИЯ НАДПИСЕЙ ===
        occupied_rects = []
        
        # 1. Заносим в занятые зоны габариты самих компонентов (без текстов)
        for comp in self.components.values():
            occupied_rects.append(comp.get_rect())

        for comp in self.components.values():
            # Внешние порты пропускаем, у них стрелки и текст отрисовываются по жестким правилам
            if type(comp).__name__ == "ExternalPort":
                continue

            # 2. Зоны проверки совпадают с отрисовкой в equipment.py
            areas = {
                "bottom": QRectF(comp.x - 20, comp.y + comp.height + 2, comp.width + 40, 30),
                "top": QRectF(comp.x - 20, comp.y - 28, comp.width + 40, 26),
                "left": QRectF(comp.x - 85, comp.y + comp.height / 2 - 15, 80, 30),
                "right": QRectF(comp.x + comp.width + 3, comp.y + comp.height / 2 - 15, 80, 30)
            }
            
            best_pos = "bottom"
            min_score = float('inf')
            best_rect = areas["bottom"]
            
            for pos, rect in areas.items():
                score = 0
                
                # Штраф за наложение на оборудование ИЛИ ДРУГИЕ НАДПИСИ
                for occ_rect in occupied_rects:
                    # Разрешаем тексту пересекать "самого себя" (свой же компонент),
                    # иначе текст будет убегать от своего же насоса или бака.
                    if occ_rect == comp.get_rect():
                        continue
                        
                    if rect.intersects(occ_rect):
                        score += 500  # Критический штраф за пересечение с графикой/чужим текстом
                
                # Штраф за наложение на трубы
                for cell in router.drawn_cells:
                    if rect.contains(cell[0], cell[1]):
                        score += 50  # Средний штраф (лучше лечь на трубу, чем на чужой насос)
                        
                # Штраф за выход за края экрана (чтобы текст не обрезался)
                if rect.left() < 0 or rect.right() > self.width() or rect.top() < 0 or rect.bottom() > self.height():
                    score += 1000
                    
                # Приоритет позиций (если все чисто, предпочитаем снизу)
                preference = {"bottom": 0, "top": 1, "right": 2, "left": 3}
                score += preference[pos]
                
                if score < min_score:
                    min_score = score
                    best_pos = pos
                    best_rect = rect
                    
            comp.label_pos = best_pos
            
            # 3. КЛЮЧЕВОЙ МОМЕНТ: Добавляем выбранное место текста в занятые зоны!
            # Теперь следующая надпись будет знать, что здесь уже занято.
            occupied_rects.append(best_rect)
        # ===========================================        

        for comp in self.components.values():
            comp.draw(painter)

        painter.end()