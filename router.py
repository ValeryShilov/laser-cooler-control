import heapq

class AStarRouter:
    def __init__(self, width, height, grid_size=10):
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.obstacles = []
        self.drawn_cells = set() # ПАМЯТЬ ТРУБ: Хранит занятые пиксели

    def add_obstacle(self, x, y, w, h, padding=10):
        self.obstacles.append((x - padding, y - padding, x + w + padding, y + h + padding))

    def register_path(self, path):
        """ Запоминает проложенную трубу, чтобы другие шли параллельно, а не поверх """
        for pt in path:
            self.drawn_cells.add(pt)

    def _is_blocked(self, x, y):
        if x < 0 or x > self.width or y < 0 or y > self.height: return True
        for ox1, oy1, ox2, oy2 in self.obstacles:
            if ox1 <= x <= ox2 and oy1 <= y <= oy2: return True
        return False

    def _cleanup_path(self, path):
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
        
        # Сохраняем готовую трубу в память, чтобы следующие трубы её обходили
        self.register_path(clean_path)
        return clean_path

    def _astar(self, start, end):
        queue = [(0, start)]
        came_from = {start: None}
        g_score = {start: 0}
        directions = [(0, self.grid_size), (0, -self.grid_size), (self.grid_size, 0), (-self.grid_size, 0)]

        while queue:
            _, current = heapq.heappop(queue)
            if current == end:
                path = []
                while current:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]

            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                if neighbor != end and self._is_blocked(neighbor[0], neighbor[1]): continue

                # ЖЕСТКИЙ ШТРАФ ЗА ПОВОРОТЫ (убивает зигзаги)
                turn_penalty = 0
                if came_from[current]:
                    prev = came_from[current]
                    if (current[0] - prev[0], current[1] - prev[1]) != (dx, dy):
                        turn_penalty = 200 

                # ШТРАФ ЗА НАЛОЖЕНИЕ ТРУБ (заставляет трубы идти параллельно)
                overlap_penalty = 0
                if neighbor in self.drawn_cells and neighbor != end and neighbor != start:
                    overlap_penalty = 150

                tentative_g = g_score[current] + 1 + turn_penalty + overlap_penalty
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + (abs(end[0] - neighbor[0]) + abs(end[1] - neighbor[1]))
                    heapq.heappush(queue, (f_score, neighbor))
        return []