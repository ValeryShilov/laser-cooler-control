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
                if (x, y) not in exempt and self._is_blocked(x, y):
                    return False
        else:  # Горизонтальный
            y = p1[1]
            x_start, x_end = min(p1[0], p2[0]), max(p1[0], p2[0])
            for x in range(x_start, x_end + 1, gs):
                if (x, y) not in exempt and self._is_blocked(x, y):
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

    def _smooth_path(self, path, exempt=None):
        """
        Пост-обработка: убирает лишние повороты.
        
        1. Агрессивное сглаживание: пытается соединить далёкие точки напрямую
           (пропуская промежуточные) через L-образный маршрут.
        2. Тройное сглаживание: для каждой тройки последовательных точек
           проверяет, можно ли заменить на более прямой маршрут.
        3. Финальная очистка коллинеарных точек.
        
        exempt — множество точек (портов), освобождённых от проверки obstacles.
        """
        if len(path) < 3:
            return path
        if exempt is None:
            exempt = set()
        
        # === Фаза 1: Агрессивное сглаживание (пропуск нескольких точек) ===
        # Пробуем соединить point[i] с point[i+k] для k=len..3, убирая промежуточные
        changed = True
        max_passes = 3
        while changed and max_passes > 0:
            changed = False
            max_passes -= 1
            new_path = [path[0]]
            i = 0
            while i < len(path) - 1:
                # Пробуем пропустить максимум точек — от самого далёкого к ближайшему
                best_j = None
                best_mid = None
                for j in range(len(path) - 1, i + 1, -1):
                    pa = path[i]
                    pb = path[j]
                    
                    # Прямая линия?
                    if (pa[0] == pb[0] or pa[1] == pb[1]) and self._line_clear(pa, pb, exempt):
                        best_j = j
                        best_mid = None
                        break
                    
                    # L-образный маршрут?
                    mid_h = (pb[0], pa[1])
                    mid_v = (pa[0], pb[1])
                    for mid in [mid_h, mid_v]:
                        if mid == pa or mid == pb:
                            continue
                        if self._line_clear(pa, mid, exempt) and self._line_clear(mid, pb, exempt):
                            best_j = j
                            best_mid = mid
                            break
                    if best_j is not None:
                        break
                
                if best_j is not None and best_j > i + 1:
                    # Нашли сокращение — пропускаем промежуточные точки
                    if best_mid is not None:
                        new_path.append(best_mid)
                    new_path.append(path[best_j])
                    i = best_j
                    changed = True
                else:
                    # Не нашли — оставляем следующую точку как есть
                    i += 1
                    if i < len(path):
                        new_path.append(path[i])
            
            path = new_path
        
        # === Фаза 2: Тройное сглаживание (L-shape на тройках) ===
        changed = True
        max_passes = 3
        while changed and max_passes > 0:
            changed = False
            max_passes -= 1
            new_path = [path[0]]
            i = 0
            while i < len(path) - 2:
                p1 = path[i]
                p3 = path[i + 2]
                p2 = path[i + 1]
                
                # Если p1→p3 уже прямая линия (ортогональная и свободная), пропускаем p2
                if (p1[0] == p3[0] or p1[1] == p3[1]) and self._line_clear(p1, p3, exempt):
                    new_path.append(p3)
                    i += 2
                    changed = True
                    continue
                
                # Пробуем L-образный маршрут с одним поворотом
                mid_h = (p3[0], p1[1])
                mid_v = (p1[0], p3[1])
                
                replaced = False
                for mid in [mid_h, mid_v]:
                    if mid == p2:
                        continue  # То же самое — пропускаем
                    if mid == p1 or mid == p3:
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
            
            # Добавляем оставшиеся точки
            while i < len(path):
                if not new_path or path[i] != new_path[-1]:
                    new_path.append(path[i])
                i += 1
            
            path = new_path
        
        # === Фаза 3: Финальная очистка коллинеарных точек ===
        path = self._cleanup_path(path)
        
        return path

    def find_path(self, exact_start, exact_end, safe_start, safe_end, waypoints=None):
        points = [safe_start]
        if waypoints:
            for wp in waypoints:
                points.append((round(wp[0]/self.grid_size)*self.grid_size, round(wp[1]/self.grid_size)*self.grid_size))
        points.append(safe_end)

        full_path = []
        for i in range(len(points) - 1):
            segment = self._astar(points[i], points[i+1])
            if not segment: return [] 
            if full_path:
                full_path.extend(segment[1:])
            else:
                full_path.extend(segment)
                
        raw_path = [exact_start] + full_path + [exact_end]
        clean_path = self._cleanup_path(raw_path)
        
        # Точки портов и escape-сегменты освобождены от проверки obstacles.
        # Это позволяет _smooth_path оптимизировать через зону padding рядом с портами.
        exempt = {exact_start, exact_end, safe_start, safe_end}
        gs = self.grid_size
        # Добавляем все промежуточные точки escape-сегментов в exempt
        for seg_start, seg_end in [(exact_start, safe_start), (safe_end, exact_end)]:
            dx = seg_end[0] - seg_start[0]
            dy = seg_end[1] - seg_start[1]
            steps = max(abs(dx), abs(dy)) // gs if gs > 0 else 0
            if steps > 0:
                for s in range(steps + 1):
                    ex = seg_start[0] + (dx * s // steps)
                    ey = seg_start[1] + (dy * s // steps)
                    exempt.add((ex, ey))
        
        smooth_path = self._smooth_path(clean_path, exempt)
        
        # Сохраняем готовую трубу в память, чтобы следующие трубы её обходили
        self.register_path(smooth_path)
        return smooth_path

    def _astar(self, start, end):
        queue = [(0, start)]
        came_from = {start: None}
        g_score = {start: 0}
        gs = self.grid_size
        directions = [(0, gs), (0, -gs), (gs, 0), (-gs, 0)]

        # Освобождаем start и end от проверки препятствий:
        # это позволяет трубам выходить из портов, расположенных
        # вплотную к компоненту (внутри зоны obstacle-padding).
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

                # Проверка препятствий: start и end свободны от проверки
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
                    overlap_penalty = 200

                # Штраф за соседство с трубой (мягкое разнесение)
                proximity_penalty = 0
                for pdx, pdy in directions:
                    adj = (neighbor[0] + pdx, neighbor[1] + pdy)
                    if adj in self.drawn_cells and adj not in exempt:
                        proximity_penalty = 30
                        break

                tentative_g = g_score[current] + gs + turn_penalty + overlap_penalty + proximity_penalty
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = abs(end[0] - neighbor[0]) + abs(end[1] - neighbor[1])
                    f_score = tentative_g + h * 1.001  # Tie-breaking ускоряет поиск
                    heapq.heappush(queue, (f_score, neighbor))
        return []