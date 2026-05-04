from collections import defaultdict
from rules import PORT_ORDER


class TopologyLayoutEngine:
    def __init__(self, padding=50):
        self.width = 1000
        self.height = 600
        self.padding = padding
        self.pad_left = padding
        self.pad_right = padding
        self.pad_top = 80
        self.pad_bottom = padding

    def layout(self, components, connections):
        main_comps = {}
        ext_ports = []
        for cid, comp in components.items():
            if type(comp).__name__ == "ExternalPort":
                ext_ports.append(comp)
            else:
                main_comps[cid] = comp

        safe_w = self.width - self.pad_left - self.pad_right
        safe_h = self.height - self.pad_top - self.pad_bottom

        # ── Построить граф фреонового контура и механические связи ──
        freon_adj = defaultdict(list)
        mechanical_links = {}          # src → tgt

        for conn in connections:
            src, tgt = conn['source_id'], conn['target_id']
            ctype = conn['type']
            if src in main_comps and tgt in main_comps:
                if ctype == 'freon':
                    freon_adj[src].append(tgt)
                elif ctype == 'mechanical':
                    mechanical_links[src] = tgt

        positioned = set()

        # ── 1. Найти замкнутый фреоновый цикл и расставить его ──
        cycle = self._find_cycle(freon_adj, set(main_comps.keys()))
        if cycle:
            pts = self._cycle_rect_positions(len(cycle))
            for i, cid in enumerate(cycle):
                self._place(main_comps[cid], pts[i][0], pts[i][1], safe_w, safe_h)
                positioned.add(cid)

        # ── 2. Механические связи (вентилятор слева от конденсатора) ──
        for src_id, tgt_id in mechanical_links.items():
            if src_id not in positioned and tgt_id in positioned and src_id in main_comps:
                partner = main_comps[tgt_id]
                comp = main_comps[src_id]
                comp.x = round((partner.x - comp.width - 10) / 10) * 10
                comp.y = round((partner.y + (partner.height - comp.height) / 2) / 10) * 10
                comp.update_ports()
                # Проверяем коллизию и сдвигаем при необходимости
                self._nudge_to_free(comp, main_comps, positioned, src_id)
                positioned.add(src_id)

        # ── 3. Байпас (freon_bypass) ──
        bypass_placed = set()
        for conn in connections:
            if conn['type'] != 'freon_bypass':
                continue
            src, tgt = conn['source_id'], conn['target_id']
            # Определяем, какой из двух ещё не размещён
            if src in positioned and tgt not in positioned and tgt in main_comps:
                unplaced_id, anchor = tgt, main_comps[src]
            elif tgt in positioned and src not in positioned and src in main_comps:
                unplaced_id, anchor = src, main_comps[tgt]
            else:
                continue
            if unplaced_id in positioned or unplaced_id in bypass_placed:
                continue
            self._place_bypass(main_comps[unplaced_id], anchor, cycle, main_comps, safe_w, safe_h)
            # Проверяем коллизию
            self._nudge_to_free(main_comps[unplaced_id], main_comps, positioned, unplaced_id)
            positioned.add(unplaced_id)
            bypass_placed.add(unplaced_id)

        # ── 4. Водяной контур (BFS от уже расставленных) ──
        changed = True
        while changed:
            changed = False
            for conn in connections:
                src, tgt = conn['source_id'], conn['target_id']
                ctype = conn['type']
                if ctype not in ('water_lt', 'water_ht', 'drain'):
                    continue
                if src in positioned and tgt not in positioned and tgt in main_comps:
                    self._place_downstream(main_comps[tgt], main_comps[src], ctype, safe_w, safe_h)
                    self._nudge_to_free(main_comps[tgt], main_comps, positioned, tgt)
                    positioned.add(tgt)
                    changed = True
                elif tgt in positioned and src not in positioned and src in main_comps:
                    self._place_downstream(main_comps[src], main_comps[tgt], ctype, safe_w, safe_h)
                    self._nudge_to_free(main_comps[src], main_comps, positioned, src)
                    positioned.add(src)
                    changed = True

        # ── 5. Остаток — размещение рядом с ближайшим однотипным компонентом ──
        for cid in main_comps:
            if cid not in positioned:
                comp = main_comps[cid]
                placed_near = False

                # Ищем уже размещённый компонент того же класса
                comp_class = type(comp).__name__
                for pid in positioned:
                    if type(main_comps[pid]).__name__ == comp_class:
                        buddy = main_comps[pid]
                        # Размещаем правее и чуть ниже компаньона
                        comp.x = round((buddy.x + buddy.width + 20) / 10) * 10
                        comp.y = round(buddy.y / 10) * 10
                        comp.update_ports()
                        self._nudge_to_free(comp, main_comps, positioned, cid)
                        placed_near = True
                        break

                if not placed_near:
                    # Нет однотипного — размещаем в свободной зоне справа
                    self._place(comp, 0.60, 0.50, safe_w, safe_h)
                    self._nudge_to_free(comp, main_comps, positioned, cid)

                positioned.add(cid)

        # ── 6. Внешние порты ──
        if ext_ports:
            ext_ports.sort(key=lambda p: PORT_ORDER.index(p.id) if p.id in PORT_ORDER else 99)
            
            # Размещаем внешние порты на фиксированном расстоянии от самого правого компонента
            max_comp_x = max([c.x + c.width for c in main_comps.values()]) if main_comps else 700
            x_pos = max_comp_x + 120  
            
            # Найдём к чему подключены внешние порты для выравнивания Y
            aligned_y = {}
            for conn in connections:
                src, tgt = conn['source_id'], conn['target_id']
                src_port = conn.get('source_port', 'out')
                if tgt in [p.id for p in ext_ports] and src in main_comps:
                    comp = main_comps[src]
                    if src_port in comp.ports:
                        y_pos = comp.ports[src_port][1]
                        # Если порт смотрит вниз (слив), труба сначала опускается на 30px
                        if src_port == 'drain':
                            y_pos += 30
                        aligned_y[tgt] = y_pos

            default_start_y = self.pad_top
            for port in ext_ports:
                port.x = round((x_pos - port.width / 2) / 10) * 10
                
                if port.id in aligned_y:
                    # Выравниваем так, чтобы port.ports['in'][1] совпадал с aligned_y
                    # port.y + 20 = aligned_y -> port.y = aligned_y - 20
                    port.y = round((aligned_y[port.id] - 20) / 10) * 10
                else:
                    port.y = round(default_start_y / 10) * 10
                    default_start_y += 60
                    
                port.update_ports()

    #  Вспомогательные методы
    def _place(self, comp, x_pct, y_pct, safe_w, safe_h):
        """Разместить компонент по процентным координатам безопасной зоны."""
        comp.x = round((self.padding + safe_w * x_pct - comp.width / 2) / 10) * 10
        comp.y = round((self.padding + safe_h * y_pct - comp.height / 2) / 10) * 10
        comp.update_ports()

    # ── Обнаружение и разрешение коллизий ──

    def _rects_overlap(self, r1, r2, padding=15):
        """Проверяет пересечение двух прямоугольников (x, y, w, h) с отступом."""
        x1, y1, w1, h1 = r1
        x2, y2, w2, h2 = r2
        return not (x1 + w1 + padding <= x2 or x2 + w2 + padding <= x1 or
                    y1 + h1 + padding <= y2 or y2 + h2 + padding <= y1)

    def _overlaps_any(self, comp, main_comps, positioned, exclude_id=None):
        """Проверяет, пересекается ли comp с любым уже размещённым компонентом."""
        comp_rect = (comp.x, comp.y, comp.width, comp.height)
        for cid in positioned:
            if cid == exclude_id:
                continue
            other = main_comps[cid]
            other_rect = (other.x, other.y, other.width, other.height)
            if self._rects_overlap(comp_rect, other_rect):
                return True
        return False

    def _nudge_to_free(self, comp, main_comps, positioned, comp_id):
        """
        Сдвигает компонент в ближайшую свободную позицию, если он
        перекрывается с уже размещёнными компонентами.
        Поиск идёт спиралью вокруг исходной позиции.
        """
        if not self._overlaps_any(comp, main_comps, positioned, comp_id):
            return  # Позиция уже свободна

        orig_x, orig_y = comp.x, comp.y
        step = 10

        # Спиральный поиск: пробуем смещения по возрастанию расстояния
        for dist in range(step, 300, step):
            # 8 направлений на каждом расстоянии
            offsets = [
                (0, dist), (0, -dist),          # вниз, вверх
                (dist, 0), (-dist, 0),          # вправо, влево
                (dist, dist), (-dist, dist),    # диагонали
                (dist, -dist), (-dist, -dist),
            ]
            for dx, dy in offsets:
                comp.x = round((orig_x + dx) / 10) * 10
                comp.y = round((orig_y + dy) / 10) * 10

                # Не выходим за границы рабочей области
                if comp.x < self.pad_left or comp.x + comp.width > self.width - self.pad_right:
                    continue
                if comp.y < self.pad_top or comp.y + comp.height > self.height - self.pad_bottom:
                    continue

                if not self._overlaps_any(comp, main_comps, positioned, comp_id):
                    comp.update_ports()
                    return

        comp.x, comp.y = orig_x, orig_y
        comp.update_ports()

    # ── Поиск цикла ──

    def _find_cycle(self, adj, valid):
        """DFS-поиск замкнутого направленного цикла в фреоновом графе."""
        for start in adj:
            if start not in valid:
                continue
            visited = set()
            result = self._dfs(start, start, [], visited, adj, valid)
            if result and len(result) >= 3:
                return result
        return []

    def _dfs(self, start, node, path, visited, adj, valid):
        if node == start and path:
            return path
        if node in visited:
            return None
        visited.add(node)
        for nb in adj.get(node, []):
            if nb not in valid:
                continue
            if nb in visited and nb != start:
                continue
            result = self._dfs(start, nb, path + [node], visited, adj, valid)
            if result:
                return result
        visited.discard(node)
        return None

    # ── Позиции по прямоугольному контуру ──

    def _cycle_rect_positions(self, n):
        """
        Разместить n компонентов цикла по прямоугольнику.
        Порядок обхода: низ-лево → верх-лево → верх-центр → центр.
        """
        corners = [
            (0.12, 0.82),    # низ-лево  (Компрессор)
            (0.12, 0.22),    # верх-лево (Конденсатор)
            (0.32, 0.12),    # верх-центр (Дроссель)
            (0.50, 0.50),    # центр      (Бак / Испаритель)
        ]
        if n <= 4:
            return corners[:n]
        # Дополнительные точки на нижнем ребре прямоугольника
        positions = list(corners)
        for i in range(4, n):
            t = (i - 3) / (n - 3)
            x = corners[3][0] + t * (corners[0][0] - corners[3][0])
            y = corners[3][1] + t * (corners[0][1] - corners[3][1])
            positions.append((x, y))
        return positions

    # ── Байпас ──

    def _place_bypass(self, valve, anchor, cycle, main_comps, safe_w, safe_h):
        """Разместить клапан байпаса правее и выше компрессора."""
        # Ищем компонент цикла, расположенный прямо над якорем (конденсатор)
        above = None
        for cid in cycle:
            c = main_comps[cid]
            same_col = abs((c.x + c.width / 2) - (anchor.x + anchor.width / 2)) < 50
            if same_col and c.y < anchor.y:
                above = c
                break

        x_pos = anchor.x + anchor.width + 80
        if above:
            y_pos = above.y + above.height + 30
        else:
            y_pos = anchor.y - 60

        valve.x = round(x_pos / 10) * 10
        valve.y = round((y_pos - valve.height / 2) / 10) * 10
        valve.update_ports()

    # ── Водяной контур ──

    def _place_downstream(self, comp, anchor, conn_type, safe_w, safe_h):
        """Разместить компонент водяного контура правее якоря.
        
        Вертикальная позиция выбирается так, чтобы труба шла
        горизонтально:
        - Для water_lt: насос встаёт на уровне порта water_out бака
        - Для water_ht: ТЭН встаёт на уровне середины бака
        - Для drain: компонент встаёт ниже якоря на уровне слива
        """
        anchor_x_pct = (anchor.x + anchor.width / 2 - self.padding) / safe_w
        x_pct = min(0.85, anchor_x_pct + 0.15)

        # Попробуем выровнять по порту якоря, чтобы труба шла горизонтально
        if 'water_lt' in conn_type and hasattr(anchor, 'ports') and 'water_out' in anchor.ports:
            # Насос — на уровне водяного выхода бака
            port_y = anchor.ports['water_out'][1]
            y_pct = (port_y + comp.height / 2 - self.padding) / safe_h
        elif 'water_ht' in conn_type:
            y_pct = 0.35        # верхняя зона (ТЭН)
        elif 'drain' in conn_type:
            # Компонент слива — ниже якоря, на уровне сливного порта
            if hasattr(anchor, 'ports') and 'drain' in anchor.ports:
                port_y = anchor.ports['drain'][1]
                y_pct = (port_y + 30 + comp.height / 2 - self.padding) / safe_h
            else:
                y_pct = (anchor.y + anchor.height + 30 + comp.height / 2 - self.padding) / safe_h
        else:
            y_pct = 0.50

        self._place(comp, x_pct, y_pct, safe_w, safe_h)