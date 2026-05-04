"""
Абстрактный адаптер оборудования (HAL).

Определяет интерфейс общения с физическим железом.
Конкретные реализации: MockAdapter (заглушка), в будущем PicoAdapter.
"""
from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """Интерфейс для взаимодействия с оборудованием чиллера."""

    @abstractmethod
    def read_sensors(self) -> dict:
        """Считывает показания всех датчиков.
        
        Returns:
            dict с ключами: temp_lt, temp_ht, temp_ambient,
            flow_lt, flow_ht, pressure, water_level
        """

    @abstractmethod
    def set_relay(self, name: str, state: bool):
        """Управляет реле.
        
        Args:
            name: 'pump', 'compressor', 'heater', 'valve', 'fan'
            state: True = включить, False = выключить
        """
