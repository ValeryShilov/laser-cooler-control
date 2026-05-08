import os
import sys
import json
import pytest
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")



import logging

# Настройка логгера для тестов
test_logger = logging.getLogger("test_journal")
test_logger.setLevel(logging.INFO)

os.makedirs(REPORTS_DIR, exist_ok=True)
log_file = os.path.join(REPORTS_DIR, "test_journal.log")
fh = logging.FileHandler(log_file, mode='w', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
test_logger.addHandler(fh)

class TestLog:
    """Журнал проверок одного теста."""

    def __init__(self, node_id, node_name):
        self.node_id = node_id
        self.node_name = node_name
        test_logger.info("=== START TEST: %s ===", self.node_name)

    def check(self, description, actual, expected, op="eq", **kwargs):
        """Записать проверку и выполнить assertion."""
        passed = False
        actual_str = repr(actual)
        expected_str = repr(expected)

        if op == "eq":
            passed = actual == expected
        elif op == "is":
            passed = actual is expected
            expected_str = f"is {repr(expected)}"
        elif op == "ne":
            passed = actual != expected
            expected_str = f"≠ {repr(expected)}"
        elif op == "gt":
            passed = actual > expected
            expected_str = f"> {repr(expected)}"
        elif op == "lt":
            passed = actual < expected
            expected_str = f"< {repr(expected)}"
        elif op == "ge":
            passed = actual >= expected
            expected_str = f">= {repr(expected)}"
        elif op == "le":
            passed = actual <= expected
            expected_str = f"<= {repr(expected)}"
        elif op == "in":
            passed = actual in expected
            expected_str = f"содержится в {repr(expected)}"
        elif op == "not_in":
            passed = actual not in expected
            expected_str = f"не содержится в {repr(expected)}"
        elif op == "approx":
            tolerance = kwargs.get("abs", 1)
            passed = builtins_abs(actual - expected) <= tolerance
            expected_str = f"{repr(expected)} ± {tolerance}"

        if passed:
            test_logger.info("[PASSED] %s: %s (Ожидалось: %s)", description, actual_str, expected_str)
        else:
            test_logger.error("[FAILED] %s: получено %s, ожидалось %s", description, actual_str, expected_str)

        assert passed, f"{description}: ожидалось {expected_str}, получено {actual_str}"

    def finish(self):
        test_logger.info("=== END TEST: %s ===\n", self.node_name)

# Нужен доступ к встроенному abs, чтобы не конфликтовать с kwarg 'abs'
import builtins
builtins_abs = builtins.abs

@pytest.fixture
def test_log(request):
    """Фикстура журнала. Каждый тест получает свой экземпляр TestLog."""
    log = TestLog(request.node.nodeid, request.node.name)
    yield log
    log.finish()

def pytest_sessionfinish(session, exitstatus):
    print(f"\n\n[OK] Журнал тестирования сохранён: {log_file}")

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
