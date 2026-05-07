from PySide6.QtCore import QRectF
from ui.equipment import BaseEquipment, Tank, Pump, Compressor, ExternalPort

def test_base_equipment_rect(test_log):
    eq = BaseEquipment(10, 20, 100, 50, "TestEq")
    rect = eq.get_rect()
    test_log.check("Прямоугольник компонента", rect, QRectF(10, 20, 100, 50))
    test_log.check("Начальное состояние", eq.state, "off")

def test_tank_ports_update(test_log):
    tank = Tank(100, 100)
    tank.update_ports()
    test_log.check("Порт freon_out существует", "freon_out" in tank.ports, True, op="is")
    test_log.check("Порт water_out существует", "water_out" in tank.ports, True, op="is")

    tank.x = 200
    tank.y = 200
    tank.update_ports()

    test_log.check("freon_out после сдвига", tank.ports["freon_out"], (200, 200 + 190))
    test_log.check("water_lt_in после сдвига", tank.ports["water_lt_in"], (200 + 90, 200))
    test_log.check("water_ht_in после сдвига", tank.ports["water_ht_in"], (200 + 30, 200))
    test_log.check("water_out после сдвига", tank.ports["water_out"], (200 + 120, 200 + 160))
    test_log.check("drain после сдвига", tank.ports["drain"], (200 + 60, 200 + 200))

def test_pump_ports_update(test_log):
    pump = Pump(0, 0)
    pump.x = 100
    pump.y = 100
    pump.update_ports()

    test_log.check("Порт in насоса", pump.ports["in"], (100, 100 + 30))
    test_log.check("Порт out насоса", pump.ports["out"], (100 + 50, 100 + 30))

def test_external_port_label_pos(test_log):
    port = ExternalPort(0, 0, "Test Label")
    test_log.check("Позиция надписи", port.label_pos, "bottom")

    port.x = 50
    port.y = 50
    port.update_ports()
    test_log.check("Порт in внешнего штуцера", port.ports["in"], (50, 50 + 20))
    test_log.check("Порт out внешнего штуцера", port.ports["out"], (50, 50 + 20))
