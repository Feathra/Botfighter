import random
import math
import time
import pygame

class DummyAgent:
    def __init__(self, ship_index):
        self.ship_index = ship_index  # The index of the ship controlled by the agent
        self.last_direction_change = time.time()  # Track the last time the direction was changed
        self.current_rotation = 0  # Current rotation direction

    def decide(self, game_state, walls):
        """
        Returns a dictionary with possible actions:
        {
            "rotate": -3,     # Rotate left
            "thrust": 1,      # Move forward
            "shoot": True     # Shoot
        }
        """
        # Get the agent's ship and the target ship
        my_ship = game_state["ships"][self.ship_index]
        target_ship = game_state["ships"][1 - self.ship_index]  # The other ship is the target

        # Extract positions and angles
        my_x, my_y, my_angle = my_ship["x"], my_ship["y"], my_ship["angle"]
        target_x, target_y = target_ship["x"], target_ship["y"]

        # Scan for enemies with the laser
        enemy_detected = self._scan_with_laser(my_x, my_y, my_angle, target_x, target_y, walls)

        if enemy_detected:
            # Calculate the angle to the enemy
            dx = target_x - my_x
            dy = target_y - my_y
            angle_to_enemy = math.degrees(math.atan2(dy, dx))

            # Calculate the shortest rotation direction
            angle_difference = (angle_to_enemy - my_angle + 360) % 360
            if angle_difference > 180:
                angle_difference -= 360  # Rotate left if shorter

            # Limit the rotation speed
            max_rotation_speed = 40  # Maximum rotation speed per frame
            rotation = max(-max_rotation_speed, min(angle_difference, max_rotation_speed))

            # Rotate towards the enemy and shoot
            print(f"Enemy detected! Rotating by {rotation:.2f} degrees and shooting.")
            return {"rotate": rotation, "thrust": 0.5, "shoot": True}

        # Check if there is a wall directly in front of the agent
        if self._is_wall_ahead(my_x, my_y, my_angle, walls):
            # Rotate randomly to avoid the wall
            self.current_rotation = random.choice([-1, 1]) * random.randint(90, 180)  # Random angle between 90 and 180 degrees
            print(f"Wall ahead! Rotating by {self.current_rotation} degrees.")
            return {"rotate": self.current_rotation, "thrust": 0, "shoot": False}

        # Add slow self-rotation
        slow_rotation = 0.8  # Very slow rotation (1 degree per frame)
        return {"rotate": slow_rotation, "thrust": 1, "shoot": False}

    def _scan_with_laser(self, x, y, angle, target_x, target_y, walls):
        """
        Scans for enemies with a laser and returns True if the enemy is detected.
        The laser stops if it hits a wall.
        """
        laser_length = 1000  # Long range for enemy detection
        rad = math.radians(angle)
        laser_end_x = x + math.cos(rad) * laser_length
        laser_end_y = y + math.sin(rad) * laser_length

        # Check if the laser is blocked by walls
        for wall in walls:
            if self._line_intersects_rect(x, y, laser_end_x, laser_end_y, {"x": wall.x, "y": wall.y, "width": wall.width, "height": wall.height}):
                # If the laser hits a wall, stop the laser at the intersection point
                intersection = self._get_intersection_point(x, y, laser_end_x, laser_end_y, wall)
                laser_end_x, laser_end_y = intersection
                print(f"Laser blocked by wall at ({laser_end_x}, {laser_end_y})")  # Debugging
                break

        # Check if the laser hits the enemy
        if math.hypot(target_x - x, target_y - y) <= math.hypot(laser_end_x - x, laser_end_y - y):
            print("Enemy detected!")  # Debugging
            return True  # Enemy is visible

        print("Enemy not visible!")  # Debugging
        return False  # Enemy is not visible

    @staticmethod
    def _line_intersects_rect(x1, y1, x2, y2, rect):
        # Checks if a line intersects a rectangle
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
