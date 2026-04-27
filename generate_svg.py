import sys
import os
from PySide6.QtWidgets import QApplication

# 1. Шаблоны
svg_heater = """<svg viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
    <rect x="10" y="20" width="40" height="20" fill="none" stroke="{color}" stroke-width="3"/>
    <line x1="20" y1="20" x2="20" y2="40" stroke="{color}" stroke-width="3"/>
    <line x1="30" y1="20" x2="30" y2="40" stroke="{color}" stroke-width="3"/>
    <line x1="40" y1="20" x2="40" y2="40" stroke="{color}" stroke-width="3"/></svg>"""

svg_condenser = """<svg viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
    <polygon points="30,5 55,30 30,55 5,30" fill="none" stroke="{color}" stroke-width="2"/>
    <polyline points="15,30 25,20 35,40 45,30" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>
    <line x1="45" y1="15" x2="55" y2="5" stroke="{color}" stroke-width="2"/>
    <polygon points="55,5 48,5 53,10" fill="{color}"/></svg>"""

# Добавлено preserveAspectRatio="none" для бака
svg_tank_evap = """<svg viewBox="0 0 60 60" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <polyline points="15,5 15,55 45,55 45,5" fill="none" stroke="#37474F" stroke-width="3"/>
    <polyline points="20,10 40,20 20,35 40,45" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round"/></svg>"""

svg_throttle = """<svg viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
    <polygon points="10,20 10,40 30,30" fill="{color}" stroke="{color}" stroke-width="2"/>
    <polygon points="50,20 50,40 30,30" fill="{color}" stroke="{color}" stroke-width="2"/>
    <line x1="15" y1="50" x2="45" y2="10" stroke="#37474F" stroke-width="2"/>
    <polygon points="45,10 38,10 42,15" fill="#37474F"/></svg>"""

svg_pump = """<svg viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
    <circle cx="30" cy="30" r="26" stroke="#37474F" stroke-width="3" fill="none"/>
    <polygon points="16,18 16,42 46,30" fill="{color}"/></svg>"""

svg_compressor = """<svg viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
    <circle cx="30" cy="30" r="26" stroke="{color}" stroke-width="3" fill="none"/>
    <polygon points="16,18 16,42 46,30" fill="none" stroke="{color}" stroke-width="3"/></svg>"""

# ДОБАВЛЕНО: Вентилятор
svg_fan = """<svg viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
    <circle cx="30" cy="30" r="26" stroke="#37474F" stroke-width="3" fill="none"/>
    <g stroke="{color}" stroke-width="4" stroke-linecap="round">
        <line x1="30" y1="10" x2="30" y2="50" />
        <line x1="10" y1="30" x2="50" y2="30" />
        <line x1="16" y1="16" x2="44" y2="44" />
        <line x1="16" y1="44" x2="44" y2="16" />
    </g>
    <circle cx="30" cy="30" r="6" fill="#37474F"/></svg>"""

# ДОБАВЛЕНО: Клапан
svg_valve = """<svg viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
    <polygon points="10,25 10,55 30,40" fill="{color}" stroke="#37474F" stroke-width="2"/>
    <polygon points="50,25 50,55 30,40" fill="{color}" stroke="#37474F" stroke-width="2"/>
    <rect x="20" y="5" width="20" height="20" fill="none" stroke="#37474F" stroke-width="2"/>
    <line x1="20" y1="25" x2="40" y2="5" stroke="#37474F" stroke-width="2"/>
    <line x1="30" y1="25" x2="30" y2="40" stroke="#37474F" stroke-width="2"/></svg>"""

# Исправленный список (теперь тут все 8)
elements = [
    ("heater", svg_heater),
    ("condenser", svg_condenser),
    ("tank_evap", svg_tank_evap),
    ("throttle", svg_throttle),
    ("pump", svg_pump),
    ("compressor", svg_compressor),
    ("fan", svg_fan),      # <-- добавлено
    ("valve", svg_valve)   # <-- добавлено
]

STATES = {"off": "#B0BEC5", "on": "#4CAF50", "err": "#F44336"}

def export_files():
    folder_name = "svg_icons" # Убедитесь, что имя папки совпадает с тем, что в вашем основном коде
    os.makedirs(folder_name, exist_ok=True)
    for element_id, template in elements:
        for state_name, hex_color in STATES.items():
            final_svg = template.format(color=hex_color)
            filepath = os.path.join(folder_name, f"{element_id}_{state_name}.svg")
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(final_svg)
    print("✅ Все файлы (включая вентилятор и клапан) успешно созданы!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    export_files()