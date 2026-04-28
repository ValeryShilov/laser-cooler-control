from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
from PySide6.QtCore import Qt

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
            Логика: порт привязан к РЕБРУ компонента — escape идёт
            перпендикулярно этому ребру наружу.
            """
            grid_px = round(port_pos[0] / 10) * 10
            grid_py = round(port_pos[1] / 10) * 10

            safe_dist = 30
            if is_external:
                return (grid_px, grid_py), (grid_px - safe_dist, grid_py)

            # Определяем, к какому ребру ближе всего порт
            dist_left   = abs(port_pos[0] - obj.x)
            dist_right  = abs(port_pos[0] - (obj.x + obj.width))
            dist_top    = abs(port_pos[1] - obj.y)
            dist_bottom = abs(port_pos[1] - (obj.y + obj.height))

            min_dist = min(dist_left, dist_right, dist_top, dist_bottom)

            if min_dist == dist_left:
                return (grid_px, grid_py), (grid_px - safe_dist, grid_py)
            elif min_dist == dist_right:
                return (grid_px, grid_py), (grid_px + safe_dist, grid_py)
            elif min_dist == dist_top:
                return (grid_px, grid_py), (grid_px, grid_py - safe_dist)
            else:
                return (grid_px, grid_py), (grid_px, grid_py + safe_dist)

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

            exact_start, safe_start = get_escape_point(src_obj, start_pos, "ext_" in src_obj.id)
            exact_end, safe_end = get_escape_point(tgt_obj, end_pos, "ext_" in tgt_obj.id)

            path_pts = router.find_path(exact_start, exact_end, safe_start, safe_end, waypoints=[])

            if path_pts:
                path = QPainterPath()
                path.moveTo(path_pts[0][0], path_pts[0][1])
                for pt in path_pts[1:]:
                    path.lineTo(pt[0], pt[1])

                painter.setPen(self.get_pen_by_type(conn['type']))
                painter.drawPath(path)

        for comp in self.components.values():
            comp.draw(painter)

        painter.end()