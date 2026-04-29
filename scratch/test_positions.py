"""
Тестовый скрипт: проверяет результаты нового движка компоновки.
Выводит позиции всех компонентов после layout().
"""
import sys, os
# Add parent dir to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)

from parser import SchemeParser
from layout import TopologyLayoutEngine

parser = SchemeParser("scheme.yaml")
components, connections = parser.parse()

engine = TopologyLayoutEngine(padding=80)
engine.width = 1000
engine.height = 500    # Тот же viewport, что и у SVG-эталона
engine.layout(components, connections)

print("=== Component positions (width=1000, height=500) ===")
for cid, comp in components.items():
    cx = comp.x + comp.width / 2
    cy = comp.y + comp.height / 2
    ctype = type(comp).__name__
    print(f"  {cid:20s}  type={ctype:14s}  pos=({comp.x:5.0f}, {comp.y:5.0f})  center=({cx:5.0f}, {cy:5.0f})  size={comp.width}x{comp.height}")

print("\n=== Reference SVG centers (with 120px x-offset) ===")
ref = {
    "compressor_main":       (210, 320),
    "condenser_unit":       (210, 130),
    "fan_cooling":        (155, 130),
    "throttle":   (350, 30),
    "valve_bypass":     (320, 230),
    "tank_evaporator":       (510, 260),
    "pump_circulating":       (650, 320),
    "heater_optics":     (750, 200),
    "port_laser_in": (870, 60),
    "port_optics_in":(870, 120),
    "port_optics_out":(870, 200),
    "port_laser_out":(870, 320),
    "port_drain_system":    (870, 400),
}
for cid, (rx, ry) in ref.items():
    if cid in components:
        comp = components[cid]
        cx = comp.x + comp.width / 2
        cy = comp.y + comp.height / 2
        dx = cx - rx
        dy = cy - ry
        print(f"  {cid:20s}  ref=({rx:5.0f}, {ry:5.0f})  actual=({cx:5.0f}, {cy:5.0f})  delta=({dx:+5.0f}, {dy:+5.0f})")
