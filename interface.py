import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QDoubleSpinBox, QGroupBox,
    QGridLayout, QTabWidget, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPainterPath, QPolygonF

class CustomChillerMnemonic(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(450) 
        
        self.is_running = False
        self.heater_on = False
        self.solenoid_open = False
        self.tank_level = 0.85

    def set_states(self, running, heater, solenoid):
        self.is_running = running
        self.heater_on = heater
        self.solenoid_open = solenoid
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg_color = QColor(245, 247, 250)
        water_cold = QColor(33, 150, 243)
        water_hot = QColor(255, 152, 0)
        freon = QColor(0, 188, 212)
        active = QColor(76, 175, 80)
        idle = QColor(180, 180, 180)
        heater_color = QColor(244, 67, 54)

        painter.fillRect(self.rect(), bg_color)
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 6, 6)

        painter.translate(120, 0) 

        pen_freon = QPen(freon if self.is_running else idle, 3, Qt.SolidLine)
        pen_lt = QPen(water_cold if self.is_running else idle, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        pen_ht = QPen(water_hot if self.is_running else idle, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        pen_drain = QPen(idle, 3, Qt.DashLine)

        # ФРЕОН
        painter.setPen(pen_freon)
        painter.drawLine(90, 280, 90, 230) 
        painter.drawLine(90, 230, 90, 210)
        painter.drawLine(90, 50, 90, 30)
        painter.drawLine(90, 30, 210, 30)
        painter.drawLine(250, 30, 300, 30)
        painter.drawLine(300, 30, 300, 180)
        painter.drawLine(300, 180, 340, 180)
        
        # ФРЕОН: Байпас
        painter.setPen(QPen(freon if self.solenoid_open else idle, 3, Qt.SolidLine))
        painter.drawLine(90, 230, 180, 230) 
        painter.drawLine(220, 230, 300, 230) 

        # ФРЕОН: Обратка
        painter.setPen(pen_freon)
        painter.drawLine(340, 350, 130, 350)
        painter.drawLine(130, 350, 130, 320)

        # ВОДА: Насос и выходы
        painter.setPen(pen_lt)
        painter.drawLine(440, 320, 500, 320)
        painter.drawLine(560, 320, 580, 320)
        painter.drawLine(580, 320, 750, 320)
        
        painter.setPen(pen_ht)
        painter.drawLine(580, 320, 580, 200)
        painter.drawLine(580, 200, 610, 200) 
        painter.drawLine(650, 200, 750, 200) 

        # ВОДА: Возвраты
        painter.setPen(pen_lt)
        painter.drawLine(750, 60, 420, 60)
        painter.drawLine(420, 60, 420, 160) 
        
        painter.setPen(pen_ht)
        painter.drawLine(750, 120, 380, 120)
        painter.drawLine(380, 120, 380, 160) 

        # Слив
        painter.setPen(pen_drain)
        painter.drawLine(400, 360, 400, 400)
        painter.drawLine(400, 400, 750, 400)

        # 2. ОТРИСОВКА КОМПОНЕНТОВ
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.setFont(QFont("Arial", 8, QFont.Bold))

        # БАК
        tank = QRectF(340, 160, 100, 200)
        painter.setBrush(QBrush(QColor(230, 235, 240)))
        painter.drawRoundedRect(tank, 4, 4)
        water_h = tank.height() * self.tank_level
        painter.setBrush(QBrush(water_cold))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(tank.x(), tank.bottom() - water_h, tank.width(), water_h), 4, 4)
        
        # Испаритель
        painter.setPen(QPen(freon if self.is_running else idle, 3))
        evap_path = QPainterPath()
        evap_path.moveTo(340, 180)
        for y in range(190, 350, 30):
            evap_path.lineTo(430, y)
            evap_path.lineTo(350, y + 15)
        evap_path.lineTo(340, 350)
        painter.drawPath(evap_path)
        painter.setPen(Qt.black)
        painter.drawText(tank.adjusted(0,5,0,0), Qt.AlignHCenter | Qt.AlignTop, "Бак и\nИспаритель")

        # Компрессор
        comp = QRectF(60, 280, 60, 80)
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.setBrush(QBrush(active if self.is_running else idle))
        painter.drawRoundedRect(comp, 10, 10)
        painter.drawRect(70, 270, 15, 10)
        painter.drawRect(95, 270, 15, 10)
        painter.setPen(Qt.white if self.is_running else Qt.black)
        painter.drawText(comp, Qt.AlignCenter, "Комп.")

        # Конденсатор
        cond = QRectF(70, 50, 40, 160)
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.setBrush(QBrush(QColor(210, 220, 230)))
        painter.drawRect(cond)
        for y in range(60, 210, 10):
            painter.drawLine(65, y, 115, y)
        painter.setPen(Qt.black)
        painter.drawText(QRectF(30, 215, 120, 20), Qt.AlignCenter, "Конденсатор")

        # Вентилятор
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.setBrush(QBrush(active if self.is_running else idle))
        painter.drawEllipse(15, 110, 40, 40)
        painter.drawLine(35, 130, 25, 120); painter.drawLine(35, 130, 45, 120); painter.drawLine(35, 130, 35, 145)
        painter.setPen(Qt.black)
        painter.drawText(QRectF(-20, 155, 100, 20), Qt.AlignCenter, "Вентилятор")

        # Дроссель
        painter.setPen(QPen(freon if self.is_running else idle, 3))
        for x in range(210, 250, 5):
            painter.drawLine(x, 20, x+5, 40)
        painter.setPen(Qt.black)
        painter.drawText(QRectF(190, 0, 80, 20), Qt.AlignCenter, "Дроссель")

        # Электромагнитный клапан
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.setBrush(QBrush(active if self.solenoid_open else idle))
        sol_poly = QPolygonF([QPointF(180, 220), QPointF(220, 240), QPointF(220, 220), QPointF(180, 240)])
        painter.drawPolygon(sol_poly)
        painter.drawRect(190, 210, 20, 15)
        painter.setPen(Qt.black)
        painter.drawText(QRectF(160, 245, 80, 30), Qt.AlignCenter, "Клапан\nБайпаса")

        # Насос
        pump = QPointF(530, 320)
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.setBrush(QBrush(active if self.is_running else idle))
        painter.drawEllipse(pump, 30, 30)
        painter.drawRect(495, 305, 10, 30) 
        painter.setBrush(QBrush(Qt.white))
        painter.drawPolygon(QPolygonF([pump+QPointF(-10,-12), pump+QPointF(-10,12), pump+QPointF(15,0)]))
        painter.setPen(Qt.black)
        painter.drawText(QRectF(pump.x()-40, pump.y()+35, 80, 20), Qt.AlignCenter, "Насос")

        # Нагреватель
        heater_rect = QRectF(610, 160, 40, 80)
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.setBrush(QBrush(heater_color if self.heater_on else QColor(220,220,220)))
        painter.drawRect(heater_rect)
        painter.setPen(QPen(Qt.white if self.heater_on else Qt.darkGray, 2))
        for y in range(170, 230, 10):
            painter.drawLine(615, y, 645, y+5)
            painter.drawLine(645, y+5, 615, y+10)
        painter.setPen(Qt.black)
        painter.drawText(QRectF(600, 135, 60, 20), Qt.AlignCenter, "ТЭН")

        # 3. ПОДПИСИ ШТУЦЕРОВ
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.setPen(Qt.black)
        painter.drawText(QRectF(765, 50, 200, 20), Qt.AlignLeft | Qt.AlignVCenter, "Вход L (Лазер)")
        painter.drawText(QRectF(765, 110, 200, 20), Qt.AlignLeft | Qt.AlignVCenter, "Вход H (Оптика)")
        painter.drawText(QRectF(755, 190, 200, 20), Qt.AlignLeft | Qt.AlignVCenter, "Выход H (Оптика)")
        painter.drawText(QRectF(755, 310, 200, 20), Qt.AlignLeft | Qt.AlignVCenter, "Выход L (Лазер)")
        painter.drawText(QRectF(755, 390, 200, 20), Qt.AlignLeft | Qt.AlignVCenter, "Слив")

        # Стрелочки
        painter.setBrush(Qt.black)
        painter.drawPolygon(QPolygonF([QPointF(750, 60), QPointF(760, 55), QPointF(760, 65)])) 
        painter.drawPolygon(QPolygonF([QPointF(750, 120), QPointF(760, 115), QPointF(760, 125)])) 
        painter.drawPolygon(QPolygonF([QPointF(750, 200), QPointF(740, 195), QPointF(740, 205)])) 
        painter.drawPolygon(QPolygonF([QPointF(750, 320), QPointF(740, 315), QPointF(740, 325)])) 
        painter.drawPolygon(QPolygonF([QPointF(750, 400), QPointF(740, 395), QPointF(740, 405)])) 

        painter.end()


class ChillerPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Интерфейс чиллера")
        self.setMinimumSize(1200, 850)
        self.init_ui()
        self.apply_styles()
        self.connect_signals()
        self.toggle_mode_settings(0)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.setup_monitoring_tab()
        self.setup_service_tab()

    def setup_monitoring_tab(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Мониторинг (Главная)")
        layout = QVBoxLayout(tab)
        
        self.mnemonic = CustomChillerMnemonic()
        layout.addWidget(self.mnemonic)

        mid_panel = QHBoxLayout()
        
        # ТЕМПЕРАТУРЫ
        temp_group = QGroupBox("Управление температурой")
        temp_layout = QGridLayout()
        temp_layout.setSpacing(10)
        
        temp_layout.addWidget(QLabel("Режим:"), 0, 0)
        self.cb_mode_main = QComboBox()
        self.cb_mode_main.addItems(["Интеллектуальный (Авто)", "Постоянный (Ручной)"])
        self.cb_mode_main.setStyleSheet("font-size: 14px; font-weight: bold;")
        temp_layout.addWidget(self.cb_mode_main, 0, 1, 1, 2)

        lbl_act = QLabel("Текущая")
        lbl_act.setStyleSheet("color: #777; font-size: 12px;")
        lbl_set = QLabel("Уставка")
        lbl_set.setStyleSheet("color: #777; font-size: 12px;")
        temp_layout.addWidget(lbl_act, 1, 1, Qt.AlignCenter)
        temp_layout.addWidget(lbl_set, 1, 2, Qt.AlignCenter)

        temp_layout.addWidget(QLabel("Лазер (LT):"), 2, 0)
        self.lbl_t1 = QLabel("25.0")
        self.lbl_t1.setStyleSheet("font-size: 26px; color: #1976D2; font-weight: bold;")
        temp_layout.addWidget(self.lbl_t1, 2, 1, Qt.AlignCenter)
        
        self.sp_main_lt = QDoubleSpinBox()
        self.sp_main_lt.setRange(15.0, 35.0)
        self.sp_main_lt.setValue(25.0)
        self.sp_main_lt.setSuffix(" °C")
        self.sp_main_lt.setStyleSheet("font-size: 16px; font-weight: bold;")
        temp_layout.addWidget(self.sp_main_lt, 2, 2)

        temp_layout.addWidget(QLabel("Оптика (HT):"), 3, 0)
        self.lbl_t2 = QLabel("30.0")
        self.lbl_t2.setStyleSheet("font-size: 26px; color: #F57C00; font-weight: bold;")
        temp_layout.addWidget(self.lbl_t2, 3, 1, Qt.AlignCenter)
        
        self.sp_main_ht = QDoubleSpinBox()
        self.sp_main_ht.setRange(20.0, 40.0)
        self.sp_main_ht.setValue(30.0)
        self.sp_main_ht.setSuffix(" °C")
        self.sp_main_ht.setStyleSheet("font-size: 16px; font-weight: bold;")
        temp_layout.addWidget(self.sp_main_ht, 3, 2)

        temp_layout.addWidget(QLabel("Окр. среда:"), 4, 0)
        self.lbl_t_amb = QLabel("24.1")
        self.lbl_t_amb.setStyleSheet("font-size: 18px; color: #555; font-weight: bold;")
        temp_layout.addWidget(self.lbl_t_amb, 4, 1, Qt.AlignCenter)
        
        temp_group.setLayout(temp_layout)
        mid_panel.addWidget(temp_group)

        # Гидравлика
        hydr_group = QGroupBox("Гидравлика")
        hydr_layout = QGridLayout()
        hydr_layout.setSpacing(5)
        
        hydr_layout.addWidget(QLabel("Расход (LT):"), 0, 0)
        self.lbl_flow_lt = QLabel("0.0 л/м")
        self.lbl_flow_lt.setStyleSheet("font-size: 18px; font-weight: bold;")
        hydr_layout.addWidget(self.lbl_flow_lt, 0, 1, Qt.AlignRight)

        hydr_layout.addWidget(QLabel("Расход (HT):"), 1, 0)
        self.lbl_flow_ht = QLabel("0.0 л/м")
        self.lbl_flow_ht.setStyleSheet("font-size: 18px; font-weight: bold;")
        hydr_layout.addWidget(self.lbl_flow_ht, 1, 1, Qt.AlignRight)

        hydr_layout.addWidget(QLabel("Давление:"), 2, 0)
        self.lbl_press = QLabel("0.0 бар")
        self.lbl_press.setStyleSheet("font-size: 18px; font-weight: bold;")
        hydr_layout.addWidget(self.lbl_press, 2, 1, Qt.AlignRight)

        hydr_layout.addWidget(QLabel("Уровень воды:"), 3, 0)
        self.lbl_level = QLabel("Норма")
        self.lbl_level.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E7D32;")
        hydr_layout.addWidget(self.lbl_level, 3, 1, Qt.AlignRight)

        hydr_group.setLayout(hydr_layout)
        mid_panel.addWidget(hydr_group)

        # Состояние агрегатов
        status_group = QGroupBox("Агрегаты")
        status_layout = QVBoxLayout()
        status_layout.setSpacing(2)
        
        self.lbl_pump = QLabel("Насос: ВЫКЛ")
        self.lbl_comp = QLabel("Компрессор: ВЫКЛ")
        self.lbl_heater = QLabel("ТЭН: ВЫКЛ")
        self.lbl_valve = QLabel("Байпас: ЗАКРЫТ")

        for lbl in [self.lbl_pump, self.lbl_comp, self.lbl_heater, self.lbl_valve]:
            lbl.setStyleSheet("color: #757575; font-weight: bold; font-size: 13px;")
            status_layout.addWidget(lbl)

        status_group.setLayout(status_layout)
        mid_panel.addWidget(status_group)

        # Управление
        ctrl_group = QGroupBox("Управление")
        ctrl_layout = QVBoxLayout()
        
        self.status_label = QLabel("ОСТАНОВЛЕН")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("background-color: #e0e0e0; color: #555; font-size: 14px; font-weight: bold; padding: 6px; border-radius: 4px;")
        ctrl_layout.addWidget(self.status_label)

        btn_box = QHBoxLayout()
        self.start_btn = QPushButton("СТАРТ")
        self.stop_btn = QPushButton("СТОП")
        self.stop_btn.setEnabled(False)
        
        btn_box.addWidget(self.start_btn)
        btn_box.addWidget(self.stop_btn)
        ctrl_layout.addLayout(btn_box)
        ctrl_group.setLayout(ctrl_layout)
        mid_panel.addWidget(ctrl_group)

        layout.addLayout(mid_panel)

    def setup_service_tab(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Настройки и Наладка")
        layout = QHBoxLayout(tab)
        
        col_left = QVBoxLayout()
        col_right = QVBoxLayout()

        sp_group = QGroupBox("Параметры регулирования температур")
        sp_layout = QGridLayout()
        sp_layout.setSpacing(10)
        
        # Строка 1: Режим
        sp_layout.addWidget(QLabel("Режим работы:"), 0, 0)
        self.cb_mode_srv = QComboBox()
        self.cb_mode_srv.addItems(["Интеллектуальный (Авто)", "Постоянный (Ручной)"])
        sp_layout.addWidget(self.cb_mode_srv, 0, 1, 1, 3)
        
        # Строка 2: LT Контур
        sp_layout.addWidget(QLabel("Уставка Лазер (LT):"), 1, 0)
        self.sp_lt = QDoubleSpinBox(); self.sp_lt.setRange(15.0, 35.0); self.sp_lt.setValue(25.0)
        sp_layout.addWidget(self.sp_lt, 1, 1)

        sp_layout.addWidget(QLabel("Гистерезис (LT):"), 1, 2)
        self.sp_hyst_lt = QDoubleSpinBox(); self.sp_hyst_lt.setRange(0.1, 5.0); self.sp_hyst_lt.setSingleStep(0.1); self.sp_hyst_lt.setValue(0.5)
        sp_layout.addWidget(self.sp_hyst_lt, 1, 3)

        # Строка 3: HT Контур
        sp_layout.addWidget(QLabel("Уставка Оптика (HT):"), 2, 0)
        self.sp_ht = QDoubleSpinBox(); self.sp_ht.setRange(20.0, 40.0); self.sp_ht.setValue(30.0)
        sp_layout.addWidget(self.sp_ht, 2, 1)

        sp_layout.addWidget(QLabel("Гистерезис (HT):"), 2, 2)
        self.sp_hyst_ht = QDoubleSpinBox(); self.sp_hyst_ht.setRange(0.1, 5.0); self.sp_hyst_ht.setSingleStep(0.1); self.sp_hyst_ht.setValue(1.0)
        sp_layout.addWidget(self.sp_hyst_ht, 2, 3)

        # Строка 4: Интеллектуальный режим
        sp_layout.addWidget(QLabel("Дельта Интеллект. (ΔT):"), 3, 0)
        self.sp_delta = QDoubleSpinBox(); self.sp_delta.setRange(-10.0, 10.0); self.sp_delta.setSingleStep(0.1); self.sp_delta.setValue(-2.0)
        sp_layout.addWidget(self.sp_delta, 3, 1)

        # Строка 5: Пороги аварий
        sp_layout.addWidget(QLabel("Доп. перегрев (+°C):"), 4, 0)
        self.sp_alm_high = QDoubleSpinBox(); self.sp_alm_high.setRange(1.0, 15.0); self.sp_alm_high.setSingleStep(0.1); self.sp_alm_high.setValue(3.0)
        sp_layout.addWidget(self.sp_alm_high, 4, 1)

        sp_layout.addWidget(QLabel("Доп. переохлажд. (-°C):"), 4, 2)
        self.sp_alm_low = QDoubleSpinBox(); self.sp_alm_low.setRange(1.0, 15.0); self.sp_alm_low.setSingleStep(0.1); self.sp_alm_low.setValue(3.0)
        sp_layout.addWidget(self.sp_alm_low, 4, 3)

        sp_group.setLayout(sp_layout)
        col_left.addWidget(sp_group)

        # Индикаторы Аварий
        alarm_group = QGroupBox("Статус защит и аварий")
        alarm_layout = QVBoxLayout()
        alarm_layout.setSpacing(10)
        
        alarms = [
            "Превышение максимальной температуры помещения",
            "Превышение максимальной температуры воды",
            "Падение температуры воды ниже минимума",
            "Неисправность датчиков температуры",
            "Слишком низкий уровень воды в баке",
            "Ошибка насоса, блокировка или падение расхода воды"
        ]
        
        self.alarm_indicators = [] 
        
        for text in alarms:
            row_layout = QHBoxLayout()
            indicator = QLabel()
            indicator.setFixedSize(16, 16)
            indicator.setStyleSheet("background-color: #4CAF50; border-radius: 8px; border: 1px solid #388E3C;") 
            
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #333; font-weight: bold; font-size: 13px;")
            
            row_layout.addWidget(indicator)
            row_layout.addWidget(lbl)
            row_layout.addStretch()
            
            alarm_layout.addLayout(row_layout)
            self.alarm_indicators.append(indicator)
            
        alarm_group.setLayout(alarm_layout)
        col_left.addWidget(alarm_group)
        col_left.addStretch()

        # ПИД-регулятор
        pid_group = QGroupBox("ПИД-регулятор (ТЭН Оптики)")
        pid_layout = QGridLayout()
        pid_layout.setSpacing(10)

        lbl_pid_desc = QLabel("Настройка ШИМ для плавного удержания температуры")
        lbl_pid_desc.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        pid_layout.addWidget(lbl_pid_desc, 0, 0, 1, 2)

        pid_layout.addWidget(QLabel("Пропорц. (P):"), 1, 0)
        self.pid_p = QDoubleSpinBox()
        self.pid_p.setRange(0.0, 100.0); self.pid_p.setSingleStep(0.1); self.pid_p.setValue(12.5)
        pid_layout.addWidget(self.pid_p, 1, 1)

        pid_layout.addWidget(QLabel("Интеграл. (I):"), 2, 0)
        self.pid_i = QDoubleSpinBox()
        self.pid_i.setRange(0.0, 100.0); self.pid_i.setSingleStep(0.1); self.pid_i.setValue(1.8)
        pid_layout.addWidget(self.pid_i, 2, 1)

        pid_layout.addWidget(QLabel("Дифференц. (D):"), 3, 0)
        self.pid_d = QDoubleSpinBox()
        self.pid_d.setRange(0.0, 100.0); self.pid_d.setSingleStep(0.1); self.pid_d.setValue(0.2)
        pid_layout.addWidget(self.pid_d, 3, 1)

        pid_group.setLayout(pid_layout)
        col_right.addWidget(pid_group)

        # Ручное управление
        man_group = QGroupBox("Ручное тестирование выходов")
        man_layout = QVBoxLayout()
        self.cb_debug = QCheckBox("Включить режим наладки (Блокирует автомат)")
        self.cb_debug.setStyleSheet("color: #D32F2F; font-weight: bold;")
        man_layout.addWidget(self.cb_debug)

        btn_grid = QGridLayout()
        self.btn_man_pump = QPushButton("Реле: Насос")
        self.btn_man_comp = QPushButton("Реле: Компрессор")
        self.btn_man_fan = QPushButton("Реле: Вентилятор")
        self.btn_man_heater = QPushButton("Реле: ТЭН")
        self.btn_man_valve = QPushButton("Реле: Клапан Байпаса")

        self.man_buttons = [self.btn_man_pump, self.btn_man_comp, self.btn_man_fan, self.btn_man_heater, self.btn_man_valve]
        
        for i, btn in enumerate(self.man_buttons):
            btn.setCheckable(True)
            btn.setEnabled(False)
            btn.setStyleSheet("QPushButton:checked { background-color: #FF9800; color: white; }")
            btn_grid.addWidget(btn, i//2, i%2)
            
        man_layout.addLayout(btn_grid)
        man_group.setLayout(man_layout)
        col_right.addWidget(man_group)
        col_right.addStretch()

        layout.addLayout(col_left)
        layout.addLayout(col_right)

    def connect_signals(self):
        # Синхронизация уставок между вкладками
        self.sp_main_lt.valueChanged.connect(self.sp_lt.setValue)
        self.sp_lt.valueChanged.connect(self.sp_main_lt.setValue)
        
        self.sp_main_ht.valueChanged.connect(self.sp_ht.setValue)
        self.sp_ht.valueChanged.connect(self.sp_main_ht.setValue)
        
        # Привязка логики смены режима
        self.cb_mode_main.currentIndexChanged.connect(self.cb_mode_srv.setCurrentIndex)
        self.cb_mode_srv.currentIndexChanged.connect(self.cb_mode_main.setCurrentIndex)
        self.cb_mode_main.currentIndexChanged.connect(self.toggle_mode_settings)

        self.start_btn.clicked.connect(self.start_system)
        self.stop_btn.clicked.connect(self.stop_system)
        self.cb_debug.toggled.connect(self.toggle_debug)
        
        self.btn_man_pump.toggled.connect(self.update_manual_state)
        self.btn_man_comp.toggled.connect(self.update_manual_state)
        self.btn_man_heater.toggled.connect(self.update_manual_state)
        self.btn_man_valve.toggled.connect(self.update_manual_state)

    def toggle_mode_settings(self, index):
        """ Блокирует/разблокирует поля в зависимости от режима (0:Авто, 1:Ручной) """
        is_manual = (index == 1)
        
        self.sp_lt.setEnabled(is_manual)
        self.sp_ht.setEnabled(is_manual)
        self.sp_main_lt.setEnabled(is_manual)
        self.sp_main_ht.setEnabled(is_manual)
        
        self.sp_delta.setEnabled(not is_manual)

    def update_manual_state(self):
        if self.cb_debug.isChecked():
            is_run = self.btn_man_pump.isChecked() or self.btn_man_comp.isChecked()
            self.mnemonic.set_states(
                running=is_run,
                heater=self.btn_man_heater.isChecked(),
                solenoid=self.btn_man_valve.isChecked()
            )

    def start_system(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("АВТОМАТИКА: В РАБОТЕ")
        self.status_label.setStyleSheet("background-color: #C8E6C9; color: #2E7D32; font-size: 14px; font-weight: bold; padding: 6px; border-radius: 4px;")
        
        self.lbl_pump.setText("Насос: РАБОТА")
        self.lbl_pump.setStyleSheet("color: #2E7D32; font-weight: bold; font-size: 13px;")
        self.lbl_comp.setText("Компрессор: РАБОТА")
        self.lbl_comp.setStyleSheet("color: #1976D2; font-weight: bold; font-size: 13px;")
        
        self.lbl_heater.setText("ТЭН: НАГРЕВ")
        self.lbl_heater.setStyleSheet("color: #D32F2F; font-weight: bold; font-size: 13px;")
        
        self.lbl_flow_lt.setText("14.5 л/м")
        self.lbl_flow_ht.setText("2.8 л/м")
        self.lbl_press.setText("3.1 бар")
        self.lbl_t_amb.setText("25.2")
        self.lbl_level.setText("Норма (85%)")
        self.lbl_level.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E7D32;")
        
        self.mnemonic.set_states(running=True, heater=True, solenoid=False)

    def stop_system(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("АВТОМАТИКА: ОСТАНОВ")
        self.status_label.setStyleSheet("background-color: #e0e0e0; color: #555; font-size: 14px; font-weight: bold; padding: 6px; border-radius: 4px;")
        
        for lbl in [self.lbl_pump, self.lbl_comp, self.lbl_heater, self.lbl_valve]:
            lbl.setText(lbl.text().split(":")[0] + ": ВЫКЛ")
            lbl.setStyleSheet("color: #757575; font-weight: bold; font-size: 13px;")
            
        self.lbl_flow_lt.setText("0.0 л/м")
        self.lbl_flow_ht.setText("0.0 л/м")
        self.lbl_press.setText("0.0 бар")
            
        self.mnemonic.set_states(running=False, heater=False, solenoid=False)

    def toggle_debug(self, checked):
        self.start_btn.setEnabled(not checked)
        if checked:
            self.stop_system()
            self.status_label.setText("РЕЖИМ НАЛАДКИ (РУЧНОЙ)")
            self.status_label.setStyleSheet("background-color: #FFE0B2; color: #E65100; font-size: 14px; font-weight: bold; padding: 6px; border-radius: 4px;")
            
        for btn in self.man_buttons:
            btn.setEnabled(checked)
            if not checked:
                btn.setChecked(False)
        
        if not checked:
            self.update_manual_state()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f2f4f7; }
            QGroupBox { font-weight: bold; font-size: 14px; border: 1px solid #c4c8cc; border-radius: 6px; margin-top: 15px; padding-top: 15px; background-color: #ffffff; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #333; }
            QPushButton { background-color: #4CAF50; color: white; border: none; padding: 10px 15px; font-size: 13px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cfd8dc; color: #90a4ae; }
            QDoubleSpinBox, QComboBox { padding: 5px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; }
            QDoubleSpinBox:disabled { background-color: #eeeeee; color: #999999; }
            QTabWidget::pane { border: 1px solid #c4c8cc; border-radius: 6px; background-color: #ffffff; }
            QTabBar::tab { background-color: #e6e9ed; border: 1px solid #c4c8cc; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; padding: 8px 20px; font-weight: bold; color: #555; }
            QTabBar::tab:selected { background-color: #ffffff; border-bottom: 1px solid #ffffff; color: #000; }
        """)
        self.stop_btn.setStyleSheet("""
            QPushButton { background-color: #F44336; }
            QPushButton:hover { background-color: #D32F2F; }
            QPushButton:disabled { background-color: #cfd8dc; color: #90a4ae; }
        """)