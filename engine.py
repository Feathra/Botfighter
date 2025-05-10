import time
import pygame
import math
import random
import requests
import json
import threading
import os
from dummy_agent import DummyAgent

# Set world size and screen dimensions
WORLD_WIDTH, WORLD_HEIGHT = 2000, 2000
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600

# Define colors
WHITE = (255, 255, 255)
BLUE = (50, 100, 255)
RED = (255, 50, 50)
GREEN = (50, 200, 50)
GOLD = (255, 215, 0)

# Define enemy patrol states
PATROL_STATE_FORWARD = 0
PATROL_STATE_TURNING = 1
PATROL_STATE_WALL_AVOID = 2

# Try to connect to server, fallback to local if not available
SERVER_URL = "http://localhost:8000"
BACKUP_URLS = ["http://localhost:8080", "http://localhost:8888", "http://localhost:9000"]
ACCESS_SERVER_FLAG = False

def try_server_connection():
    """Try to connect to any available server"""
    global SERVER_URL, ACCESS_SERVER_FLAG
    
    urls = [SERVER_URL] + BACKUP_URLS
    for url in urls:
        try:
            response = requests.get(f"{url}/walls", timeout=0.5)
            response.raise_for_status()
            SERVER_URL = url
            ACCESS_SERVER_FLAG = True
            print(f"Connected to server at {url}")
            return True
        except Exception as e:
            print(f"Failed to connect to {url}: {e}")
    
    print("No server connection available. Using local mode.")
    return False

# Try to establish connection
try_server_connection()

# ------------------------
# SpaceObject Class (Physics)
# ------------------------
class SpaceObject:
    """Base class for physics objects in the game."""
    
    def __init__(self, x, y, angle=0, velocity_x=0, velocity_y=0, hp=100, WORLD_WIDTH=2000, WORLD_HEIGHT=2000, concurrents=None):
        self.WORLD_WIDTH = WORLD_WIDTH
        self.WORLD_HEIGHT = WORLD_HEIGHT
        self.x = x
        self.y = y
        self.angle = angle
        self.vx = velocity_x  # Initial velocity
        self.vy = velocity_y
        self.hp = hp  # Health points
        self.concurrents = concurrents
        self.patrol_state = PATROL_STATE_FORWARD
        self.patrol_timer = 0
        self.patrol_turn_target = 0
        self.patrol_direction = 1

    def update_position(self, is_enemy=False):
        """Update the position based on velocity with friction and speed limits."""
        max_speed = 8 if not is_enemy else 3  # Player: 8, Enemy: 3
        friction = 0.99  # Friction effect
        self.vx *= friction
        self.vy *= friction
        self.vx = max(-max_speed, min(self.vx, max_speed))
        self.vy = max(-max_speed, min(self.vy, max_speed))
        self.x += self.vx
        self.y += self.vy
        self.x = max(0, min(self.x, self.WORLD_WIDTH))
        self.y = max(0, min(self.y, self.WORLD_HEIGHT))

    def thrust(self, amount):
        """Apply thrust in the direction of the ship's angle."""
        rad = math.radians(self.angle)
        self.vx += math.cos(rad) * amount
        self.vy += math.sin(rad) * amount

    def rotate(self, degrees):
        """Rotate the ship by a specified number of degrees."""
        self.angle = (self.angle + degrees) % 360

    def get_state(self):
        """Get the current state as a dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "vy": self.vy,
            "angle": self.angle,
        }
        
    def check_wall_collision(self, walls):
        """Check for collision with walls and adjust position/velocity."""
        ship_rect = pygame.Rect(self.x - 10, self.y - 10, 20, 20)  # Size of the ship
        concurrent_react = [pygame.Rect(so.x - 10, so.y - 10, 20, 20) for so in self.concurrents if so is not self] if self.concurrents else []
        
        for wall in walls+concurrent_react:
            if ship_rect.colliderect(wall):
                # Bounce back based on direction
                if self.x < wall.x:  # Left of the wall
                    self.x = wall.x - 10
                    self.vx = 0
                elif self.x > wall.x + wall.width:  # Right of the wall
                    self.x = wall.x + wall.width + 10
                    self.vx = 0
                if self.y < wall.y:  # Above the wall
                    self.y = wall.y - 10
                    self.vy = 0
                elif self.y > wall.y + wall.height:  # Below the wall
                    self.y = wall.y + wall.height + 10
                    self.vy = 0

# ------------------------
# Bullet Class
# ------------------------   
class Bullet:
    """Class representing bullets fired by ships."""
    
    def __init__(self, x, y, angle, owner, speed=15, lifespan=60):
        self.x = x
        self.y = y
        self.angle = angle
        self.owner = owner
        self.lifespan = lifespan  # Lifespan in frames
        rad = math.radians(angle)
        self.vx = math.cos(rad) * speed
        self.vy = math.sin(rad) * speed
        
    def update(self):
        """Update the bullet position and decrease lifespan."""
        self.x += self.vx
        self.y += self.vy
        self.lifespan -= 1

    def is_offscreen(self, world_width, world_height):
        """Check if the bullet is offscreen or expired."""
        return not (0 <= self.x <= world_width and 0 <= self.y <= world_height) or self.lifespan <= 0

# ------------------------
# Coin Class
# ------------------------
class Coin:
    """Class representing collectible coins in the game."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # Make the coin rectangle slightly larger for easier collection
        self.rect = pygame.Rect(self.x - 8, self.y - 10, 16, 20)

    def draw(self, screen, camera_x, camera_y):
        """Draw the coin with a pulsing effect."""
        coin_screen_x = self.rect.x - camera_x + SCREEN_WIDTH // 2
        coin_screen_y = self.rect.y - camera_y + SCREEN_HEIGHT // 2
        
        # Draw a slightly larger and more visible coin
        pygame.draw.ellipse(screen, GOLD, (coin_screen_x, coin_screen_y, self.rect.width, self.rect.height))
        pygame.draw.ellipse(screen, (255, 255, 0), (coin_screen_x+2, coin_screen_y+2, self.rect.width-4, self.rect.height-4))
        
        # Add a pulsing effect to make coins more noticeable
        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 2
        pygame.draw.ellipse(screen, (255, 255, 200), (coin_screen_x+4-pulse, coin_screen_y+4-pulse, 
                                                     self.rect.width-8+pulse*2, self.rect.height-8+pulse*2))

    def collides_with(self, ship_rect):
        """Check if the coin collides with a ship."""
        return self.rect.colliderect(ship_rect)

# ------------------------
# GameEngine Class
# ------------------------
class GameEngine:
    """Main game engine class that manages the game state."""
    
    def __init__(self, walls):
        self.ships = []
        self.ships.append(SpaceObject(*generate_valid_position(walls, WORLD_WIDTH, WORLD_HEIGHT), concurrents=self.ships))
        self.ships.append(SpaceObject(*generate_valid_position(walls, WORLD_WIDTH, WORLD_HEIGHT), concurrents=self.ships))
        self.bullets = [] 
        self.score = [0, 0]
        self.time = 0
        self.coins = generate_coins(20, walls)
        self.last_state_update_time = None
        self.state_update_min_period = 0.1  # 10 times per second

    def update(self, walls):
        """Update the game state (ships, bullets, collisions)."""
        # Update ships
        new_ships = []
        for i, ship in enumerate(self.ships[:]):
            is_enemy = (i == 1)  # The enemy is the second ship
            ship.update_position(is_enemy=is_enemy)
            ship.check_wall_collision(walls)  # Wall collision check
            
            if ship.hp <= 0:  # Remove the ship if HP is 0
                self.ships.remove(ship)
                if is_enemy:  # If an enemy dies, double the number of enemies
                    for _ in range(2):  # Add two new enemies
                        x, y = generate_valid_position(walls, WORLD_WIDTH, WORLD_HEIGHT)
                        new_ships.append(SpaceObject(x, y, angle=random.randint(0, 360), hp=100, concurrents=self.ships))
        
        self.ships.extend(new_ships)

        # Update bullets
        for bullet in self.bullets:
            bullet.update()
            
        new_bullets = []
        for bullet in self.bullets:
            hit = False
            
            # Check for collisions with walls
            bullet_rect = pygame.Rect(bullet.x - 3, bullet.y - 3, 6, 6)  # Bullet size
            for wall in walls:
                if bullet_rect.colliderect(wall):
                    hit = True
                    break

            # Check for collisions with ships
            for i, ship in enumerate(self.ships):
                if i != bullet.owner and self._collides(bullet, ship):  # Avoid friendly fire
                    ship.hp -= 10  # Damage dealt
                    hit = True
                    if ship.hp <= 0 and i == 1:  # Points for killing an enemy
                        self.score[0] += 10  # Player earns 10 points
                    print(f"Ship {i} hit! HP: {ship.hp}")

            # Add bullet to the new list if it hasn't hit anything and its lifespan is not over
            if not hit and bullet.lifespan > 0:
                new_bullets.append(bullet)

        self.bullets = [b for b in new_bullets if not b.is_offscreen(WORLD_WIDTH, WORLD_HEIGHT)]

        # Update server with latest state
        self.update_state_on_server()

    def update_state_on_server(self):
        """Send current game state to the server if connected."""
        if not ACCESS_SERVER_FLAG or (self.last_state_update_time and time.time() - self.last_state_update_time < self.state_update_min_period):
            return

        # Create payload
        state = {
            "ships": [{"x": ship.x, "y": ship.y, "angle": ship.angle} for ship in self.ships],
            "bullets": [{"x": bullet.x, "y": bullet.y, "angle": bullet.angle, "lifespan": bullet.lifespan, "owner": bullet.owner} for bullet in self.bullets],
            "coins": [{"x": coin.x, "y": coin.y} for coin in self.coins],
            "score": self.score
        }
        
        # Send in background thread to avoid blocking game loop
        def send_state():
            try:
                requests.post(f"{SERVER_URL}/update_state", json=state, timeout=0.5)
            except Exception as e:
                print(f"Error sending state: {e}")
        
        threading.Thread(target=send_state).start()
        self.last_state_update_time = time.time()

    def get_agent_actions(self, game_state, walls):
        """Get agent actions using only sensor data through the server."""
        try:
            if not ACCESS_SERVER_FLAG:
                # Fallback to direct control when server is not available
                dummy_agent = DummyAgent(ship_index=0)
                return dummy_agent.decide(game_state, walls)
                
            # Prepare ship data
            ship = self.ships[0]  # Agent ship
            
            # Create payload with minimal required data
            payload = {
                "ship_id": 0,
                "ships": [{
                    "x": ship.x,
                    "y": ship.y,
                    "angle": ship.angle
                }]
            }
            
            # Get decision from server (which will use sensors internally)
            response = requests.post(f"{SERVER_URL}/decide/", json=payload, timeout=0.2)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error communicating with agent server: {e}")
            # Fall back to direct control with what information we have
            dummy_agent = DummyAgent(ship_index=0)
            return dummy_agent.decide(game_state, walls)
   
    def shoot(self, ship_index):
        """Create a new bullet from the specified ship."""
        ship = self.ships[ship_index]
        # Spawn bullet slightly in front of the ship
        rad = math.radians(ship.angle)
        bullet_x = ship.x + math.cos(rad) * 15
        bullet_y = ship.y + math.sin(rad) * 15
        bullet = Bullet(bullet_x, bullet_y, ship.angle, owner=ship_index, speed=15)
        self.bullets.append(bullet)

    def draw_bullets(self, screen, camera_x, camera_y):
        """Draw all bullets on screen."""
        for bullet in self.bullets:
            screen_x, screen_y = world_to_screen(bullet.x, bullet.y, camera_x, camera_y)
            pygame.draw.circle(screen, (0, 0, 0), (screen_x, screen_y), 3)

    def draw_coins(self, screen, camera_x, camera_y):
        """Draw all coins on screen."""
        for coin in self.coins:
            coin.draw(screen, camera_x, camera_y)
    
    def rotate_ship(self, index, degrees):
        """Rotate the ship at the given index."""
        self.ships[index].rotate(degrees)
    
    def thrust_ship(self, index, amount):
        """Apply thrust to the ship at the given index."""
        self.ships[index].thrust(amount)

    def get_game_state(self):
        """Get the current game state as a dictionary."""
        return {
            "ships": [ship.get_state() for ship in self.ships],
            "score": self.score,
            "time": self.time
        }
        
    def _collides(self, bullet, ship):
        """Check if a bullet collides with a ship."""
        dist = math.hypot(bullet.x - ship.x, bullet.y - ship.y)
        return dist < 15  # Simple collision radius

# ------------------------
# Helper Functions
# ------------------------
def world_to_screen(x, y, camera_x, camera_y):
    """Convert world coordinates to screen coordinates."""
    return int(x - camera_x + SCREEN_WIDTH // 2), int(y - camera_y + SCREEN_HEIGHT // 2)

def draw_ship(screen, ship, color, camera_x, camera_y):
    """Draw a ship on the screen."""
    screen_x, screen_y = world_to_screen(ship.x, ship.y, camera_x, camera_y)
    angle = ship.angle
    length = 20
    rad = math.radians(angle)
    end_x = screen_x + math.cos(rad) * length
    end_y = screen_y + math.sin(rad) * length
    pygame.draw.circle(screen, color, (screen_x, screen_y), 10)
    pygame.draw.line(screen, color, (screen_x, screen_y), (int(end_x), int(end_y)), 2)

def create_labyrinth():
    """Create a labyrinth of walls for the game."""
    walls = [
        # Outer walls
        pygame.Rect(50, 50, 1900, 20),  # Top wall
        pygame.Rect(50, 50, 20, 1900),  # Left wall
        pygame.Rect(50, 1930, 1900, 20),  # Bottom wall
        pygame.Rect(1930, 50, 20, 1900),  # Right wall

        # Inner structures
        pygame.Rect(200, 200, 20, 400),  # Vertical wall top left
        pygame.Rect(200, 600, 400, 20),  # Horizontal wall top left
        pygame.Rect(600, 200, 20, 400),  # Vertical wall top center
        pygame.Rect(600, 600, 400, 20),  # Horizontal wall top center
        pygame.Rect(1000, 200, 20, 800),  # Vertical wall top right
        pygame.Rect(200, 1000, 800, 20),  # Horizontal wall center
        pygame.Rect(1200, 200, 20, 800),  # Vertical wall center right
        pygame.Rect(1200, 1000, 400, 20),  # Horizontal wall center right
        pygame.Rect(1600, 200, 20, 800),  # Vertical wall top far right
        pygame.Rect(200, 1400, 400, 20),  # Horizontal wall bottom left
        pygame.Rect(600, 1400, 20, 400),  # Vertical wall bottom center
        pygame.Rect(600, 1800, 400, 20),  # Horizontal wall bottom center
        pygame.Rect(1000, 1400, 20, 400),  # Vertical wall bottom right
        pygame.Rect(1200, 1400, 400, 20),  # Horizontal wall bottom right
        pygame.Rect(1600, 1400, 20, 400),  # Vertical wall bottom far right

        # Dead ends
        pygame.Rect(300, 300, 100, 20),  # Horizontal dead end top left
        pygame.Rect(1500, 1500, 100, 20),  # Horizontal dead end bottom right
        pygame.Rect(800, 800, 20, 100),  # Vertical dead end center
    ]
    
    # Try to get walls from server
    if ACCESS_SERVER_FLAG:
        try:
            response = requests.get(f"{SERVER_URL}/walls", timeout=0.5)
            response.raise_for_status()
            data = response.json()
            walls_coords = data.get("walls", [])
            if walls_coords:
                print(f"Loaded {len(walls_coords)} walls from server")
                return [pygame.Rect(wall["x"], wall["y"], wall["width"], wall["height"]) for wall in walls_coords]
        except Exception as e:
            print(f"Error loading walls from server: {e}")
    
    return walls

def generate_valid_position(walls, world_width, world_height):
    """Generate a random position that is not inside any wall."""
    max_attempts = 100
    for _ in range(max_attempts):
        x = random.randint(100, world_width - 100)
        y = random.randint(100, world_height - 100)
        rect = pygame.Rect(x - 10, y - 10, 20, 20)  # Approximate ship size
        
        is_valid = True
        for wall in walls:
            if rect.colliderect(wall):
                is_valid = False
                break
        
        if is_valid:
            return x, y
            
    # Fallback positions if random generation fails
    fallback_positions = [(400, 400), (1600, 1600), (400, 1600), (1600, 400)]
    return random.choice(fallback_positions)

def generate_coins(num_coins, walls):
    """Generate coins in valid positions."""
    coins = []
    for _ in range(num_coins):
        for _ in range(100):  # Try up to 100 times per coin
            x = random.randint(100, WORLD_WIDTH - 100)
            y = random.randint(100, WORLD_HEIGHT - 100)
            coin = Coin(x, y)
            
            is_valid = True
            for wall in walls:
                if coin.rect.colliderect(wall):
                    is_valid = False
                    break
                    
            if is_valid:
                coins.append(coin)
                break
                
    print(f"Generated {len(coins)} coins")
    return coins

def show_start_menu(screen):
    """Show the game start menu."""
    font = pygame.font.SysFont(None, 48)
    title_font = pygame.font.SysFont(None, 72)
    
    title = title_font.render("BotFighter Arena", True, (0, 0, 150))
    text_player = font.render("Play as Player (Press P)", True, (0, 0, 0))
    text_agent = font.render("Watch Agent (Press A)", True, (0, 0, 0))
    text_quit = font.render("Quit (Press Q)", True, (0, 0, 0))
    
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
    text_player_rect = text_player.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    text_agent_rect = text_agent.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
    text_quit_rect = text_quit.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))

    running_menu = True
    
    while running_menu:
        screen.fill((220, 220, 255))
        screen.blit(title, title_rect)
        screen.blit(text_player, text_player_rect)
        screen.blit(text_agent, text_agent_rect)
        screen.blit(text_quit, text_quit_rect)
        
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    return "player"
                elif event.key == pygame.K_a:
                    return "agent"
                elif event.key == pygame.K_q:
                    pygame.quit()
                    exit()

def show_game_over(screen, score):
    """Show game over screen with restart option."""
    font = pygame.font.SysFont(None, 48)
    score_font = pygame.font.SysFont(None, 36)
    
    game_over_text = font.render("Game Over!", True, (255, 0, 0))
    score_text = score_font.render(f"Final Score: {score}", True, (0, 0, 0))
    restart_text = font.render("Press R to Restart or Q to Quit", True, (0, 0, 0))
    
    game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    
    screen.fill(WHITE)
    screen.blit(game_over_text, game_over_rect)
    screen.blit(score_text, score_rect)
    screen.blit(restart_text, restart_rect)
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True  # Restart
                elif event.key == pygame.K_q:
                    pygame.quit()
                    exit()

def patrol_movement(enemy, walls):
    """Move enemy in a more logical patrolling pattern."""
    # Update patrol timer
    enemy.patrol_timer += 1
    
    # Check for walls ahead to avoid
    ship_rect = pygame.Rect(enemy.x - 10, enemy.y - 10, 20, 20)
    ahead_distance = 80  # Look further ahead for patrol
    rad = math.radians(enemy.angle)
    look_x = enemy.x + math.cos(rad) * ahead_distance
    look_y = enemy.y + math.sin(rad) * ahead_distance
    look_rect = pygame.Rect(look_x - 10, look_y - 10, 20, 20)
    
    # Wall detection
    wall_ahead = False
    for wall in walls:
        if look_rect.colliderect(wall):
            wall_ahead = True
            break
    
    # State machine for more logical movement
    if enemy.patrol_state == PATROL_STATE_FORWARD:
        # Move forward until timer expires or wall detected
        enemy.thrust(0.2)  # Consistent thrust
        
        # Occasionally make course adjustments
        if enemy.patrol_timer % 60 == 0:  # Every ~1 second
            # Small course adjustment
            enemy.rotate(random.uniform(-2, 2))
        
        # Change to turning state periodically
        if enemy.patrol_timer > 180 and random.random() < 0.01:  # ~3 seconds forward
            enemy.patrol_state = PATROL_STATE_TURNING
            enemy.patrol_timer = 0
            # Choose a turn amount between 70-110 degrees for more natural corners
            enemy.patrol_turn_target = random.choice([-1, 1]) * random.randint(70, 110)
            enemy.patrol_direction = 1 if enemy.patrol_turn_target > 0 else -1
            
        # Wall avoidance takes priority
        if wall_ahead:
            enemy.patrol_state = PATROL_STATE_WALL_AVOID
            enemy.patrol_timer = 0
            
    elif enemy.patrol_state == PATROL_STATE_TURNING:
        # Gradual turning to target angle
        turn_amount = min(2.0, abs(enemy.patrol_turn_target) * 0.1)
        enemy.rotate(turn_amount * enemy.patrol_direction)
        enemy.patrol_turn_target -= turn_amount * enemy.patrol_direction
        
        # Keep some momentum while turning
        enemy.thrust(0.1)
        
        # When turn complete or timer expires, go back to forward
        if abs(enemy.patrol_turn_target) < 5 or enemy.patrol_timer > 120:
            enemy.patrol_state = PATROL_STATE_FORWARD
            enemy.patrol_timer = 0
            
        # Wall avoidance still takes priority
        if wall_ahead:
            enemy.patrol_state = PATROL_STATE_WALL_AVOID
            enemy.patrol_timer = 0
            
    elif enemy.patrol_state == PATROL_STATE_WALL_AVOID:
        # More aggressive wall avoidance
        # Turn perpendicular to our current direction
        enemy.rotate(4 * enemy.patrol_direction)
        
        # Apply reverse thrust
        if enemy.patrol_timer < 15:
            enemy.thrust(-0.2)
        
        # Check if we're now clear of walls
        if enemy.patrol_timer > 30 and not wall_ahead:
            enemy.patrol_state = PATROL_STATE_FORWARD
            enemy.patrol_timer = 0
            # Switch patrol direction for variety
            enemy.patrol_direction *= -1
            
        # If wall avoidance is taking too long, force a state change
        if enemy.patrol_timer > 90:  # ~1.5 seconds
            enemy.patrol_state = PATROL_STATE_TURNING
            enemy.patrol_timer = 0
            enemy.patrol_turn_target = 180  # Try to turn completely around
            
    return wall_ahead

def avoid_walls(ship, walls):
    """Make a ship avoid nearby walls."""
    ship_rect = pygame.Rect(ship.x - 10, ship.y - 10, 20, 20)
    # Check further ahead (50 pixels instead of 30)
    lookahead_rect = ship_rect.inflate(50, 50)
    
    for wall in walls:
        if lookahead_rect.colliderect(wall):
            # Simple avoidance: rotate away from the center of the wall
            wall_center_x = wall.x + wall.width // 2
            wall_center_y = wall.y + wall.height // 2
            angle_to_wall = math.degrees(math.atan2(wall_center_y - ship.y, wall_center_x - ship.x))
            angle_difference = (angle_to_wall - ship.angle + 360) % 360
            
            # Faster rotation to avoid walls
            if angle_difference > 180:
                ship.rotate(5)  # Rotate right faster
            else:
                ship.rotate(-5)  # Rotate left faster
                
            # Apply reverse thrust to move away from wall
            ship.thrust(-0.3)
            return True  # Wall detected
    
    return False  # No wall detected

def can_see_player(enemy, player, walls):
    """Check if the enemy has a clear line of sight to the player."""
    dx = player.x - enemy.x
    dy = player.y - enemy.y
    distance = math.hypot(dx, dy)
    steps = int(distance / 10)  # Divide the line into steps

    for step in range(1, steps):  # Skip first step to avoid self-collision
        check_x = enemy.x + dx * (step / steps)
        check_y = enemy.y + dy * (step / steps)
        check_rect = pygame.Rect(check_x - 5, check_y - 5, 10, 10)  # Small area to check
        for wall in walls:
            if check_rect.colliderect(wall):
                return False  # Wall blocks the view
    return True

def chase_player(enemy, player):
    """Make the enemy rotate and thrust towards the player."""
    dx = player.x - enemy.x
    dy = player.y - enemy.y
    angle_to_target = math.degrees(math.atan2(dy, dx))
    angle_difference = (angle_to_target - enemy.angle + 360) % 360
    if angle_difference > 180:
        angle_difference -= 360

    enemy.rotate(angle_difference * 0.1)
    enemy.thrust(0.3)

def chase_and_shoot(enemy, player, walls, engine):
    """Make the enemy chase and shoot at the player if visible."""
    if can_see_player(enemy, player, walls):
        # Chase the player
        chase_player(enemy, player)

        # Shoot at the player
        if random.random() < 0.02:  # 2% chance per frame
            engine.shoot(engine.ships.index(enemy))  # Enemy shoots
    else:
        # Improved patrol behavior when player not visible
        wall_detected = patrol_movement(enemy, walls)
        
        # If wall detection failed in patrol, use backup avoidance
        if wall_detected and enemy.patrol_state != PATROL_STATE_WALL_AVOID:
            avoid_walls(enemy, walls)

def main():
    """Main game function."""
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("BotFighter Arena")

    # Make sure the background image exists, create a simple one if not
    background_path = "galaxie.jpg"
    if not os.path.exists(background_path):
        # Create a simple starfield background
        background = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
        background.fill((0, 0, 30))  # Dark blue
        for _ in range(1000):
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            radius = random.randint(1, 3)
            brightness = random.randint(150, 255)
            pygame.draw.circle(background, (brightness, brightness, brightness), (x, y), radius)
        pygame.image.save(background, background_path)
        print(f"Created new background image: {background_path}")
    
    # Load background
    try:
        background_image = pygame.image.load(background_path)
        background_image = pygame.transform.scale(background_image, (WORLD_WIDTH, WORLD_HEIGHT))
    except pygame.error:
        print(f"Error loading background image. Using plain background.")
        background_image = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
        background_image.fill((0, 0, 30))  # Dark blue background

    # Create transparent overlay
    transparent_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
    transparent_surface.blit(background_image, (0, 0))
    transparent_surface.set_alpha(128)  # Semi-transparent

    # Create info box
    info_box = pygame.Surface((150, 60), pygame.SRCALPHA)
    info_box.fill((128, 128, 128, 160))  # Semi-transparent gray

    walls = create_labyrinth()
    clock = pygame.time.Clock()
    game_over = False

    # Main game loop
    while True:
        mode = show_start_menu(screen)
        engine = GameEngine(walls)
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

            # Check game over condition
            if len(engine.ships) == 0 or (len(engine.ships) > 0 and engine.ships[0].hp <= 0):
                game_over = True
                running = False
                continue

            # Get player ship
            player = engine.ships[0] if len(engine.ships) > 0 else None
            if not player:
                game_over = True
                running = False
                continue

            # Camera follows player
            camera_x = player.x
            camera_y = player.y

            # Clear screen and draw background
            screen.fill(WHITE)
            screen.blit(transparent_surface, (-camera_x + SCREEN_WIDTH // 2, -camera_y + SCREEN_HEIGHT // 2))

            # Draw walls
            for wall in walls:
                wall_screen = pygame.Rect(
                    wall.x - camera_x + SCREEN_WIDTH // 2,
                    wall.y - camera_y + SCREEN_HEIGHT // 2,
                    wall.width,
                    wall.height
                )
                pygame.draw.rect(screen, (80, 80, 80), wall_screen)

            # Draw coins
            engine.draw_coins(screen, camera_x, camera_y)

            # Check coin collection
            player_rect = pygame.Rect(player.x - 20, player.y - 20, 40, 40)
            for coin in engine.coins[:]:
                if coin.collides_with(player_rect):
                    engine.coins.remove(coin)
                    engine.score[0] += 1
                    print(f"Coin collected! {len(engine.coins)} coins remaining")
                    # Generate a new coin to replace the collected one
                    if len(engine.coins) < 10:
                        new_coin = generate_coins(1, walls)
                        if new_coin:
                            engine.coins.extend(new_coin)

            # Player controls or agent actions
            if mode == "player":
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]:
                    engine.rotate_ship(0, -3)
                if keys[pygame.K_RIGHT]:
                    engine.rotate_ship(0, 3)
                if keys[pygame.K_UP]:
                    engine.thrust_ship(0, 1)
                if keys[pygame.K_SPACE]:
                    engine.shoot(0)
            elif mode == "agent" and player:
                game_state = {
                    "ships": [{
                        "x": player.x,
                        "y": player.y,
                        "angle": player.angle
                    }]
                }
                actions = engine.get_agent_actions(game_state, walls)
                
                engine.rotate_ship(0, actions["rotate"])
                engine.thrust_ship(0, actions["thrust"])
                if actions["shoot"]:
                    engine.shoot(0)

            # Enemy movement and behavior
            for i, enemy in enumerate(engine.ships):
                if i == 0:  # Skip the player (index 0)
                    continue
                chase_and_shoot(enemy, player, walls, engine)

            # Update game state
            engine.update(walls)

            # Draw ships
            for i, ship in enumerate(engine.ships):
                color = BLUE if i == 0 else RED
                draw_ship(screen, ship, color, camera_x, camera_y)

                # If the ship is an enemy, draw its HP
                if i != 0:
                    enemy_screen_x, enemy_screen_y = world_to_screen(ship.x, ship.y, camera_x, camera_y)
                    font = pygame.font.SysFont(None, 24)
                    hp_text = font.render(f"{ship.hp}", True, (255, 0, 0))
                    screen.blit(hp_text, (enemy_screen_x + 15, enemy_screen_y - 15))

            # Display HP and Score
            font = pygame.font.SysFont(None, 24)
            p1_hp = engine.ships[0].hp
            hp_text = font.render(f"Player HP: {p1_hp}", True, (0, 0, 0))
            score_text = font.render(f"Score: {engine.score[0]}", True, (0, 0, 0))

            # Draw the info box and text
            screen.blit(info_box, (10, 10))
            screen.blit(hp_text, (20, 20))
            screen.blit(score_text, (20, 40))

            # Draw bullets
            engine.draw_bullets(screen, camera_x, camera_y)

            pygame.display.flip()
            clock.tick(60)  # Limit to 60 FPS

        # Game over screen
        if game_over:
            restart = show_game_over(screen, engine.score[0])
            if restart:
                game_over = False
                continue
            else:
                break

    pygame.quit()

if __name__ == "__main__":
    main()
