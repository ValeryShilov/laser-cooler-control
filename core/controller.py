"""
Контроллер системы чиллера.

Управляет состояниями (старт/стоп/наладка) и излучает сигналы.
Не знает ничего про UI-виджеты — общается только через Qt-сигналы.
"""
from PySide6.QtCore import QObject, Signal
from core.models import SystemState


class SystemController(QObject):
    """Центральный контроллер бизнес-логики чиллера."""

    state_changed = Signal(object)  # Излучает SystemState

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._heater = False
        self._valve = False
        self._debug_mode = False

    # ── Публичный API ──

    def start(self):
        """Запуск системы в автоматическом режиме."""
        self._running = True
        self._heater = True
        self._valve = False
        self._emit()

    def stop(self):
        """Остановка системы."""
        self._running = False
        self._heater = False
        self._valve = False
        self._emit()

    def set_debug_mode(self, enabled: bool):
        """Включение/выключение режима наладки."""
        if enabled:
            self.stop()
        self._debug_mode = enabled
        self._emit()

    def set_relay(self, name: str, state: bool):
        """Ручное управление реле в режиме наладки."""
        if name == "heater":
            self._heater = state
        elif name == "valve":
            self._valve = state
        self._emit()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def debug_mode(self) -> bool:
        return self._debug_mode

    # ── Внутренние методы ──

    def _emit(self):
        """Собирает текущее состояние и излучает сигнал."""
        state = SystemState(
            running=self._running,
            heater_on=self._heater,
            valve_open=self._valve,
            debug_mode=self._debug_mode,
            # Данные датчиков будут заполняться адаптером в будущем
            temp_lt=25.0 if self._running else 25.0,
            temp_ht=30.0 if self._running else 30.0,
            temp_ambient=25.2 if self._running else 24.1,
            flow_lt=14.5 if self._running else 0.0,
            flow_ht=2.8 if self._running else 0.0,
            pressure=3.1 if self._running else 0.0,
            water_level=0.85,
        )
        self.state_changed.emit(state)
