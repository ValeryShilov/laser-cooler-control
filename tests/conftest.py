import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

@pytest.fixture
def mock_components_snapshot():
    """Возвращает мок 'снимка' компонентов (как тот, что генерирует make_comp_snapshot)."""
    return {
        "tank": {
            "id": "tank",
            "class_name": "Tank",
            "x": 400, "y": 150,
            "width": 120, "height": 200,
            "ports": {
                "freon_out": (400, 340),
                "water_lt_in": (490, 130)
            }
        },
        "pump": {
            "id": "pump",
            "class_name": "Pump",
            "x": 600, "y": 300,
            "width": 50, "height": 50,
            "ports": {
                "in": (600, 330),
                "out": (650, 330)
            }
        },
        "port_in": {
            "id": "port_in",
            "class_name": "ExternalPort",
            "x": 800, "y": 130,
            "width": 150, "height": 30,
            "ports": {
                "in": (800, 150),
                "out": (800, 150)
            }
        }
    }
