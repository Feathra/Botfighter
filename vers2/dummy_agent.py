import random
import math
import time
import pygame

class DummyAgent:
    def __init__(self, ship_index):
        self.ship_index = ship_index
        self.last_direction_change = time.time()
        self.current_rotation = 0

    def decide_from_sensors(self, sensor_data):
        """
        Makes decisions based only on laser and radar sensor data
        """
        # Check for wall ahead with laser
        if sensor_data.get("laser_hit", False) and sensor_data.get("laser_distance", 100) < 30:
            # Wall detected ahead - turn randomly between 45-135 degrees
            turn_angle = random.uniform(45, 135) * random.choice([-1, 1])
            print(f"Wall detected at distance {sensor_data.get('laser_distance')}, turning {turn_angle}")
            return {"rotate": turn_angle, "thrust": 0, "shoot": False}
        
        # Search for objects in radar
        enemies = []
        coins = []
        
        for obj in sensor_data.get("radar_objects", []):
            if obj["type"] == "enemy":
                enemies.append(obj)
            elif obj["type"] == "coin":
                coins.append(obj)
        
        # Target nearest enemy if any detected
        if enemies:
            # Sort by distance
            enemies.sort(key=lambda x: x["distance"])
            nearest_enemy = enemies[0]
            
            # Turn toward enemy
            turn_rate = min(5, abs(nearest_enemy["angle"])) * (1 if nearest_enemy["angle"] > 0 else -1)
            
            # If facing roughly toward enemy, shoot
            should_shoot = abs(nearest_enemy["angle"]) < 10
            
            # If enemy is very close, back up, otherwise approach
            thrust_value = -0.5 if nearest_enemy["distance"] < 100 else 0.5
            print(f"Enemy detected at distance {nearest_enemy['distance']}, angle {nearest_enemy['angle']}")
            
            return {
                "rotate": turn_rate, 
                "thrust": thrust_value, 
                "shoot": should_shoot
            }
        
        # If no enemies but coins found, collect nearest coin
        elif coins:
            # Sort by distance
            coins.sort(key=lambda x: x["distance"])
            nearest_coin = coins[0]
            
            # Better steering toward coins
            relative_angle = nearest_coin["angle"]
            
            # More aggressive turning for larger angles
            if abs(relative_angle) > 90:
                turn_rate = 5 * (1 if relative_angle > 0 else -1)
            else:
                turn_rate = min(5, abs(relative_angle) * 0.2) * (1 if relative_angle > 0 else -1)
            
            # Adjust thrust based on angle - slow down when turning sharply
            thrust_value = 1.0 if abs(relative_angle) < 30 else 0.5
            
            print(f"Coin detected at distance {nearest_coin['distance']}, angle {relative_angle}, turn: {turn_rate}, thrust: {thrust_value}")
            
            # Move toward coin
            return {
                "rotate": turn_rate, 
                "thrust": thrust_value, 
                "shoot": False
            }
        
        # No objects detected - explore randomly
        else:
            # Slow random exploration pattern
            return {
                "rotate": random.uniform(-1, 1),
                "thrust": 0.5,
                "shoot": False
            }

    # Single decide method that uses sensors when possible
    def decide(self, game_state, walls):
        """Main decision method that uses sensor data if possible"""
        try:
            # If already formatted as sensor data
            if "laser_hit" in game_state:
                return self.decide_from_sensors(game_state)
                
            # Otherwise use legacy mode (for testing without server)
            if self.ship_index < len(game_state["ships"]):
                return self._legacy_decide(game_state, walls)
            return {"rotate": 0, "thrust": 0, "shoot": False}
        except Exception as e:
            print(f"Error in agent decision: {e}")
            return {"rotate": 0, "thrust": 0, "shoot": False}
            
    def _legacy_decide(self, game_state, walls):
        """Legacy decision method - only used for testing without server"""
        my_ship = game_state["ships"][self.ship_index]
        
        # More random movement for testing
        if random.random() < 0.05:
            return {
                "rotate": random.uniform(-5, 5),
                "thrust": random.uniform(0, 1),
                "shoot": random.random() < 0.1
            }
        
        return {"rotate": 0.5, "thrust": 0.5, "shoot": False}
    
    # Helper methods for line-wall intersections
    @staticmethod
    def _line_intersects_rect(x1, y1, x2, y2, rect):
        # Implementation unchanged
        rect_lines = [
            ((rect["x"], rect["y"]), (rect["x"] + rect["width"], rect["y"])),
            ((rect["x"] + rect["width"], rect["y"]), (rect["x"] + rect["width"], rect["y"] + rect["height"])),
            ((rect["x"] + rect["width"], rect["y"] + rect["height"]), (rect["x"], rect["y"] + rect["height"])),
            ((rect["x"], rect["y"] + rect["height"]), (rect["x"], rect["y"]))
        ]
        for (rx1, ry1), (rx2, ry2) in rect_lines:
            if DummyAgent._line_intersects_line(x1, y1, x2, y2, rx1, ry1, rx2, ry2):
                return True
        return False

    @staticmethod
    def _line_intersects_line(x1, y1, x2, y2, x3, y3, x4, y4):
        # Checks if two lines intersect
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

        return ccw((x1, y1), (x3, y3), (x4, y4)) != ccw((x2, y2), (x3, y3), (x4, y4)) and ccw((x1, y1), (x2, y2), (x3, y3)) != ccw((x1, y1), (x2, y2), (x4, y4))

    @staticmethod
    def _get_intersection_point(x1, y1, x2, y2, rect):
        # Convert pygame.Rect to dictionary if necessary
        if isinstance(rect, pygame.Rect):
            rect = {"x": rect.x, "y": rect.y, "width": rect.width, "height": rect.height}

        # Calculates the intersection point of a line with a rectangle
        rect_lines = [
            ((rect["x"], rect["y"]), (rect["x"] + rect["width"], rect["y"])),
            ((rect["x"] + rect["width"], rect["y"]), (rect["x"] + rect["width"], rect["y"] + rect["height"])),
            ((rect["x"] + rect["width"], rect["y"] + rect["height"]), (rect["x"], rect["y"] + rect["height"])),
            ((rect["x"], rect["y"] + rect["height"]), (rect["x"], rect["y"]))
        ]
        for (rx1, ry1), (rx2, ry2) in rect_lines:
            denom = (x1 - x2) * (ry1 - ry2) - (y1 - y2) * (rx1 - rx2)
            if denom == 0:
                continue
            t = ((x1 - rx1) * (ry1 - ry2) - (y1 - ry1) * (rx1 - rx2)) / denom
            u = -((x1 - x2) * (y1 - ry1) - (y1 - y2) * (x1 - rx1)) / denom
            if 0 <= t <= 1 and 0 <= u <= 1:
                return x1 + t * (x2 - x1), y1 + t * (y2 - y1)
        return x2, y2  # Default to the end of the line if no intersection is found

    def _is_wall_ahead(self, x, y, angle, walls):
        """
        Checks if there is a wall directly in front of the agent.
        """
        laser_length = 10  # Short range to check for walls ahead
        rad = math.radians(angle)
        laser_end_x = x + math.cos(rad) * laser_length
        laser_end_y = y + math.sin(rad) * laser_length

        # Optimization: Only check walls within a radius
        close_walls = []
        check_radius = 50  # Check only walls very close ahead
        for wall in walls:
            if math.hypot(x - (wall.x + wall.width / 2), y - (wall.y + wall.height / 2)) < check_radius:
                close_walls.append(wall)

        for wall in close_walls:
            if self._line_intersects_rect(x, y, laser_end_x, laser_end_y, {"x": wall.x, "y": wall.y, "width": wall.width, "height": wall.height}):
                return True
        return False

def can_see_player(enemy, player, walls):
    """
    Checks if the enemy has a clear line of sight to the player.
    """
    dx = player.x - enemy.x
    dy = player.y - enemy.y
    distance = math.hypot(dx, dy)
    steps = int(distance / 10)  # Divide the line into steps

    for step in range(steps):
        check_x = enemy.x + dx * (step / steps)
        check_y = enemy.y + dy * (step / steps)
        check_rect = pygame.Rect(check_x - 5, check_y - 5, 10, 10)  # Small area to check
        for wall in walls:
            if check_rect.colliderect(wall):
                print(f"Wall blocks view at ({check_x}, {check_y})")  # Debugging
                return False  # Wall blocks the view
    return True
