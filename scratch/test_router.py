"""Minimal A* test - no Qt dependency"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from services.router import AStarRouter

router = AStarRouter(width=1000, height=500, grid_size=10)
# Add a simple obstacle
router.add_obstacle(200, 100, 100, 100, padding=10)

print("Test 1: Simple horizontal path")
t = time.time()
p = router.find_path((100, 50), (400, 50), (130, 50), (370, 50))
print(f"  Time: {time.time()-t:.3f}s, Path: {p}")

print("\nTest 2: Path around obstacle")
t = time.time()
p = router.find_path((150, 150), (350, 150), (180, 150), (320, 150))
print(f"  Time: {time.time()-t:.3f}s, Path: {p}")

print("\nTest 3: Complex path")
t = time.time()
p = router.find_path((100, 200), (400, 100), (130, 200), (370, 100))
print(f"  Time: {time.time()-t:.3f}s, Path: {p}")

print("\nDone!")
