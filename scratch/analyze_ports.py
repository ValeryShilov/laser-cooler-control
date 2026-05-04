"""
Анализ несоответствий между SVG viewBox и размерами компонентов.
Показывает где визуальный контент SVG не совпадает с позициями портов.
"""

components = {
    'Compressor': {'vb': (60,60), 'size': (60,60), 'par': 'default'},
    'Condenser':  {'vb': (60,60), 'size': (60,160), 'par': 'default'},
    'Fan':        {'vb': (60,60), 'size': (40,40), 'par': 'default'},
    'Throttle':   {'vb': (60,60), 'size': (60,40), 'par': 'default'},
    'Valve':      {'vb': (60,60), 'size': (60,40), 'par': 'default'},
    'Pump':       {'vb': (60,60), 'size': (50,50), 'par': 'default'},
    'Heater':     {'vb': (60,60), 'size': (40,80), 'par': 'default'},
    'Tank':       {'vb': (60,60), 'size': (100,200), 'par': 'none'},
}

print("=== SVG viewBox vs Component Size ===\n")
for name, info in components.items():
    vw, vh = info['vb']
    cw, ch = info['size']
    par = info['par']
    
    if par == 'none':
        print(f"  {name}: {vw}x{vh} -> {cw}x{ch} (stretched, no issues)")
        continue
    
    scale = min(cw/vw, ch/vh)
    rw = vw * scale
    rh = vh * scale
    xoff = (cw - rw) / 2
    yoff = (ch - rh) / 2
    
    if xoff > 2 or yoff > 2:
        print(f"  {name}: {vw}x{vh} -> {cw}x{ch}  *** MISMATCH ***")
        print(f"    scale={scale:.3f}, visual area: ({xoff:.0f},{yoff:.0f})-({xoff+rw:.0f},{yoff+rh:.0f})")
        print(f"    x-offset={xoff:.0f}px, y-offset={yoff:.0f}px")
    else:
        print(f"  {name}: {vw}x{vh} -> {cw}x{ch}  OK (scale={scale:.3f})")

print("\n=== Detailed Port Analysis ===\n")

# Condenser
print("CONDENSER (60x60 viewBox -> 60x160 component):")
scale = min(60/60, 160/60)  # = 1.0
yoff = (160 - 60) / 2  # = 50
print(f"  SVG content rendered at y=[{yoff:.0f}..{yoff+60:.0f}] within [0..160]")
print(f"  Port 'in'  defined at y=160 (bottom) -> {160-yoff-60:.0f}px BELOW visual content!")
print(f"  Port 'out' defined at y=0   (top)    -> {yoff:.0f}px ABOVE visual content!")
print(f"  FIX NEEDED: ports should be at y={yoff:.0f} and y={yoff+60:.0f}")
print()

# Throttle  
print("THROTTLE (60x60 viewBox -> 60x40 component):")
scale = min(60/60, 40/60)  # = 0.667
xoff = (60 - 60*scale) / 2  # = 10
yoff = 0
svg_center_y = 30 * scale + yoff
svg_left_x = 10 * scale + xoff
svg_right_x = 50 * scale + xoff
print(f"  Scale={scale:.3f}, x-offset={xoff:.0f}px")
print(f"  SVG triangle tips: left at x={svg_left_x:.1f}, right at x={svg_right_x:.1f}")
print(f"  SVG center y = {svg_center_y:.1f}")
print(f"  Port 'in'  at x=0  -> {svg_left_x:.1f}px gap from visual left tip")
print(f"  Port 'out' at x=60 -> {60-svg_right_x:.1f}px gap from visual right tip")
print(f"  Port y=20, visual center y={svg_center_y:.1f} -> OK")
print()

# Valve
print("VALVE (60x60 viewBox -> 60x40 component):")
print(f"  Same scale as Throttle, same x-offset issues")
svg_valve_center_y = 40 * scale  # triangle meeting point at y=40 in SVG
print(f"  SVG triangle center at y={svg_valve_center_y:.1f}, port at y=20 -> {abs(20-svg_valve_center_y):.1f}px gap")
print()

# Heater
print("HEATER (60x60 viewBox -> 40x80 component):")
scale_h = min(40/60, 80/60)  # = 0.667
xoff_h = (40 - 60*scale_h) / 2  # = 0
yoff_h = (80 - 60*scale_h) / 2  # = 20
svg_center_y = 30 * scale_h + yoff_h
svg_left_x = 10 * scale_h + xoff_h
svg_right_x = 50 * scale_h + xoff_h
print(f"  Scale={scale_h:.3f}, y-offset={yoff_h:.0f}px")
print(f"  SVG rect center y = {svg_center_y:.1f}, port y=40 -> OK")
print(f"  SVG left edge x={svg_left_x:.1f}, port 'in' at x=0 -> {svg_left_x:.1f}px gap")
print(f"  SVG right edge x={svg_right_x:.1f}, port 'out' at x=40 -> {40-svg_right_x:.1f}px gap")
print()

# Pump
print("PUMP (60x60 viewBox -> 50x50 component):")
scale_p = min(50/60, 50/60)  # = 0.833
circle_left = (30-26) * scale_p  # center-radius mapped
circle_right = (30+26) * scale_p
print(f"  Scale={scale_p:.3f}")
print(f"  Circle left edge at x={circle_left:.1f}, port 'in' at x=0 -> {circle_left:.1f}px gap")
print(f"  Circle right edge at x={circle_right:.1f}, port 'out' at x=50 -> {50-circle_right:.1f}px gap")

print("\n\n=== SUMMARY: Components needing fixes ===")
print("1. CONDENSER: CRITICAL - 50px offset on ports (top and bottom)")
print("2. THROTTLE:  MODERATE - 17px x-offset on both sides")
print("3. VALVE:     MODERATE - 17px x-offset + 7px y-offset")
print("4. HEATER:    MINOR   - 7px x-offset on both sides")
print("5. PUMP:      MINOR   - 3px gap on both sides")
