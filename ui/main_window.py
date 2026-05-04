from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QDoubleSpinBox, QGroupBox,
    QGridLayout, QTabWidget, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt

from ui.mnemonic import ChillerMnemonic
from ui.styles import MAIN_STYLE, STOP_BUTTON_STYLE
from core.controller import SystemController

class ChillerPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Интерфейс чиллера")
        self.setMinimumSize(1200, 850)
        
        self.controller = SystemController(self)
        
        self.init_ui()
        self.apply_styles()
        self.connect_signals()
        
        # Подписываемся на изменения состояния
        self.controller.state_changed.connect(self._on_state_changed)
        
        # Инициализируем состояния полей ввода
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
        
        # ВСТРАИВАЕМ МНЕМОСХЕМУ
        self.mnemonic = ChillerMnemonic()
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

        # ГИДРАВЛИКА
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

        # СОСТОЯНИЕ АГРЕГАТОВ
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

        # УПРАВЛЕНИЕ
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
        
        sp_layout.addWidget(QLabel("Режим работы:"), 0, 0)
        self.cb_mode_srv = QComboBox()
        self.cb_mode_srv.addItems(["Интеллектуальный (Авто)", "Постоянный (Ручной)"])
        sp_layout.addWidget(self.cb_mode_srv, 0, 1, 1, 3)
        
        sp_layout.addWidget(QLabel("Уставка Лазер (LT):"), 1, 0)
        self.sp_lt = QDoubleSpinBox(); self.sp_lt.setRange(15.0, 35.0); self.sp_lt.setValue(25.0)
        sp_layout.addWidget(self.sp_lt, 1, 1)

        sp_layout.addWidget(QLabel("Гистерезис (LT):"), 1, 2)
        self.sp_hyst_lt = QDoubleSpinBox(); self.sp_hyst_lt.setRange(0.1, 5.0); self.sp_hyst_lt.setSingleStep(0.1); self.sp_hyst_lt.setValue(0.5)
        sp_layout.addWidget(self.sp_hyst_lt, 1, 3)

        sp_layout.addWidget(QLabel("Уставка Оптика (HT):"), 2, 0)
        self.sp_ht = QDoubleSpinBox(); self.sp_ht.setRange(20.0, 40.0); self.sp_ht.setValue(30.0)
        sp_layout.addWidget(self.sp_ht, 2, 1)

        sp_layout.addWidget(QLabel("Гистерезис (HT):"), 2, 2)
        self.sp_hyst_ht = QDoubleSpinBox(); self.sp_hyst_ht.setRange(0.1, 5.0); self.sp_hyst_ht.setSingleStep(0.1); self.sp_hyst_ht.setValue(1.0)
        sp_layout.addWidget(self.sp_hyst_ht, 2, 3)

        sp_layout.addWidget(QLabel("Дельта Интеллект. (ΔT):"), 3, 0)
        self.sp_delta = QDoubleSpinBox(); self.sp_delta.setRange(-10.0, 10.0); self.sp_delta.setSingleStep(0.1); self.sp_delta.setValue(-2.0)
        sp_layout.addWidget(self.sp_delta, 3, 1)

        sp_layout.addWidget(QLabel("Доп. перегрев (+°C):"), 4, 0)
        self.sp_alm_high = QDoubleSpinBox(); self.sp_alm_high.setRange(1.0, 15.0); self.sp_alm_high.setSingleStep(0.1); self.sp_alm_high.setValue(3.0)
        sp_layout.addWidget(self.sp_alm_high, 4, 1)

        sp_layout.addWidget(QLabel("Доп. переохлажд. (-°C):"), 4, 2)
        self.sp_alm_low = QDoubleSpinBox(); self.sp_alm_low.setRange(1.0, 15.0); self.sp_alm_low.setSingleStep(0.1); self.sp_alm_low.setValue(3.0)
        sp_layout.addWidget(self.sp_alm_low, 4, 3)

        sp_group.setLayout(sp_layout)
        col_left.addWidget(sp_group)

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
        self.sp_main_lt.valueChanged.connect(self.sp_lt.setValue)
        self.sp_lt.valueChanged.connect(self.sp_main_lt.setValue)
        
        self.sp_main_ht.valueChanged.connect(self.sp_ht.setValue)
        self.sp_ht.valueChanged.connect(self.sp_main_ht.setValue)
        
        self.cb_mode_main.currentIndexChanged.connect(self.cb_mode_srv.setCurrentIndex)
        self.cb_mode_srv.currentIndexChanged.connect(self.cb_mode_main.setCurrentIndex)
        self.cb_mode_main.currentIndexChanged.connect(self.toggle_mode_settings)

        self.start_btn.clicked.connect(self.controller.start)
        self.stop_btn.clicked.connect(self.controller.stop)
        self.cb_debug.toggled.connect(self._on_debug_toggled)
        
        self.btn_man_pump.toggled.connect(self._on_manual_relay)
        self.btn_man_comp.toggled.connect(self._on_manual_relay)
        self.btn_man_heater.toggled.connect(self._on_manual_relay)
        self.btn_man_valve.toggled.connect(self._on_manual_relay)

    def toggle_mode_settings(self, index):
        is_manual = (index == 1)
        self.sp_lt.setEnabled(is_manual)
        self.sp_ht.setEnabled(is_manual)
        self.sp_main_lt.setEnabled(is_manual)
        self.sp_main_ht.setEnabled(is_manual)
        self.sp_delta.setEnabled(not is_manual)

    # ================================================================
    #  Реакция на изменение состояния (сигнал от контроллера)
    # ================================================================

    def _on_state_changed(self, state):
        """Обновляет все виджеты по данным из SystemState."""
        if state.running:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("АВТОМАТИКА: В РАБОТЕ")
            self.status_label.setStyleSheet("background-color: #C8E6C9; color: #2E7D32; font-size: 14px; font-weight: bold; padding: 6px; border-radius: 4px;")

            self.lbl_pump.setText("Насос: РАБОТА")
            self.lbl_pump.setStyleSheet("color: #2E7D32; font-weight: bold; font-size: 13px;")
            self.lbl_comp.setText("Компрессор: РАБОТА")
            self.lbl_comp.setStyleSheet("color: #1976D2; font-weight: bold; font-size: 13px;")
            self.lbl_heater.setText("ТЭН: НАГРЕВ" if state.heater_on else "ТЭН: ВЫКЛ")
            self.lbl_heater.setStyleSheet("color: #D32F2F; font-weight: bold; font-size: 13px;" if state.heater_on else "color: #757575; font-weight: bold; font-size: 13px;")
            self.lbl_valve.setText("Байпас: ЗАКРЫТ")

            self.lbl_flow_lt.setText(f"{state.flow_lt} л/м")
            self.lbl_flow_ht.setText(f"{state.flow_ht} л/м")
            self.lbl_press.setText(f"{state.pressure} бар")
            self.lbl_t_amb.setText(str(state.temp_ambient))
            self.lbl_level.setText(f"Норма ({int(state.water_level * 100)}%)")
            self.lbl_level.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E7D32;")
        else:
            self.start_btn.setEnabled(not state.debug_mode)
            self.stop_btn.setEnabled(False)

            if state.debug_mode:
                self.status_label.setText("РЕЖИМ НАЛАДКИ (РУЧНОЙ)")
                self.status_label.setStyleSheet("background-color: #FFE0B2; color: #E65100; font-size: 14px; font-weight: bold; padding: 6px; border-radius: 4px;")
            else:
                self.status_label.setText("АВТОМАТИКА: ОСТАНОВ")
                self.status_label.setStyleSheet("background-color: #e0e0e0; color: #555; font-size: 14px; font-weight: bold; padding: 6px; border-radius: 4px;")

            for lbl in [self.lbl_pump, self.lbl_comp, self.lbl_heater, self.lbl_valve]:
                lbl.setText(lbl.text().split(":")[0] + ": ВЫКЛ")
                lbl.setStyleSheet("color: #757575; font-weight: bold; font-size: 13px;")

            self.lbl_flow_lt.setText("0.0 л/м")
            self.lbl_flow_ht.setText("0.0 л/м")
            self.lbl_press.setText("0.0 бар")

        # Обновляем мнемосхему
        self.mnemonic.set_states(
            running=state.running,
            heater=state.heater_on,
            solenoid=state.valve_open
        )

    def _on_debug_toggled(self, checked):
        """Реакция на переключение режима наладки."""
        self.controller.set_debug_mode(checked)
        for btn in self.man_buttons:
            btn.setEnabled(checked)
            if not checked:
                btn.setChecked(False)

    def _on_manual_relay(self):
        """Реакция на переключение реле в режиме наладки."""
        if self.cb_debug.isChecked():
            is_run = self.btn_man_pump.isChecked() or self.btn_man_comp.isChecked()
            self.controller._running = is_run
            self.controller.set_relay("heater", self.btn_man_heater.isChecked())
            self.controller.set_relay("valve", self.btn_man_valve.isChecked())

    def apply_styles(self):
        self.setStyleSheet(MAIN_STYLE)
        self.stop_btn.setStyleSheet(STOP_BUTTON_STYLE)