import os
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QPainterPath
from PySide6.QtSvg import QSvgRenderer


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_THIS_DIR)
ICONS_DIR = os.path.join(BASE_DIR, "svg_icons")

class BaseEquipment:
    """ Базовый класс для всего оборудования на схеме """
    def __init__(self, x, y, width, height, name):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.name = name
        
        self.id = "" # Сюда парсер запишет ID из YAML
        self.state = "off" 
        self.renderer = QSvgRenderer()
        self.ports = {}
        self.label_pos = "bottom"  # По умолчанию текст снизу 

    def set_state(self, new_state):
        self.state = new_state
        self.load_svg()

    def load_svg(self):
        pass

    def update_ports(self):
        """ 
        Пересчитывает координаты портов относительно текущих x и y.
        Вызывается движком layout.py ПОСЛЕ расстановки элементов.
        """
        pass

    def get_rect(self):
        return QRectF(self.x, self.y, self.width, self.height)
    
    def draw_label(self, painter: QPainter):
        """ Вынесенная логика отрисовки текста с автовыравниванием """
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        
        # Динамически вычисляем ширину и высоту текста
        metrics = painter.fontMetrics()
        # Даем тексту запас по ширине, чтобы он мог переноситься (например, ширина + 80), 
        # но boundingRect сам вычислит необходимую высоту.
        max_width = max(150, self.width + 80)
        bounding_rect = metrics.boundingRect(0, 0, int(max_width), 1000, Qt.AlignCenter | Qt.TextWordWrap, self.name)
        text_w, text_h = bounding_rect.width(), bounding_rect.height()
        
        align = Qt.AlignCenter | Qt.TextWordWrap
        if self.label_pos == "bottom":
            text_rect = QRectF(self.x + self.width/2 - text_w/2, self.y + self.height + 5, text_w, text_h)
        elif self.label_pos == "top":
            text_rect = QRectF(self.x + self.width/2 - text_w/2, self.y - text_h - 5, text_w, text_h)
        elif self.label_pos == "left":
            text_rect = QRectF(self.x - text_w - 5, self.y + self.height/2 - text_h/2, text_w, text_h)
            align = Qt.AlignRight | Qt.AlignVCenter | Qt.TextWordWrap
        elif self.label_pos == "right":
            text_rect = QRectF(self.x + self.width + 5, self.y + self.height/2 - text_h/2, text_w, text_h)
            align = Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap
            
        painter.drawText(text_rect, align, self.name)

    def draw(self, painter: QPainter):
        """ Стандартная отрисовка: SVG + Текст """
        self.renderer.render(painter, self.get_rect())
        self.draw_label(painter)


# ==========================================
# КОНКРЕТНЫЕ КОМПОНЕНТЫ
# ==========================================

class Compressor(BaseEquipment):
    def __init__(self, x, y):
        super().__init__(x, y, 60, 60, "Компрессор")
        self.load_svg()

    def load_svg(self):
        self.renderer.load(os.path.join(ICONS_DIR, f"compressor_{self.state}.svg"))

    def update_ports(self):
        self.ports['out'] = (self.x + 30, self.y)           # Выход сверху
        self.ports['in'] = (self.x + 30, self.y + 60)       # Вход снизу


class Condenser(BaseEquipment):
    def __init__(self, x, y):
        super().__init__(x, y, 60, 160, "Конденсатор")
        self.load_svg()

    def load_svg(self):
        self.renderer.load(os.path.join(ICONS_DIR, f"condenser_{self.state}.svg"))

    def update_ports(self):
        self.ports['in'] = (self.x + 30, self.y + 160)      # Вход снизу
        self.ports['out'] = (self.x + 30, self.y)           # Выход сверху


class Fan(BaseEquipment):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 40, "Вент.")
        self.load_svg()

    def load_svg(self):
        self.renderer.load(os.path.join(ICONS_DIR, f"fan_{self.state}.svg"))

    def update_ports(self):
        pass # У вентилятора нет трубных портов


class Throttle(BaseEquipment):
    def __init__(self, x, y):
        super().__init__(x, y, 60, 40, "Дроссель")
        self.load_svg()

    def load_svg(self):
        self.renderer.load(os.path.join(ICONS_DIR, f"throttle_{self.state}.svg"))

    def update_ports(self):
        self.ports['in'] = (self.x, self.y + 20)            
        self.ports['out'] = (self.x + 60, self.y + 20)      


class Valve(BaseEquipment):
    def __init__(self, x, y):
        super().__init__(x, y, 60, 40, "Клапан Байпаса")
        self.load_svg()

    def load_svg(self):
        self.renderer.load(os.path.join(ICONS_DIR, f"valve_{self.state}.svg"))

    def update_ports(self):
        self.ports['in'] = (self.x, self.y + 30)            # Вход слева (смещен вниз к центру клапана)
        self.ports['out'] = (self.x + 60, self.y + 30)      # Выход справа


class Pump(BaseEquipment):
    def __init__(self, x, y):
        super().__init__(x, y, 60, 60, "Насос")
        self.load_svg()

    def load_svg(self):
        self.renderer.load(os.path.join(ICONS_DIR, f"pump_{self.state}.svg"))

    def update_ports(self):
        self.ports['in'] = (self.x, self.y + 30)            # Вход слева (по центру)
        self.ports['out'] = (self.x + 60, self.y + 30)      # Выход справа


class Heater(BaseEquipment):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 40, "ТЭН")
        self.load_svg()

    def load_svg(self):
        self.renderer.load(os.path.join(ICONS_DIR, f"heater_{self.state}.svg"))

    def update_ports(self):
        self.ports['in'] = (self.x, self.y + 20)            # Вход слева
        self.ports['out'] = (self.x + 40, self.y + 20)      # Выход справа

    def draw(self, painter: QPainter):
        super().draw(painter)


class Tank(BaseEquipment):
    def __init__(self, x, y):
        super().__init__(x, y, 120, 200, "Бак и Испаритель")
        self.water_level = 0.85 
        self.load_svg()

    def load_svg(self):
        self.renderer.load(os.path.join(ICONS_DIR, f"tank_evap_{self.state}.svg"))

    def update_ports(self):
        # Порты фреона — левая сторона бака
        self.ports['freon_in'] = (self.x, self.y + 50)          # Левый, верхняя треть
        self.ports['freon_out'] = (self.x, self.y + 190)        # Левый, нижний край
        # Водяные входы — оба сверху, разнесены по X
        self.ports['water_lt_in'] = (self.x + 90, self.y)       # Вход L: сверху, правее
        self.ports['water_ht_in'] = (self.x + 30, self.y)       # Вход H: сверху, левее
        # Водяной выход — правая сторона
        self.ports['water_out'] = (self.x + 120, self.y + 160)  # Правый, середина
        # Слив — низ, центр
        self.ports['drain'] = (self.x + 60, self.y + 200)       # Низ, центр

    def draw(self, painter: QPainter):
        water_max_h = 190
        current_water_h = water_max_h * self.water_level
        water_rect = QRectF(self.x + 6, self.y + self.height - 5 - current_water_h, 108, current_water_h)
        painter.fillRect(water_rect, QColor(33, 150, 243, 100))
        
        self.renderer.render(painter, self.get_rect())
        self.draw_label(painter)


class ExternalPort(BaseEquipment):
    def __init__(self, x, y, name=""):
        super().__init__(x, y, 150, 30, name)

    def update_ports(self):
        """ 
        Штуцер всегда находится на левом краю блока (self.x), 
        так как порты стоят справа на экране, и трубы подходят к ним слева.
        """
        self.ports['in'] = (self.x, self.y + 20)
        self.ports['out'] = (self.x, self.y + 20)

    def draw(self, painter: QPainter):
        """ Переопределяем отрисовку: рисуем стрелку и текст сбоку """
        
        # Определяем направление: если это вход (и не слив), стрелка смотрит влево (внутрь схемы)
        is_input = "in" in self.id and "drain" not in self.id
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(60, 60, 60))
        
        path = QPainterPath()
        if is_input:
            # Стрелка ВЛЕВО (поток входит в чиллер). 
            # Острие касается левого края (self.x) - точки входа трубы
            path.moveTo(self.x, self.y + 20)          # Острие
            path.lineTo(self.x + 15, self.y + 10)      # Верхний угол базы
            path.lineTo(self.x + 15, self.y + 30)     # Нижний угол базы
            path.closeSubpath()
        else:
            # Стрелка ВПРАВО (поток выходит из чиллера).
            # Плоское основание касается левого края (self.x) - точки выхода трубы
            path.moveTo(self.x, self.y + 10)           # Верхний угол базы
            path.lineTo(self.x, self.y + 30)          # Нижний угол базы
            path.lineTo(self.x + 15, self.y + 20)     # Острие
            path.closeSubpath()
            
        painter.drawPath(path)
        
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(self.x + 25, self.y + 20, self.name)