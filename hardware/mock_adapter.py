"""
Возвращает статические/случайные значения датчиков.
Используется для разработки и тестирования UI.
"""
from hardware.base import BaseAdapter


class MockAdapter(BaseAdapter):
    """Имитирует оборудование чиллера для отладки."""

    def __init__(self):
        self._relays = {
            'pump': False,
            'compressor': False,
            'heater': False,
            'valve': False,
            'fan': False,
        }

    def read_sensors(self) -> dict:
        """Возвращает фиксированные значения (как сейчас в interface.py)."""
        running = self._relays.get('pump', False) or self._relays.get('compressor', False)
        return {
            'temp_lt': 25.0,
            'temp_ht': 30.0,
            'temp_ambient': 25.2 if running else 24.1,
            'flow_lt': 14.5 if running else 0.0,
            'flow_ht': 2.8 if running else 0.0,
            'pressure': 3.1 if running else 0.0,
            'water_level': 0.85,
        }

    def set_relay(self, name: str, state: bool):
        """Сохраняет состояние реле в памяти."""
        if name in self._relays:
            self._relays[name] = state

    def get_relay(self, name: str) -> bool:
        """Возвращает текущее состояние реле."""
        return self._relays.get(name, False)
