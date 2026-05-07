import os
import sys
import json
import pytest
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")


class TestLog:
    """Журнал проверок одного теста."""

    def __init__(self, node_id, node_name):
        self.node_id = node_id
        self.node_name = node_name
        self.checks = []
        self.status = "PASSED"

    def check(self, description, actual, expected, op="eq", **kwargs):
        """Записать проверку и выполнить assertion.

        Args:
            description: Что проверяется (человекочитаемый текст).
            actual: Фактическое значение.
            expected: Ожидаемое значение.
            op: Оператор сравнения:
                'eq'     — actual == expected
                'ne'     — actual != expected
                'gt'     — actual > expected
                'lt'     — actual < expected
                'ge'     — actual >= expected
                'is'     — actual is expected
                'in'     — actual in expected
                'not_in' — actual not in expected
                'approx' — |actual - expected| <= abs (передайте abs=...)
        """
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

        self.checks.append({
            "description": description,
            "expected": expected_str,
            "actual": actual_str,
            "passed": passed,
        })

        if not passed:
            self.status = "FAILED"

        assert passed, f"{description}: ожидалось {expected_str}, получено {actual_str}"

    def to_dict(self):
        return {
            "test_id": self.node_id,
            "test_name": self.node_name,
            "status": self.status,
            "checks": self.checks,
        }


# Нужен доступ к встроенному abs, чтобы не конфликтовать с kwarg 'abs'
import builtins
builtins_abs = builtins.abs

# Глобальное хранилище результатов за сессию
_all_test_logs = []


@pytest.fixture
def test_log(request):
    """Фикстура журнала. Каждый тест получает свой экземпляр TestLog."""
    log = TestLog(request.node.nodeid, request.node.name)
    yield log
    _all_test_logs.append(log.to_dict())


def pytest_sessionfinish(session, exitstatus):
    """Хук: вызывается после завершения всех тестов. Сохраняет журнал в JSON."""
    if not _all_test_logs:
        return

    os.makedirs(REPORTS_DIR, exist_ok=True)

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(_all_test_logs),
        "passed": sum(1 for t in _all_test_logs if t["status"] == "PASSED"),
        "failed": sum(1 for t in _all_test_logs if t["status"] != "PASSED"),
        "tests": _all_test_logs,
    }

    report_path = os.path.join(REPORTS_DIR, "test_journal.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n\n[OK] Журнал тестирования сохранён: {report_path}")


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
