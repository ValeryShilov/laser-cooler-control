"""
Модели данных системы чиллера.

Содержит структуры для передачи состояний между слоями
(controller → UI).
"""
from dataclasses import dataclass, field
from enum import Enum


class SystemMode(Enum):
    OFF = "off"
    AUTO = "auto"
    MANUAL = "manual"


@dataclass(frozen=True)
class SystemState:
    """Неизменяемый снимок состояния системы."""
    mode: SystemMode = SystemMode.OFF
    heater_on: bool = False
    valve_open: bool = False

    # Показания датчиков (заполняются адаптером)
    temp_lt: float = 25.0
    temp_ht: float = 30.0
    temp_ambient: float = 24.1
    flow_lt: float = 0.0
    flow_ht: float = 0.0
    pressure: float = 0.0
    water_level: float = 0.85


@dataclass
class RenderData:
    """Результат фоновых вычислений (routing + label placement).
    
    Передаётся из SchemeWorker → ChillerMnemonic через сигнал.
    paintEvent использует эти данные без пересчёта.
    """
    pipe_paths: list = field(default_factory=list)      # [(points_list, conn_type), ...]
    label_positions: dict = field(default_factory=dict)  # {comp_id: "bottom"|"top"|...}
    obstacles: list = field(default_factory=list)        # [(x1, y1, x2, y2), ...] для debug отрисовки
    generation: int = 0                                  # Для отсеивания устаревших результатов
