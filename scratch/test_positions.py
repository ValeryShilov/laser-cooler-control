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
    "comp_1":       (210, 320),
    "cond_1":       (210, 130),
    "fan_1":        (155, 130),
    "throttle_1":   (350, 30),
    "valve_bp":     (320, 230),
    "tank_1":       (510, 260),
    "pump_1":       (650, 320),
    "heater_1":     (750, 200),
    "ext_laser_in": (870, 60),
    "ext_optics_in":(870, 120),
    "ext_optics_out":(870, 200),
    "ext_laser_out":(870, 320),
    "ext_drain":    (870, 400),
}
for cid, (rx, ry) in ref.items():
    if cid in components:
        comp = components[cid]
        cx = comp.x + comp.width / 2
        cy = comp.y + comp.height / 2
        dx = cx - rx
        dy = cy - ry
        print(f"  {cid:20s}  ref=({rx:5.0f}, {ry:5.0f})  actual=({cx:5.0f}, {cy:5.0f})  delta=({dx:+5.0f}, {dy:+5.0f})")
