import logging
from collections import defaultdict
from rules import PORT_ORDER


logger = logging.getLogger(__name__)


class TopologyLayoutEngine:
    def __init__(self, padding=50):
        self.width = 1000
        self.height = 600
        self.padding = padding
        self.pad_left = padding
        self.pad_right = padding
        self.pad_top = 70
        self.pad_bottom = padding

    def layout(self, components, connections):
        """Главный оркестратор расстановки компонентов."""
        main_comps, ext_ports = self._separate_components(components)
        safe_w = self.width - self.pad_left - self.pad_right
        safe_h = self.height - self.pad_top - self.pad_bottom

        logger.debug("Step: separate_components", extra={"journal_entry": {
            "step": "separate_components",
            "context": {},
            "input": {"total_components": len(components)},
            "output": {"main_count": len(main_comps),
                       "ext_port_count": len(ext_ports)},
            "decision": None,
        }})

        freon_adj, mechanical_links = self._build_adjacency(connections, main_comps)
        logger.debug("Step: build_adjacency", extra={"journal_entry": {
            "step": "build_adjacency",
            "context": {},
            "input": {"connections_count": len(connections)},
            "output": {"freon_edges": sum(len(v) for v in freon_adj.values()),
                       "mechanical_links": len(mechanical_links)},
            "decision": None,
        }})

        positioned = set()

        cycle = self._place_freon_cycle(freon_adj, main_comps, positioned, safe_w, safe_h)
        self._place_mechanical(mechanical_links, main_comps, positioned)
        self._place_bypass_components(connections, cycle, main_comps, positioned, safe_w, safe_h)
        self._place_water_circuit(connections, main_comps, positioned, safe_w, safe_h)
        self._place_remaining(main_comps, positioned, safe_w, safe_h)
        self._place_external_ports(ext_ports, connections, main_comps)

        return None

    # ── Фаза 0: Разделение компонентов ──

    def _separate_components(self, components):
        """Разделяет компоненты на основные и внешние порты."""
        main_comps = {}
        ext_ports = []
        for cid, comp in components.items():
            if type(comp).__name__ == "ExternalPort":
                ext_ports.append(comp)
            else:
                main_comps[cid] = comp
        return main_comps, ext_ports

    def _build_adjacency(self, connections, main_comps):
        """Строит граф фреонового контура и словарь механических связей."""
        freon_adj = defaultdict(list)
        mechanical_links = {}
        for conn in connections:
            src, tgt = conn['source_id'], conn['target_id']
            ctype = conn['type']
            if src in main_comps and tgt in main_comps:
                if ctype == 'freon':
                    freon_adj[src].append(tgt)
                elif ctype == 'mechanical':
                    mechanical_links[src] = tgt
        return freon_adj, mechanical_links

    # ── Фаза 1: Фреоновый цикл ──

    def _place_freon_cycle(self, freon_adj, main_comps, positioned, safe_w, safe_h):
        """Находит замкнутый фреоновый цикл и расставляет его по углам."""
        cycle = self._find_cycle(freon_adj, set(main_comps.keys()))
        placed = {}
        if cycle:
            pts = self._cycle_rect_positions(len(cycle))
            for i, cid in enumerate(cycle):
                self._place(main_comps[cid], pts[i][0], pts[i][1], safe_w, safe_h)
                positioned.add(cid)
                placed[cid] = {"x": main_comps[cid].x, "y": main_comps[cid].y,
                               "pct": pts[i]}

        logger.debug("Step: place_freon_cycle", extra={"journal_entry": {
            "step": "place_freon_cycle",
            "context": {},
            "input": {"freon_nodes": list(freon_adj.keys())},
            "output": {"cycle": cycle if cycle else [],
                       "positions": placed},
            "decision": {"found_cycle": bool(cycle),
                         "cycle_length": len(cycle) if cycle else 0},
        }})
        return cycle

    # ── Фаза 2: Механические связи ──

    def _place_mechanical(self, mechanical_links, main_comps, positioned):
        """Размещает механически связанные компоненты (вентилятор ← конденсатор)."""
        placed = {}
        for src_id, tgt_id in mechanical_links.items():
            if src_id not in positioned and tgt_id in positioned and src_id in main_comps:
                partner = main_comps[tgt_id]
                comp = main_comps[src_id]
                comp.x = round((partner.x - comp.width - 10) / 10) * 10
                comp.y = round((partner.y + (partner.height - comp.height) / 2) / 10) * 10
                comp.update_ports()
                self._nudge_to_free(comp, main_comps, positioned, src_id)
                positioned.add(src_id)
                placed[src_id] = {"partner": tgt_id, "x": comp.x, "y": comp.y}

        logger.debug("Step: place_mechanical", extra={"journal_entry": {
            "step": "place_mechanical",
            "context": {},
            "input": {"links": dict(mechanical_links)},
            "output": {"placed": placed},
            "decision": None,
        }})

    # ── Фаза 3: Байпас ──

    def _place_bypass_components(self, connections, cycle, main_comps, positioned, safe_w, safe_h):
        """Размещает клапаны байпаса рядом с фреоновым контуром."""
        bypass_placed = set()
        placed = {}
        for conn in connections:
            if conn['type'] != 'freon_bypass':
                continue
            src, tgt = conn['source_id'], conn['target_id']
            if src in positioned and tgt not in positioned and tgt in main_comps:
                unplaced_id, anchor = tgt, main_comps[src]
            elif tgt in positioned and src not in positioned and src in main_comps:
                unplaced_id, anchor = src, main_comps[tgt]
            else:
                continue
            if unplaced_id in positioned or unplaced_id in bypass_placed:
                continue
            self._place_bypass(main_comps[unplaced_id], anchor, cycle, main_comps, safe_w, safe_h)
            self._nudge_to_free(main_comps[unplaced_id], main_comps, positioned, unplaced_id)
            positioned.add(unplaced_id)
            bypass_placed.add(unplaced_id)
            placed[unplaced_id] = {"anchor": anchor.id,
                                   "x": main_comps[unplaced_id].x,
                                   "y": main_comps[unplaced_id].y}

        logger.debug("Step: place_bypass", extra={"journal_entry": {
            "step": "place_bypass",
            "context": {},
            "input": {"bypass_connections": len([c for c in connections if c['type'] == 'freon_bypass'])},
            "output": {"placed": placed},
            "decision": None,
        }})

    # ── Фаза 4: Водяной контур (BFS) ──

    def _place_water_circuit(self, connections, main_comps, positioned, safe_w, safe_h):
        """BFS-расстановка компонентов водяного контура от уже размещённых."""
        placed = []
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
                    placed.append({"comp_id": tgt, "anchor": src, "type": ctype,
                                   "x": main_comps[tgt].x, "y": main_comps[tgt].y})
                    changed = True
                elif tgt in positioned and src not in positioned and src in main_comps:
                    self._place_downstream(main_comps[src], main_comps[tgt], ctype, safe_w, safe_h)
                    self._nudge_to_free(main_comps[src], main_comps, positioned, src)
                    positioned.add(src)
                    placed.append({"comp_id": src, "anchor": tgt, "type": ctype,
                                   "x": main_comps[src].x, "y": main_comps[src].y})
                    changed = True

        logger.debug("Step: place_water_circuit", extra={"journal_entry": {
            "step": "place_water_circuit",
            "context": {},
            "input": {"water_connections": len([c for c in connections
                      if c['type'] in ('water_lt', 'water_ht', 'drain')])},
            "output": {"placed": placed},
            "decision": None,
        }})

    # ── Фаза 5: Остаток ──

    def _place_remaining(self, main_comps, positioned, safe_w, safe_h):
        """Размещает оставшиеся компоненты рядом с однотипными или в свободной зоне."""
        placed = []
        for cid in main_comps:
            if cid in positioned:
                continue
            comp = main_comps[cid]
            placed_near = self._place_near_buddy(comp, cid, main_comps, positioned)
            if not placed_near:
                self._place(comp, 0.60, 0.50, safe_w, safe_h)
                self._nudge_to_free(comp, main_comps, positioned, cid)
            positioned.add(cid)
            placed.append({"comp_id": cid, "method": "buddy" if placed_near else "fallback",
                           "x": comp.x, "y": comp.y})

        logger.debug("Step: place_remaining", extra={"journal_entry": {
            "step": "place_remaining",
            "context": {},
            "input": {"unpositioned_count": len(placed)},
            "output": {"placed": placed},
            "decision": None,
        }})

    def _place_near_buddy(self, comp, comp_id, main_comps, positioned):
        """Пытается поставить компонент рядом с однотипным уже размещённым."""
        comp_class = type(comp).__name__
        for pid in positioned:
            if type(main_comps[pid]).__name__ == comp_class:
                buddy = main_comps[pid]
                comp.x = round((buddy.x + buddy.width + 20) / 10) * 10
                comp.y = round(buddy.y / 10) * 10
                comp.update_ports()
                self._nudge_to_free(comp, main_comps, positioned, comp_id)
                return True
        return False

    # ── Фаза 6: Внешние порты ──

    def _place_external_ports(self, ext_ports, connections, main_comps):
        """Оркестратор размещения внешних портов."""
        if not ext_ports:
            logger.debug("Step: place_external_ports", extra={"journal_entry": {
                "step": "place_external_ports",
                "context": {},
                "input": {"ext_port_count": 0},
                "output": {},
                "decision": {"skipped": True, "reason": "no external ports"},
            }})
            return
        ext_ports.sort(key=lambda p: PORT_ORDER.index(p.id) if p.id in PORT_ORDER else 99)

        max_comp_x = max([c.x + c.width for c in main_comps.values()]) if main_comps else 700
        x_pos = max_comp_x + 120
        min_spacing = 70

        desired_y = self._align_ports_y(ext_ports, connections, main_comps)
        desired_y = self._resolve_port_overlaps(ext_ports, desired_y, min_spacing)
        self._finalize_port_positions(ext_ports, x_pos, desired_y, min_spacing)

        final_positions = {p.id: {"x": p.x, "y": p.y} for p in ext_ports}
        logger.debug("Step: place_external_ports", extra={"journal_entry": {
            "step": "place_external_ports",
            "context": {},
            "input": {"ext_port_count": len(ext_ports),
                      "x_pos": x_pos},
            "output": {"desired_y": dict(desired_y),
                       "final_positions": final_positions},
            "decision": None,
        }})

    def _align_ports_y(self, ext_ports, connections, main_comps):
        """Вычисляет желаемую Y-координату для каждого внешнего порта."""
        aligned_y = {}
        for conn in connections:
            src, tgt = conn['source_id'], conn['target_id']
            src_port = conn.get('source_port', 'out')
            tgt_port = conn.get('target_port', 'in')

            if tgt in [p.id for p in ext_ports] and src in main_comps:
                if tgt not in aligned_y:
                    comp = main_comps[src]
                    if src_port in comp.ports:
                        y_pos = comp.ports[src_port][1]
                        if src_port == 'drain':
                            y_pos += 30
                        aligned_y[tgt] = y_pos

            if src in [p.id for p in ext_ports] and tgt in main_comps:
                if src not in aligned_y:
                    comp = main_comps[tgt]
                    if tgt_port in comp.ports:
                        aligned_y[src] = comp.ports[tgt_port][1]

        desired_y = {}
        for port in ext_ports:
            if port.id in aligned_y:
                desired_y[port.id] = round((aligned_y[port.id] - 20) / 10) * 10
        return desired_y

    def _resolve_port_overlaps(self, ext_ports, desired_y, min_spacing):
        """Разрешает наложения внешних портов по Y-координате."""
        y_groups = defaultdict(list)
        for port in ext_ports:
            if port.id in desired_y:
                y_groups[desired_y[port.id]].append(port)

        for shared_y, group in y_groups.items():
            if len(group) <= 1:
                continue
            n = len(group)
            group_ids = {p.id for p in group}

            y_above = self.pad_top
            for p in ext_ports:
                if p.id in group_ids:
                    break
                if p.id in desired_y:
                    y_above = max(y_above, desired_y[p.id] + min_spacing)

            space_above = max(shared_y - y_above, 0)

            if space_above > 0:
                actual_spacing = min(min_spacing, space_above / max(n - 1, 1))
                actual_spacing = max(actual_spacing, 40)
                for i, port in enumerate(group):
                    offset = (n - 1 - i) * actual_spacing
                    desired_y[port.id] = round(max(y_above, shared_y - offset) / 10) * 10
            else:
                for i, port in enumerate(group):
                    desired_y[port.id] = shared_y + i * min_spacing

        return desired_y

    def _finalize_port_positions(self, ext_ports, x_pos, desired_y, min_spacing):
        """Финальное размещение портов с гарантией порядка и отсутствия наложений."""
        prev_bottom = self.pad_top
        for port in ext_ports:
            port.x = round((x_pos - port.width / 2) / 10) * 10

            if port.id in desired_y:
                port.y = desired_y[port.id]
            else:
                port.y = round(prev_bottom / 10) * 10

            if port.y < prev_bottom:
                port.y = round(prev_bottom / 10) * 10

            prev_bottom = port.y + min_spacing
            port.update_ports()

    # ══════════════════════════════════════════
    #  Вспомогательные методы (без изменений)
    # ══════════════════════════════════════════

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
            return

        orig_x, orig_y = comp.x, comp.y
        step = 10

        for dist in range(step, 300, step):
            offsets = [
                (0, dist), (0, -dist),
                (dist, 0), (-dist, 0),
                (dist, dist), (-dist, dist),
                (dist, -dist), (-dist, -dist),
            ]
            for dx, dy in offsets:
                comp.x = round((orig_x + dx) / 10) * 10
                comp.y = round((orig_y + dy) / 10) * 10

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
            (0.12, 0.82),
            (0.12, 0.22),
            (0.32, 0.12),
            (0.50, 0.50),
        ]
        if n <= 4:
            return corners[:n]
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

        if 'water_lt' in conn_type and hasattr(anchor, 'ports') and 'water_out' in anchor.ports:
            port_y = anchor.ports['water_out'][1]
            y_pct = (port_y + comp.height / 2 - self.padding) / safe_h
        elif 'water_ht' in conn_type:
            y_pct = 0.50
        elif 'drain' in conn_type:
            if hasattr(anchor, 'ports') and 'drain' in anchor.ports:
                port_y = anchor.ports['drain'][1]
                y_pct = (port_y + 30 + comp.height / 2 - self.padding) / safe_h
            else:
                y_pct = (anchor.y + anchor.height + 30 + comp.height / 2 - self.padding) / safe_h
        else:
            y_pct = 0.50

        self._place(comp, x_pct, y_pct, safe_w, safe_h)