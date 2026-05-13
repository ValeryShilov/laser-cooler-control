import logging
from collections import defaultdict



logger = logging.getLogger(__name__)


class TopologyLayoutEngine:
    def __init__(self, padding=100):
        self.width = 1000
        self.height = 600
        self.padding = padding
        self.pad_left = padding
        self.pad_right = padding
        self.pad_top = padding
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
        """Оркестратор размещения внешних портов.
        
        Алгоритм:
        1. Для каждого порта вычисляем ideal_y по позиции связанного компонента
        2. Сортируем по ideal_y (drain всегда в конце)
        3. Размещаем сверху вниз, разрешая наложения минимальным сдвигом
        """
        if not ext_ports:
            logger.debug("Step: place_external_ports", extra={"journal_entry": {
                "step": "place_external_ports",
                "context": {},
                "input": {"ext_port_count": 0},
                "output": {},
                "decision": {"skipped": True, "reason": "no external ports"},
            }})
            return

        # X-позиция: правее всех основных компонентов
        max_comp_x = max([c.x + c.width for c in main_comps.values()]) if main_comps else 700
        x_pos = max_comp_x + 120
        min_spacing = 40  # ExternalPort.height=30 + 10px отступ

        # Шаг 1: Вычисляем роль и ideal_y для каждого порта
        port_info = self._compute_port_info(ext_ports, connections, main_comps)

        # Шаг 2: Сортируем по ideal_y, drain всегда последний
        sorted_ports = sorted(ext_ports, key=lambda p: (
            1 if port_info.get(p.id, {}).get('role') == 'drain' else 0,
            port_info.get(p.id, {}).get('ideal_y') or 9999
        ))

        # Шаг 2.5: Разносим порты с одинаковым ideal_y симметрично
        # Если 2 порта хотят ideal_y=120, ставим их на 100 и 140 (±20)
        # Порт, подключённый к более дальнему (левому) компоненту — сверху,
        # чтобы его труба шла поверх остальных без пересечений
        spread_y = {}
        y_groups = defaultdict(list)
        for port in sorted_ports:
            iy = port_info.get(port.id, {}).get('ideal_y')
            if iy is not None:
                y_groups[iy].append(port.id)
        for iy, group_ids in y_groups.items():
            if len(group_ids) == 1:
                spread_y[group_ids[0]] = iy
            else:
                # Сортируем внутри группы: ближний (больший X) — сверху,
                # чтобы его труба ушла горизонтально раньше и не мешала дальним
                group_ids.sort(key=lambda pid: port_info.get(pid, {}).get('target_x', 0), reverse=True)
                n = len(group_ids)
                half = (n - 1) * min_spacing / 2
                for i, pid in enumerate(group_ids):
                    spread_y[pid] = round((iy - half + i * min_spacing) / 10) * 10

        # Шаг 2.9: Пересортировка с учётом spread_y
        sorted_ports = sorted(sorted_ports, key=lambda p: (
            1 if port_info.get(p.id, {}).get('role') == 'drain' else 0,
            spread_y.get(p.id) or port_info.get(p.id, {}).get('ideal_y') or 9999
        ))

        # Шаг 3: Размещаем сверху вниз
        prev_bottom = self.pad_top
        for port in sorted_ports:
            info = port_info.get(port.id, {})
            ideal_y = spread_y.get(port.id, info.get('ideal_y'))

            port.x = round((x_pos - port.width / 2) / 10) * 10

            if ideal_y is not None:
                # Ставим на ideal_y, но не ближе чем min_spacing к предыдущему
                port.y = round(max(ideal_y, prev_bottom) / 10) * 10
            else:
                port.y = round(prev_bottom / 10) * 10

            prev_bottom = port.y + min_spacing
            port.update_ports()

        final_positions = {p.id: {"x": p.x, "y": p.y, "role": port_info.get(p.id, {}).get('role')} for p in sorted_ports}
        logger.debug("Step: place_external_ports", extra={"journal_entry": {
            "step": "place_external_ports",
            "context": {},
            "input": {"ext_port_count": len(ext_ports), "x_pos": x_pos},
            "output": {"final_positions": final_positions},
            "decision": None,
        }})

    def _compute_port_info(self, ext_ports, connections, main_comps):
        """Для каждого внешнего порта вычисляет роль (input/output/drain) и ideal_y.
        
        Роли определяются по направлению связи:
        - Порт является SOURCE (от порта к компоненту) → это VXOD в чиллер (стрелка ←)
        - Порт является TARGET (от компонента к порту) → это ВЫХОД из чиллера (стрелка →)
        - Тип связи 'drain' → СЛИВ
        
        ideal_y вычисляется как Y порта связанного компонента - 20 (центрирование).
        """
        ext_ids = {p.id for p in ext_ports}
        port_info = {}  # {port_id: {'role': str, 'ideal_y': int|None, 'target_x': int}}

        for conn in connections:
            src, tgt = conn['source_id'], conn['target_id']
            conn_type = conn.get('type', '')
            src_port = conn.get('source_port', 'out')
            tgt_port = conn.get('target_port', 'in')

            # Порт — цель трубы (output из чиллера или drain)
            if tgt in ext_ids and src in main_comps:
                comp = main_comps[src]
                role = 'drain' if conn_type == 'drain' else 'output'
                ideal_y = None
                target_x = comp.x
                if src_port in comp.ports:
                    y_val = comp.ports[src_port][1]
                    target_x = comp.ports[src_port][0]
                    ideal_y = round((y_val - 20) / 10) * 10
                if tgt not in port_info:  # первая связь побеждает
                    port_info[tgt] = {'role': role, 'ideal_y': ideal_y, 'target_x': target_x}

            # Порт — источник трубы (input в чиллер)
            if src in ext_ids and tgt in main_comps:
                comp = main_comps[tgt]
                ideal_y = None
                target_x = comp.x
                if tgt_port in comp.ports:
                    target_x = comp.ports[tgt_port][0]
                    ideal_y = round((comp.ports[tgt_port][1] - 20) / 10) * 10
                if src not in port_info:
                    port_info[src] = {'role': 'input', 'ideal_y': ideal_y, 'target_x': target_x}

        # Порты без связей — unknown
        for port in ext_ports:
            if port.id not in port_info:
                port_info[port.id] = {'role': 'unknown', 'ideal_y': None, 'target_x': 9999}

        return port_info

    # ══════════════════════════════════════════
    #  Вспомогательные методы (без изменений)
    # ══════════════════════════════════════════

    def _place(self, comp, x_pct, y_pct, safe_w, safe_h):
        """Разместить компонент по процентным координатам безопасной зоны."""
        comp.x = round((self.padding + safe_w * x_pct - comp.width / 2) / 10) * 10
        comp.y = round((self.padding + safe_h * y_pct - comp.height / 2) / 10) * 10
        comp.update_ports()

    # ── Обнаружение и разрешение коллизий ──

    def _rects_overlap(self, r1, r2, padding=35):
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
        Поиск идёт по периметрам квадратов вокруг исходной позиции.
        """
        if not self._overlaps_any(comp, main_comps, positioned, comp_id):
            return

        orig_x, orig_y = comp.x, comp.y
        step = 20

        for dist in range(step, 800, step):
            # Проверяем верхнюю и нижнюю грани квадрата (радиус dist)
            for dx in range(-dist, dist + 1, step):
                for dy in [-dist, dist]:
                    comp.x = round((orig_x + dx) / 10) * 10
                    comp.y = round((orig_y + dy) / 10) * 10
                    if not self._overlaps_any(comp, main_comps, positioned, comp_id):
                        if self.pad_left <= comp.x <= self.width - self.pad_right - comp.width:
                            if self.pad_top <= comp.y <= self.height - self.pad_bottom - comp.height:
                                comp.update_ports()
                                return

            # Проверяем левую и правую грани квадрата (без углов)
            for dy in range(-dist + step, dist, step):
                for dx in [-dist, dist]:
                    comp.x = round((orig_x + dx) / 10) * 10
                    comp.y = round((orig_y + dy) / 10) * 10
                    if not self._overlaps_any(comp, main_comps, positioned, comp_id):
                        if self.pad_left <= comp.x <= self.width - self.pad_right - comp.width:
                            if self.pad_top <= comp.y <= self.height - self.pad_bottom - comp.height:
                                comp.update_ports()
                                return

        # Fallback: игнорируем границы экрана, лишь бы не было наложений
        for dist in range(step, 1500, step):
            for dx in range(-dist, dist + 1, step):
                for dy in [-dist, dist]:
                    comp.x = round((orig_x + dx) / 10) * 10
                    comp.y = round((orig_y + dy) / 10) * 10
                    if not self._overlaps_any(comp, main_comps, positioned, comp_id):
                        comp.update_ports()
                        return
            for dy in range(-dist + step, dist, step):
                for dx in [-dist, dist]:
                    comp.x = round((orig_x + dx) / 10) * 10
                    comp.y = round((orig_y + dy) / 10) * 10
                    if not self._overlaps_any(comp, main_comps, positioned, comp_id):
                        comp.update_ports()
                        return

        # Если совсем ничего не помогло (невозможно), оставляем как есть
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