from PySide6.QtCore import QObject, Signal
from core.models import SystemState, SystemMode
from hardware.base import BaseAdapter


class SystemController(QObject):
    """Центральный контроллер бизнес-логики чиллера."""

    state_changed = Signal(object)  # Излучает SystemState

    def __init__(self, adapter: BaseAdapter, parent=None):
        super().__init__(parent)
        self.adapter = adapter
        self.mode = SystemMode.OFF


    def start(self):
        """Запуск системы в автоматическом режиме."""
        self.mode = SystemMode.AUTO
        
        self.adapter.set_relay('heater', True)
        self.adapter.set_relay('valve', False)
        self.adapter.set_relay('pump', True)
        self._emit()

    def stop(self):
        """Остановка системы."""
        self.mode = SystemMode.OFF
        
        self.adapter.set_relay('heater', False)
        self.adapter.set_relay('valve', False)
        self.adapter.set_relay('pump', False)
        self._emit()

    def set_mode(self, mode: SystemMode):
        """Установка режима работы системы."""
        if mode != SystemMode.AUTO and self.mode == SystemMode.AUTO:
            self.stop()
        self.mode = mode
        self._emit()

    def set_relay(self, name: str, state: bool):
        """Ручное управление реле (только в ручном режиме)."""
        if self.mode != SystemMode.MANUAL:
            return  # Игнорируем в других режимах
            
        self.adapter.set_relay(name, state)
        self._emit()

    # ── Внутренние методы ──

    def _emit(self):
        """Считывает данные с оборудования, собирает состояние и излучает сигнал."""
        sensors = self.adapter.read_sensors()
        
        state = SystemState(
            mode=self.mode,
            heater_on=self.adapter.get_relay('heater'),
            valve_open=self.adapter.get_relay('valve'),
            temp_lt=sensors.get('temp_lt', 0.0),
            temp_ht=sensors.get('temp_ht', 0.0),
            temp_ambient=sensors.get('temp_ambient', 0.0),
            flow_lt=sensors.get('flow_lt', 0.0),
            flow_ht=sensors.get('flow_ht', 0.0),
            pressure=sensors.get('pressure', 0.0),
            water_level=sensors.get('water_level', 0.0),
        )
        self.state_changed.emit(state)
