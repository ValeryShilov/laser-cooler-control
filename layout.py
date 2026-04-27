from rules import LAYOUT_RULES, PORT_ORDER

class RuleBasedLayoutEngine:
    def __init__(self, padding=80):
        self.width = 1000
        self.height = 600
        self.padding = padding

    def layout(self, components):
        other_comps = []
        ext_ports = []
        
        for comp in components.values():
            if type(comp).__name__ == "ExternalPort":
                ext_ports.append(comp)
            else:
                other_comps.append(comp)

        safe_w = self.width - (self.padding * 2)
        safe_h = self.height - (self.padding * 2)

        for comp in other_comps:
            ctype = type(comp).__name__
            rule = LAYOUT_RULES.get(ctype, {"x_pct": 0.5, "y_pct": 0.5})
            
            raw_x = self.padding + (safe_w * rule["x_pct"]) - (comp.width / 2)
            raw_y = self.padding + (safe_h * rule["y_pct"]) - (comp.height / 2)
            
            # ЖЕСТКАЯ ПРИВЯЗКА АГРЕГАТОВ К СЕТКЕ 10px
            comp.x = round(raw_x / 10) * 10
            comp.y = round(raw_y / 10) * 10
            comp.update_ports()

        if ext_ports:
            ext_ports.sort(key=lambda p: PORT_ORDER.index(p.id) if p.id in PORT_ORDER else 99)
            x_pos = self.padding + (safe_w * LAYOUT_RULES["ExternalPort"]["x_pct"])
            step_y = safe_h / (len(ext_ports) + 1)
            
            for i, port in enumerate(ext_ports):
                raw_y = self.padding + (step_y * (i + 1)) - (port.height / 2)
                
                port.x = round((x_pos - (port.width / 2)) / 10) * 10
                port.y = round(raw_y / 10) * 10
                port.update_ports()