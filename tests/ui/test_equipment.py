import pytest
from PySide6.QtCore import QRectF
from ui.equipment import BaseEquipment, Tank, Pump, Compressor, ExternalPort

# Note: Some QApplication-dependent initialization is typically required for GUI classes,
# but our equipment classes mostly use QRectF, string, and dict manipulation.
# If SVGRenderer complains, we might need a dummy QApplication, but let's test the geometry first.

def test_base_equipment_rect():
    eq = BaseEquipment(10, 20, 100, 50, "TestEq")
    rect = eq.get_rect()
    assert rect == QRectF(10, 20, 100, 50)
    assert eq.state == "off"

def test_tank_ports_update():
    tank = Tank(100, 100)
    
    # Check initial positions after update
    tank.update_ports()
    assert "freon_out" in tank.ports
    assert "water_out" in tank.ports
    
    # Move tank
    tank.x = 200
    tank.y = 200
    tank.update_ports()
    
    # Verify ports moved with the tank
    # Freon out is at (x, y + height - 10)
    # Height of tank is 200 by default
    assert tank.ports["freon_out"] == (200, 200 + 190)
    assert tank.ports["water_lt_in"] == (200 + 90, 200)
    assert tank.ports["water_ht_in"] == (200 + 30, 200)
    assert tank.ports["water_out"] == (200 + 120, 200 + 160)
    assert tank.ports["drain"] == (200 + 60, 200 + 200)

def test_pump_ports_update():
    pump = Pump(0, 0)
    pump.x = 100
    pump.y = 100
    pump.update_ports()
    
    # Pump width/height is 50/50
    assert pump.ports["in"] == (100, 100 + 30)
    assert pump.ports["out"] == (100 + 50, 100 + 30)

def test_external_port_label_pos():
    port = ExternalPort(0, 0, "Test Label")
    assert port.label_pos == "bottom"
    
    port.x = 50
    port.y = 50
    port.update_ports()
    # External ports usually have 'in' and 'out' exactly at their coordinates
    assert port.ports["in"] == (50, 50 + 20)
    assert port.ports["out"] == (50, 50 + 20)
