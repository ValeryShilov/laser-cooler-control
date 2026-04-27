from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
from PySide6.QtCore import Qt

from parser import SchemeParser
from layout import RuleBasedLayoutEngine
from router import AStarRouter
from rules import ROUTING_RULES

class ChillerMnemonic(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(500)
        
        # 1. Читаем YAML
        self.parser = SchemeParser("scheme.yaml")
        self.components, self.connections = self.parser.parse()
        
        # 2. Инициализируем движок компоновки
        self.layout_engine = RuleBasedLayoutEngine(padding=80)
        self.layout_engine.layout(self.components)
        
        self.is_running = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.layout_engine.width = self.width()
        self.layout_engine.height = self.height()
        self.layout_engine.layout(self.components)
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
        from rules import ROUTING_RULES

        router = AStarRouter(width=self.width(), height=self.height(), grid_size=10)

        for comp in self.components.values():
            if "ext_" not in comp.id: 
                router.add_obstacle(comp.x, comp.y, comp.width, comp.height, padding=10)

        def get_escape_point(obj, port_pos, is_external=False):
            # Жестко округляем сам порт до сетки (убивает "крючки")
            grid_px = round(port_pos[0] / 10) * 10
            grid_py = round(port_pos[1] / 10) * 10
            
            safe_dist = 30
            if is_external:
                return (grid_px, grid_py), (grid_px - safe_dist, grid_py)
            
            cx = obj.x + obj.width / 2
            cy = obj.y + obj.height / 2
            dx = port_pos[0] - cx
            dy = port_pos[1] - cy
            
            if abs(dx) >= abs(dy):
                safe_x = grid_px + (safe_dist if dx >= 0 else -safe_dist)
                return (grid_px, grid_py), (safe_x, grid_py)
            else:
                safe_y = grid_py + (safe_dist if dy >= 0 else -safe_dist)
                return (grid_px, grid_py), (grid_px, safe_y)

        # Сортируем соединения, чтобы сначала рисовались простые, а потом сложные
        # Это помогает алгоритму памяти труб работать эффективнее
        sorted_connections = sorted(self.connections, key=lambda c: 0 if "freon" in c['type'] else 1)

        for conn in sorted_connections:
            if conn['type'] == "mechanical": continue 
            
            src_obj = self.components.get(conn['source_id'])
            tgt_obj = self.components.get(conn['target_id'])
            if not src_obj or not tgt_obj: continue
            
            src_port_name = conn.get('source_port', 'out')
            tgt_port_name = conn.get('target_port', 'in')
                
            start_pos = src_obj.ports.get(src_port_name, (src_obj.x, src_obj.y))
            end_pos = tgt_obj.ports.get(tgt_port_name, (tgt_obj.x, tgt_obj.y))
            
            # Получаем ИДЕАЛЬНО выровненные точки
            exact_start, safe_start = get_escape_point(src_obj, start_pos, "ext_" in src_obj.id)
            exact_end, safe_end = get_escape_point(tgt_obj, end_pos, "ext_" in tgt_obj.id)

            rule_key = (f"{conn['source_id']}.{src_port_name}", f"{conn['target_id']}.{tgt_port_name}")
            waypoints_pct = ROUTING_RULES.get(rule_key, [])
            
            waypoints_px = []
            safe_w = self.width() - 2 * self.layout_engine.padding
            safe_h = self.height() - 2 * self.layout_engine.padding
            for wp_x_pct, wp_y_pct in waypoints_pct:
                px_x = self.layout_engine.padding + (safe_w * wp_x_pct)
                px_y = self.layout_engine.padding + (safe_h * wp_y_pct)
                waypoints_px.append((px_x, px_y))

            path_pts = router.find_path(exact_start, exact_end, safe_start, safe_end, waypoints=waypoints_px)
            
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