import heapq


class AStarRouter:
    def __init__(self, width, height, grid_size=10):
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.obstacles = []
        self.drawn_cells = set()

    def add_obstacle(self, x, y, w, h, padding=10):
        self.obstacles.append((x - padding, y - padding, x + w + padding, y + h + padding))

    def register_path(self, path):
        """ Запоминает проложенную трубу со всеми промежуточными точками """
        if not path: return
        self.drawn_cells.add(path[0])
        for i in range(len(path) - 1):
            p1 = path[i]
            p2 = path[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            steps = max(abs(dx), abs(dy)) // self.grid_size
            if steps == 0: continue
            for step in range(1, steps + 1):
                x = p1[0] + (dx * step // steps)
                y = p1[1] + (dy * step // steps)
                self.drawn_cells.add((x, y))

    def _is_blocked(self, x, y):
        if x < 0 or x > self.width or y < 0 or y > self.height: return True
        for ox1, oy1, ox2, oy2 in self.obstacles:
            if ox1 <= x <= ox2 and oy1 <= y <= oy2: return True
        return False

    def _line_clear(self, p1, p2, exempt=None):
        """Проверяет, свободен ли ортогональный отрезок от препятствий.

        exempt — множество точек, освобождённых от проверки (порты компонентов).
        """
        if p1[0] != p2[0] and p1[1] != p2[1]:
            return False  # Не ортогональный
        if exempt is None:
            exempt = set()
        gs = self.grid_size
        if p1[0] == p2[0]:  # Вертикальный
            x = p1[0]
            y_start, y_end = min(p1[1], p2[1]), max(p1[1], p2[1])
            for y in range(y_start, y_end + 1, gs):
                if (x, y) not in exempt:
                    if self._is_blocked(x, y) or (x, y) in self.drawn_cells:
                        return False
        else:  # Горизонтальный
            y = p1[1]
            x_start, x_end = min(p1[0], p2[0]), max(p1[0], p2[0])
            for x in range(x_start, x_end + 1, gs):
                if (x, y) not in exempt:
                    if self._is_blocked(x, y) or (x, y) in self.drawn_cells:
                        return False
        return True

    def _cleanup_path(self, path):
        """Удаляет дубликаты и коллинеарные промежуточные точки."""
        if not path: return []
        res = [path[0]]
        for i in range(1, len(path)):
            if path[i] != res[-1]: res.append(path[i])
        if len(res) < 2: return res

        final = [res[0]]
        for i in range(1, len(res)-1):
            p1, p2, p3 = final[-1], res[i], res[i+1]
            if (p1[0] == p2[0] == p3[0]) or (p1[1] == p2[1] == p3[1]):
                continue
            final.append(p2)
        final.append(res[-1])
        return final

    # ── Сглаживание пути ──

    def _smooth_path(self, path, exempt=None):
        """Оркестратор пост-обработки: убирает лишние повороты."""
        if len(path) < 3:
            return path
        exempt = exempt or set()
        path = self._smooth_aggressive(path, exempt)
        path = self._smooth_triples(path, exempt)
        return self._cleanup_path(path)

    def _smooth_aggressive(self, path, exempt):
        """Фаза 1: Агрессивное сглаживание — пропуск промежуточных точек."""
        changed = True
        max_passes = 3
        while changed and max_passes > 0:
            changed = False
            max_passes -= 1
            new_path = [path[0]]
            i = 0
            while i < len(path) - 1:
                best_j, best_mid = self._find_shortcut(path, i, exempt)

                if best_j is not None and best_j > i + 1:
                    if best_mid is not None:
                        new_path.append(best_mid)
                    new_path.append(path[best_j])
                    i = best_j
                    changed = True
                else:
                    i += 1
                    if i < len(path):
                        new_path.append(path[i])

            path = new_path
        return path

    def _find_shortcut(self, path, i, exempt):
        """Ищет самый далёкий j > i+1, до которого можно сократить путь."""
        for j in range(len(path) - 1, i + 1, -1):
            pa = path[i]
            pb = path[j]

            # Прямая линия?
            if (pa[0] == pb[0] or pa[1] == pb[1]) and self._line_clear(pa, pb, exempt):
                return j, None

            # L-образный маршрут?
            for mid in [(pb[0], pa[1]), (pa[0], pb[1])]:
                if mid == pa or mid == pb:
                    continue
                if self._line_clear(pa, mid, exempt) and self._line_clear(mid, pb, exempt):
                    return j, mid
        return None, None

    def _smooth_triples(self, path, exempt):
        """Фаза 2: Тройное сглаживание — L-shape на тройках."""
        changed = True
        max_passes = 3
        while changed and max_passes > 0:
            changed = False
            max_passes -= 1
            new_path = [path[0]]
            i = 0
            while i < len(path) - 2:
                p1 = path[i]
                p2 = path[i + 1]
                p3 = path[i + 2]

                # Прямая линия p1→p3?
                if (p1[0] == p3[0] or p1[1] == p3[1]) and self._line_clear(p1, p3, exempt):
                    new_path.append(p3)
                    i += 2
                    changed = True
                    continue

                # L-образная замена
                replaced = False
                for mid in [(p3[0], p1[1]), (p1[0], p3[1])]:
                    if mid == p2 or mid == p1 or mid == p3:
                        continue
                    if self._line_clear(p1, mid, exempt) and self._line_clear(mid, p3, exempt):
                        new_path.append(mid)
                        new_path.append(p3)
                        i += 2
                        changed = True
                        replaced = True
                        break

                if not replaced:
                    new_path.append(p2)
                    i += 1

            while i < len(path):
                if not new_path or path[i] != new_path[-1]:
                    new_path.append(path[i])
                i += 1

            path = new_path
        return path

    # ── Поиск пути ──

    def find_path(self, exact_start, exact_end, safe_start, safe_end,
                   waypoints=None, return_journal=False):
        """Оркестратор: строит маршрут от exact_start до exact_end.

        Args:
            return_journal: если True, возвращает (path, journal).
        """
        journal = []

        grid_points = self._build_waypoint_chain(safe_start, safe_end, waypoints)
        journal.append({
            "step": "build_waypoints",
            "context": {},
            "input": {"safe_start": safe_start, "safe_end": safe_end,
                      "waypoints": waypoints},
            "output": {"chain": grid_points, "segments": len(grid_points) - 1},
            "decision": None,
        })

        raw_path = self._route_through_points(grid_points)
        if not raw_path:
            journal.append({
                "step": "route_segments",
                "context": {},
                "input": {"segments": len(grid_points) - 1},
                "output": {"raw_path_length": 0},
                "decision": {"result": "no_path_found"},
            })
            if return_journal:
                return [], journal
            return []

        journal.append({
            "step": "route_segments",
            "context": {},
            "input": {"segments": len(grid_points) - 1},
            "output": {"raw_path_length": len(raw_path)},
            "decision": None,
        })

        full_path = [exact_start] + raw_path + [exact_end]
        clean_path = self._cleanup_path(full_path)
        exempt = self._build_exempt_set(exact_start, exact_end, safe_start, safe_end)
        smooth_path = self._smooth_path(clean_path, exempt)

        journal.append({
            "step": "smooth_path",
            "context": {},
            "input": {"clean_path_points": len(clean_path)},
            "output": {"smooth_path_points": len(smooth_path)},
            "decision": {"points_removed": len(clean_path) - len(smooth_path)},
        })

        self.register_path(smooth_path)

        journal.append({
            "step": "final_path",
            "context": {},
            "input": {"exact_start": exact_start, "exact_end": exact_end},
            "output": {"path": smooth_path, "total_points": len(smooth_path)},
            "decision": None,
        })

        if return_journal:
            return smooth_path, journal
        return smooth_path

    def _build_waypoint_chain(self, safe_start, safe_end, waypoints):
        """Подготавливает цепочку промежуточных точек, привязанных к сетке."""
        points = [safe_start]
        if waypoints:
            gs = self.grid_size
            for wp in waypoints:
                points.append((round(wp[0] / gs) * gs, round(wp[1] / gs) * gs))
        points.append(safe_end)
        return points

    def _route_through_points(self, points):
        """Последовательный A* по цепочке промежуточных точек."""
        full_path = []
        for i in range(len(points) - 1):
            segment = self._astar(points[i], points[i + 1])
            if not segment:
                return []
            if full_path:
                full_path.extend(segment[1:])
            else:
                full_path.extend(segment)
        return full_path

    def _build_exempt_set(self, exact_start, exact_end, safe_start, safe_end):
        """Строит множество точек, освобождённых от проверки препятствий."""
        exempt = {exact_start, exact_end, safe_start, safe_end}
        gs = self.grid_size
        for seg_start, seg_end in [(exact_start, safe_start), (safe_end, exact_end)]:
            dx = seg_end[0] - seg_start[0]
            dy = seg_end[1] - seg_start[1]
            steps = max(abs(dx), abs(dy)) // gs if gs > 0 else 0
            if steps > 0:
                for s in range(steps + 1):
                    ex = seg_start[0] + (dx * s // steps)
                    ey = seg_start[1] + (dy * s // steps)
                    exempt.add((ex, ey))
        return exempt

    # ── Ядро A* ──

    def _astar(self, start, end):
        queue = [(0, start)]
        came_from = {start: None}
        g_score = {start: 0}
        gs = self.grid_size
        directions = [(0, gs), (0, -gs), (gs, 0), (-gs, 0)]

        exempt = {start, end}

        max_iter = 50000
        while queue and max_iter > 0:
            max_iter -= 1
            _, current = heapq.heappop(queue)
            if current == end:
                path = []
                while current:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]

            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)

                if neighbor not in exempt and self._is_blocked(neighbor[0], neighbor[1]):
                    continue

                # Штраф за повороты (убивает зигзаги)
                turn_penalty = 0
                if came_from[current]:
                    prev = came_from[current]
                    if (current[0] - prev[0], current[1] - prev[1]) != (dx, dy):
                        turn_penalty = 200

                # Штраф за наложение на существующую трубу
                overlap_penalty = 0
                if neighbor in self.drawn_cells and neighbor not in exempt:
                    overlap_penalty = 500

                # Штраф за соседство с трубой (мягкое разнесение)
                proximity_penalty = 0
                for pdx, pdy in directions:
                    adj = (neighbor[0] + pdx, neighbor[1] + pdy)
                    if adj in self.drawn_cells and adj not in exempt:
                        proximity_penalty = 80
                        break

                tentative_g = g_score[current] + gs + turn_penalty + overlap_penalty + proximity_penalty
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = abs(end[0] - neighbor[0]) + abs(end[1] - neighbor[1])
                    f_score = tentative_g + h * 1.001
                    heapq.heappush(queue, (f_score, neighbor))
        return []