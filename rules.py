LAYOUT_RULES = {
    "Compressor":   {"x_pct": 0.15, "y_pct": 0.85},
    "Condenser":    {"x_pct": 0.15, "y_pct": 0.35},
    "Fan":          {"x_pct": 0.08, "y_pct": 0.35}, 
    "Throttle":     {"x_pct": 0.35, "y_pct": 0.00},
    "Valve":        {"x_pct": 0.35, "y_pct": 0.65},
    "Tank":         {"x_pct": 0.50, "y_pct": 0.50},
    "Pump":         {"x_pct": 0.65, "y_pct": 0.85},
    "Heater":       {"x_pct": 0.75, "y_pct": 0.40},
    "ExternalPort": {"x_pct": 0.95, "y_pct": "auto"}
}

# Строгий порядок для внешних штуцеров сверху вниз
PORT_ORDER = [
    "ext_laser_in",   # Вход L
    "ext_optics_in",  # Вход H
    "ext_optics_out", # Выход H
    "ext_laser_out",  # Выход L
    "ext_drain"       # Слив
]

ROUTING_RULES = {
    ("tank_1.freon_out", "comp_1.in"): [(0.50, 0.95), (0.15, 0.95)],
    ("comp_1.out", "valve_bp.in"): [(0.25, 0.85), (0.25, 0.65)]
}