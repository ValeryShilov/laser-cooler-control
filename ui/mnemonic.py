"""
Виджет мнемосхемы чиллера.

Ответственность: ТОЛЬКО отрисовка. Все вычисления (A*, лейблы)
выполняются в фоновом потоке SchemeWorker, результаты кэшируются.
paintEvent рисует из кэша — ноль вычислений в UI-потоке.
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
from PySide6.QtCore import Qt, QTimer

from services.parser import SchemeParser
from services.layout import TopologyLayoutEngine
from services.worker import SchemeWorker, compute_routes_and_labels, make_comp_snapshot
from core.models import RenderData


class ChillerMnemonic(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(500)

        # 1. Читаем YAML
        #self.parser = SchemeParser(r"tests\test_data\schemes\pos_extreme_density.yaml")
        self.parser = SchemeParser("scheme.yaml")
        self.components, self.connections = self.parser.parse()

        # 2. Инициализируем движок компоновки
        self.layout_engine = TopologyLayoutEngine(padding=50)
        self.layout_engine.pad_top = 80  # Увеличен для видимости верхних надписей
        self.layout_engine.layout(self.components, self.connections)

        self.is_running = False

        # 3. Кэш результатов фоновых вычислений
        self._render_data = None
        self._render_generation = 0
        self._worker = None
        
        # Режим отладки (включается по Ctrl+D)
        self._show_debug_grid = False

        # 4. Debounce-таймер для resize (150мс)
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(150)
        self._resize_timer.timeout.connect(self._on_resize_done)

        # 5. Первый расчёт — синхронный для мгновенного отображения
        self._compute_sync()

    #  Управление состояниями (вызывается из interface/main_window)

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
        self.update()  # Перерисовка без перерасчёта труб (меняются только цвета)

    def toggle_debug(self):
        """Переключает отображение отладочной сетки и зон коллизий."""
        self._show_debug_grid = not self._show_debug_grid
        self.update()

    #  Resize → debounce → фоновый пересчёт

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Layout — синхронный (быстрый, только пересчёт координат)
        self.layout_engine.width = self.width()
        self.layout_engine.height = self.height()
        self.layout_engine.layout(self.components, self.connections)
        # Запускаем debounce-таймер для маршрутизации
        self._resize_timer.start()

    def _on_resize_done(self):
        """Resize закончился — запускаем фоновый расчёт маршрутов."""
        self._request_recompute()

    #  Фоновые вычисления
    def _compute_sync(self):
        """Синхронный расчёт (первый запуск — для мгновенного отображения)."""
        snapshot = make_comp_snapshot(self.components)
        self._render_data = compute_routes_and_labels(
            snapshot, self.connections, self.width() or 1000, self.height() or 600
        )
        self._apply_labels()

    def _request_recompute(self):
        """Запуск фонового потока для пересчёта маршрутов."""
        self._render_generation += 1
        gen = self._render_generation

        snapshot = make_comp_snapshot(self.components)

        # Останавливаем предыдущий worker если он ещё работает
        if self._worker is not None and self._worker.isRunning():
            self._worker.disconnect()
            # Не ждём завершения — он просто доработает и ничего не сделает

        self._worker = SchemeWorker(
            snapshot, self.connections,
            self.width(), self.height(), gen
        )
        self._worker.render_ready.connect(self._on_render_ready)
        self._worker.start()

    def _on_render_ready(self, render_data, generation):
        """Слот: данные готовы из фонового потока."""
        if generation != self._render_generation:
            return  # Устаревший результат — игнорируем
        self._render_data = render_data
        self._apply_labels()
        self.update()

    def _apply_labels(self):
        """Применяет вычисленные позиции надписей к компонентам."""
        if not self._render_data:
            return
        for comp_id, pos in self._render_data.label_positions.items():
            if comp_id in self.components:
                self.components[comp_id].label_pos = pos

    def get_pen_by_type(self, conn_type):
        idle_c = QColor(180, 180, 180)
        colors = {
            "freon": QColor(0, 188, 212),
            "freon_bypass": QColor(0, 188, 212),
            "water_lt": QColor(33, 150, 243),
            "water_ht": QColor(255, 152, 0),
            "drain": QColor(150, 150, 150),
        }

        color = colors.get(conn_type, idle_c) if self.is_running else idle_c
        width = 4 if "water" in conn_type else 3
        style = Qt.DashLine if conn_type == "drain" else Qt.SolidLine

        return QPen(color, width, style, Qt.RoundCap, Qt.RoundJoin)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Фон
        painter.fillRect(self.rect(), QColor(245, 247, 250))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 6, 6)
        
        # 1. Отладочная сетка (Grid)
        if self._show_debug_grid:
            painter.setPen(QPen(QColor(0, 0, 0, 15), 1, Qt.DotLine))
            # Шаг 10 пикселей (AStarRouter.grid_size)
            for x in range(0, self.width(), 10):
                painter.drawLine(x, 0, x, self.height())
            for y in range(0, self.height(), 10):
                painter.drawLine(0, y, self.width(), y)

        if self._render_data:
            for path_pts, pipe_type in self._render_data.pipe_paths:
                path = QPainterPath()
                path.moveTo(path_pts[0][0], path_pts[0][1])
                for pt in path_pts[1:]:
                    path.lineTo(pt[0], pt[1])
                painter.setPen(self.get_pen_by_type(pipe_type))
                painter.drawPath(path)

        for comp in self.components.values():
            comp.draw(painter)

        # 2. Отладочные зоны поверх всего
        if self._show_debug_grid:
            # А) Зоны коллизий A* (препятствия) - Красные
            if self._render_data and hasattr(self._render_data, 'obstacles'):
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(255, 0, 0, 30))
                for (ox1, oy1, ox2, oy2) in self._render_data.obstacles:
                    painter.drawRect(ox1, oy1, ox2 - ox1, oy2 - oy1)
            
            # Б) Зоны Layout Engine (padding 35px) - Синий пунктир
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(0, 0, 255, 100), 1, Qt.DashLine))
            for comp in self.components.values():
                painter.drawRect(comp.x - 35, comp.y - 35, comp.width + 70, comp.height + 70)
                
            # В) Истинный Rendering Bounding Box объектов - Зеленый
            painter.setPen(QPen(QColor(0, 255, 0, 200), 1, Qt.SolidLine))
            for comp in self.components.values():
                painter.drawRect(comp.x, comp.y, comp.width, comp.height)

        painter.end()
