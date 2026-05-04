import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from services.router import AStarRouter

router = AStarRouter(width=1000, height=500, grid_size=10)
# Add tank obstacle
router.add_obstacle(450, 130, 100, 200, padding=10)
# Add pump obstacle
router.add_obstacle(600, 290, 50, 50, padding=10)

print("Tank obstacle:", router.obstacles[0])
print("Pump obstacle:", router.obstacles[1])

start = (580, 290)
end = (570, 320)
print(f"Start blocked? {router._is_blocked(*start)}")
print(f"End blocked? {router._is_blocked(*end)}")

path = router._astar(start, end)
print("Path:", path)
