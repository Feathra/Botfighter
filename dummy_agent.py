import random
import math
import time
import pygame

class DummyAgent:
    """
    An AI agent that makes decisions based on sensor data.
    Can navigate, avoid walls, collect coins, and fight enemies.
    """
    def __init__(self, ship_index):
        self.ship_index = ship_index
        self.last_direction_change = time.time()
        self.current_rotation = 0
        self.last_actions = {"rotate": 0, "thrust": 0, "shoot": False}
        self.target_memory = {"type": None, "position": None, "last_seen": 0}
        
        # Improved stuck detection system
        self.stuck_detection = {
            "position": None,
            "last_position": None,
            "check_time": time.time(),
            "last_check_time": time.time(),
            "is_stuck": False,
            "stuck_count": 0,
            "escape_direction": 1
        }
        
        # Wall memory to avoid repeatedly getting stuck
        self.wall_memory = []

    def decide_from_sensors(self, sensor_data):
        """
        Makes decisions based only on laser and radar sensor data.
        This is the main decision method for the agent.
        """
        current_time = time.time()
        
        # Check for null data
        if not sensor_data:
            return self._random_action()
        
        # Update stuck detection (check every second if we've moved)
        if current_time - self.stuck_detection["check_time"] > 1.0:
            self._update_stuck_detection(sensor_data)
        
        # Enhanced stuck evasion - more aggressive when detected
        if self.stuck_detection["is_stuck"]:
            self.stuck_detection["escape_direction"] = -self.stuck_detection["escape_direction"]
            turn_angle = 45 * self.stuck_detection["escape_direction"]
            
            print(f"STUCK DETECTED! Attempting escape maneuver #{self.stuck_detection['stuck_count']}")
            # Every other attempt, try backing up instead of turning
            if self.stuck_detection["stuck_count"] % 2 == 0:
                return {"rotate": turn_angle, "thrust": -0.8, "shoot": False}
            else:
                return {"rotate": turn_angle, "thrust": 0.2, "shoot": False}
        
        # Enhanced wall detection - detect walls earlier and react more intelligently
        if sensor_data.get("laser_hit", False):
            distance = sensor_data.get("laser_distance", 100)
            
            # Progressively stronger avoidance based on proximity
            if distance < 50:
                # Remember this wall location to avoid it in the future
                # Note: would need current ship position to implement fully
                
                # Determine which way to turn (consistent with prior turns)
                turn_direction = 1 if self.last_actions["rotate"] >= 0 else -1
                
                # More aggressive turning when closer to walls
                turn_amount = 15 if distance < 20 else 8
                turn_angle = turn_amount * turn_direction
                
                print(f"Wall detected at distance {distance:.1f}, turning {turn_angle}")
                
                # Stop thrusting when very close to walls
                thrust_amount = 0 if distance < 20 else 0.1
                
                return {"rotate": turn_angle, "thrust": thrust_amount, "shoot": False}
        
        # Check for wall ahead with laser
        if sensor_data.get("laser_hit", False) and sensor_data.get("laser_distance", 100) < 30:
            # Wall detected ahead - turn randomly
            turn_angle = 5 * random.choice([-1, 1]) 
            print(f"Wall detected at distance {sensor_data.get('laser_distance'):.1f}, turning {turn_angle}")
            return {"rotate": turn_angle, "thrust": 0, "shoot": False}
        
        # Search for objects in radar
        enemies = []
        coins = []
        
        for obj in sensor_data.get("radar_objects", []):
            if obj["type"] == "enemy":
                enemies.append(obj)
            elif obj["type"] == "coin":
                coins.append(obj)
        
        # Target priority: nearby enemies first, then coins
        if enemies:
            # Sort by distance
            enemies.sort(key=lambda x: x["distance"])
            nearest_enemy = enemies[0]
            
            # Save enemy in memory
            self.target_memory = {
                "type": "enemy",
                "distance": nearest_enemy["distance"],
                "angle": nearest_enemy["angle"],
                "last_seen": current_time
            }
            
            # Develop evasive or aggressive behavior based on distance
            if nearest_enemy["distance"] < 100:
                # Close combat mode - dodge or attack
                if nearest_enemy["distance"] < 50:
                    # Too close - back up while shooting
                    return {
                        "rotate": self._calculate_turn_rate(nearest_enemy["angle"], aggressive=True),
                        "thrust": -0.5,  # Back up
                        "shoot": abs(nearest_enemy["angle"]) < 15  # Shoot if facing enemy
                    }
                else:
                    # Combat range - circle strafe
                    circle_direction = 1 if nearest_enemy["angle"] > 0 else -1
                    return {
                        "rotate": 3 * circle_direction,
                        "thrust": 0.3,
                        "shoot": abs(nearest_enemy["angle"]) < 10
                    }
            else:
                # Longer range - approach and shoot
                return {
                    "rotate": self._calculate_turn_rate(nearest_enemy["angle"]),
                    "thrust": 0.5 if abs(nearest_enemy["angle"]) < 30 else 0.2,
                    "shoot": abs(nearest_enemy["angle"]) < 5 and nearest_enemy["distance"] < 300
                }
        
        # If no enemies but coins found, collect nearest coin
        elif coins:
            # Sort by distance
            coins.sort(key=lambda x: x["distance"])
            nearest_coin = coins[0]
            
            # Save coin in memory
            self.target_memory = {
                "type": "coin",
                "distance": nearest_coin["distance"],
                "angle": nearest_coin["angle"],
                "last_seen": current_time
            }
            
            # Calculate how to reach the coin
            turn_rate = self._calculate_turn_rate(nearest_coin["angle"], aggressive=False)
            
            # Adjust thrust based on angle - slow down when turning sharply
            thrust_value = 1.0 if abs(nearest_coin["angle"]) < 30 else 0.5
            
            # Move toward coin
            return {
                "rotate": turn_rate, 
                "thrust": thrust_value, 
                "shoot": False
            }
        
        # Check if we have a recent memory of an object
        elif self.target_memory["type"] and (current_time - self.target_memory["last_seen"]) < 2.0:
            # Continue moving toward the last known position
            print(f"Following memory of {self.target_memory['type']}")
            return {
                "rotate": self._calculate_turn_rate(self.target_memory["angle"]), 
                "thrust": 0.7,
                "shoot": False
            }
        
        # No objects detected - explore in a smarter pattern
        else:
            # Change direction periodically
            if current_time - self.last_direction_change > 3.0:
                self.current_rotation = random.uniform(-2, 2)
                self.last_direction_change = current_time
                
            return {
                "rotate": self.current_rotation,
                "thrust": 0.5,
                "shoot": False
            }

    def _calculate_turn_rate(self, angle, aggressive=False):
        """Calculate appropriate turn rate based on angle and situation."""
        # For coin collection, use gentler turns
        if not aggressive:  # Coin collection mode
            # For small angles, even more gentle proportional control
            if abs(angle) < 20:
                return angle * 0.15  # More gentle turn (was 0.2)
                
            # For medium angles, slower turn
            elif abs(angle) < 90:
                return 3 * (1 if angle > 0 else -1)  # Reduced from 5 to 3
                
            # For large angles, reduced turn rate
            else:
                return 4 * (1 if angle > 0 else -1)  # Reduced from 5 to 4
        
        # For combat (aggressive mode), keep existing values
        else:
            # For small angles, proportional control
            if abs(angle) < 20:
                return angle * 0.2
            # For medium angles, faster turn
            elif abs(angle) < 90:
                return 5 * (1 if angle > 0 else -1)
            # For large angles, max turn rate
            else:
                return 8 * (1 if angle > 0 else -1)

    def _random_action(self):
        """Generate random action when no sensor data is available."""
        return {
            "rotate": random.uniform(-3, 3),
            "thrust": random.uniform(0.1, 0.5),
            "shoot": random.random() < 0.05
        }

    # Combined decide method that uses sensors when possible
    def decide(self, game_state, walls):
        """Main decision method that uses sensor data if possible."""
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
        """Legacy decision method - only used for testing without server."""
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
        """Check if a line intersects with a rectangle."""
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

    """
    def _is_wall_ahead(self, x, y, angle, walls):
        
        Checks if there is a wall directly in front of the agent.
        
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
    """

    def _update_stuck_detection(self, sensor_data):
        """Update the stuck detection system based on current position"""
        current_time = time.time()
        
        # Extract position from sensor request if available
        current_pos = None
        if hasattr(sensor_data, "position"):
            current_pos = (sensor_data.position["x"], sensor_data.position["y"])
        
        # Initialize if first check
        if self.stuck_detection["position"] is None and current_pos:
            self.stuck_detection["position"] = current_pos
            self.stuck_detection["last_position"] = current_pos
            self.stuck_detection["check_time"] = current_time
            self.stuck_detection["last_check_time"] = current_time
            return
        
        if current_pos:
            # If we didn't move much in the last check
            dx = current_pos[0] - self.stuck_detection["position"][0]
            dy = current_pos[1] - self.stuck_detection["position"][1]
            distance_moved = math.sqrt(dx*dx + dy*dy)
            
            # If barely moved in the last second
            if distance_moved < 5:
                self.stuck_detection["stuck_count"] += 1
                if self.stuck_detection["stuck_count"] >= 3:
                    self.stuck_detection["is_stuck"] = True
            else:
                # Reset if we're moving
                self.stuck_detection["is_stuck"] = False
                self.stuck_detection["stuck_count"] = max(0, self.stuck_detection["stuck_count"] - 1)
            
            # Update position for next check
            self.stuck_detection["last_position"] = self.stuck_detection["position"]
            self.stuck_detection["position"] = current_pos
            
        # Reset timer for next check
        self.stuck_detection["last_check_time"] = self.stuck_detection["check_time"]
        self.stuck_detection["check_time"] = current_time


