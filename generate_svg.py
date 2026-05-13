import sys
import os
from PySide6.QtWidgets import QApplication

# 1. Шаблоны

svg_heater = """<svg viewBox="0 0 40 40" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="5" width="36" height="30" fill="none" stroke="{color}" stroke-width="3"/>
    <line x1="12" y1="5" x2="12" y2="35" stroke="{color}" stroke-width="3"/>
    <line x1="20" y1="5" x2="20" y2="35" stroke="{color}" stroke-width="3"/>
    <line x1="28" y1="5" x2="28" y2="35" stroke="{color}" stroke-width="3"/></svg>"""

svg_condenser = """<svg viewBox="0 0 60 160" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <polygon points="30,2 58,80 30,158 2,80" fill="none" stroke="{color}" stroke-width="2"/>
    <polyline points="15,80 25,55 35,105 45,80" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>
    <line x1="45" y1="38" x2="55" y2="12" stroke="{color}" stroke-width="2"/>
    <polygon points="55,12 48,14 51,22" fill="{color}"/></svg>"""

svg_tank_evap = """<svg viewBox="0 0 60 60" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <polyline points="2,1 2,59 58,59 58,1" fill="none" stroke="#37474F" stroke-width="3"/>
    <polyline points="15,10 40,22 15,38 40,50" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round"/></svg>"""

svg_throttle = """<svg viewBox="0 0 60 40" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <polygon points="2,3 2,37 30,20" fill="{color}" stroke="{color}" stroke-width="2"/>
    <polygon points="58,3 58,37 30,20" fill="{color}" stroke="{color}" stroke-width="2"/>
    <line x1="15" y1="35" x2="45" y2="5" stroke="#37474F" stroke-width="2"/>
    <polygon points="45,5 38,6 41,13" fill="#37474F"/></svg>"""

svg_pump = """<svg viewBox="0 0 60 60" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="30" cy="30" r="27" stroke="#37474F" stroke-width="3" fill="none"/>
    <polygon points="15,15 15,45 48,30" fill="{color}"/></svg>"""

svg_compressor = """<svg viewBox="0 0 60 60" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="30" cy="30" r="26" stroke="{color}" stroke-width="3" fill="none"/>
    <polygon points="16,18 16,42 46,30" fill="none" stroke="{color}" stroke-width="3"/></svg>"""

svg_fan = """<svg viewBox="0 0 40 40" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="20" cy="20" r="18" stroke="#37474F" stroke-width="3" fill="none"/>
    <g stroke="{color}" stroke-width="3" stroke-linecap="round">
        <line x1="20" y1="5" x2="20" y2="35" />
        <line x1="5" y1="20" x2="35" y2="20" />
        <line x1="9" y1="9" x2="31" y2="31" />
        <line x1="9" y1="31" x2="31" y2="9" />
    </g>
    <circle cx="20" cy="20" r="4" fill="#37474F"/></svg>"""

svg_valve = """<svg viewBox="0 0 60 40" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <polygon points="2,17 2,37 30,27" fill="{color}" stroke="#37474F" stroke-width="2"/>
    <polygon points="58,17 58,37 30,27" fill="{color}" stroke="#37474F" stroke-width="2"/>
    <rect x="20" y="0" width="20" height="14" fill="none" stroke="#37474F" stroke-width="2"/>
    <line x1="20" y1="14" x2="40" y2="0" stroke="#37474F" stroke-width="2"/>
    <line x1="30" y1="14" x2="30" y2="27" stroke="#37474F" stroke-width="2"/></svg>"""


elements = [
    ("heater", svg_heater),
    ("condenser", svg_condenser),
    ("tank_evap", svg_tank_evap),
    ("throttle", svg_throttle),
    ("pump", svg_pump),
    ("compressor", svg_compressor),
    ("fan", svg_fan),
    ("valve", svg_valve)
]

STATES = {"off": "#B0BEC5", "on": "#4CAF50", "err": "#F44336"}

def export_files():
    folder_name = "svg_icons"
    os.makedirs(folder_name, exist_ok=True)
    for element_id, template in elements:
        for state_name, hex_color in STATES.items():
            final_svg = template.format(color=hex_color)
            filepath = os.path.join(folder_name, f"{element_id}_{state_name}.svg")
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(final_svg)
    print("OK - Все файлы успешно созданы!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    export_files()