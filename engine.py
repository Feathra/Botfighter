import time
import pygame
import math
import random
import requests  # Import the requests library
import json

from dummy_agent import DummyAgent
# ------------------------
# SpaceObject Class (Physics)
# ------------------------

# This class represents the ships and their physics in the game.
# It handles the position, velocity, rotation, and collision with walls.
# The ships can move, rotate, and apply thrust. The class also manages the health points (HP) of the ships.
class SpaceObject:
    
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

    # Update the position of the ship based on its velocity and angle.
    # The ship's velocity is affected by friction, and it is clamped to a maximum speed.    
    def update_position(self, is_enemy=False):
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
        #print(f"Ship position updated to ({self.x}, {self.y}) with velocity ({self.vx}, {self.vy})")

    # Apply thrust in the direction of the ship's angle.
    # The thrust amount is added to the ship's velocity in the x and y directions.
    def thrust(self, amount):
        rad = math.radians(self.angle)
        self.vx += math.cos(rad) * amount
        self.vy += math.sin(rad) * amount

    ## Rotate the ship by a specified number of degrees.
    # The angle is clamped to the range [0, 360) degrees.
    def rotate(self, degrees):
        self.angle = (self.angle + degrees) % 360

    # Get the current state of the ship, including position, velocity, and angle.
    # This is useful for saving or sending the state of the ship.
    # The state is returned as a dictionary.
    def get_state(self):
        return {
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "vy": self.vy,
            "angle": self.angle,
        }
        
    # Check for collision with walls.
    # If a collision is detected, the ship's position and velocity are adjusted accordingly.
    # The ship is moved back to the edge of the wall, and its velocity is set to zero.

    def check_wall_collision(self, walls):
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

# This class represents the bullets fired by the ships.
# Each bullet has a position, angle, owner (ship index), and speed.     
class Bullet:
    def __init__(self, x, y, angle, owner, speed=15, lifespan=60):  # Lifespan in frames (1 second at 60 FPS)
        self.x = x
        self.y = y
        self.angle = angle
        self.owner = owner
        self.lifespan = lifespan  # Lifespan in frames
        rad = math.radians(angle)
        self.vx = math.cos(rad) * speed
        self.vy = math.sin(rad) * speed
        
    # Update the position of the bullet based on its velocity.
    # The bullet moves in the direction of its angle.
    # The position is updated by adding the velocity to the current position.
    def update(self):
        # Update position
        self.x += self.vx
        self.y += self.vy
        # Decrease lifespan
        self.lifespan -= 1

    # Check if the bullet is offscreen.
    # The bullet is considered offscreen if it is outside the world boundaries.
    def is_offscreen(self, world_width, world_height):
        # Check if the bullet is offscreen or its lifespan has expired
        return not (0 <= self.x <= world_width and 0 <= self.y <= world_height) or self.lifespan <= 0

SERVER_URL = "http://localhost:8000"  # Adjust if your server runs elsewhe
ACCESS_SERVER_FLAG = False
try:
    response = requests.get(SERVER_URL + "/walls")
    response.raise_for_status()
    ACCESS_SERVER_FLAG = True
except Exception as e:
    print(f"No connection to the server: {e}")

# ------------------------
# GameEngine Class
# ------------------------

# This class manages the game state, including the ships, bullets, score, and time.
# It handles the game logic, including updating the positions of the ships and bullets,
class GameEngine:
    def __init__(self, walls):
        self.ships = []
        self.ships.append(SpaceObject(*generate_valid_position(walls, WORLD_WIDTH, WORLD_HEIGHT), concurrents=self.ships))
        self.ships.append(SpaceObject(*generate_valid_position(walls, WORLD_WIDTH, WORLD_HEIGHT), concurrents=self.ships))
        self.bullets = [] 
        self.score = [0, 0]
        self.time = 0
        self.coins = generate_coins(20, walls)  # Store coins in GameEngine
        self.last_state_update_time = None
        self.state_update_min_period = 0.2  # 5 times per sec


    # Update the game state.
    # This includes updating the positions of the ships and bullets, checking for collisions,
    def update(self, walls):
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
                        new_ships.append(SpaceObject(x, y, angle=random.randint(0, 360), hp=100, concurrents = self.ships))
        self.ships.extend(new_ships)

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

        self.bullets = [b for b in new_bullets if not b.is_offscreen(self.ships[0].WORLD_WIDTH, self.ships[0].WORLD_HEIGHT)]

        # После всей логики обновления собираем данные и отправляем на сервер
        self.update_state_on_server()

    def update_state_on_server(self):
        if not ACCESS_SERVER_FLAG:
            return

        if self.last_state_update_time and time.time() - self.last_state_update_time < self.state_update_min_period:
            return

        ships_data = []
        for ship in self.ships:
            ships_data.append({
                "x": ship.x,
                "y": ship.y,
                "angle": ship.angle,
                "hp": ship.hp
            })

        bullets_data = []
        for bullet in self.bullets:
            bullets_data.append({
                "x": bullet.x,
                "y": bullet.y,
                "angle": bullet.angle,
                "lifespan": bullet.lifespan,
                "owner": bullet.owner
            })

        coins_data = []
        for coin in self.coins:
            coins_data.append({
                "x": coin.x,
                "y": coin.y
            })

        # Формируем полезную нагрузку (payload)
        state = {
            "ships": ships_data,
            "bullets": bullets_data,
            "coins": coins_data,
            "score": self.score
        }

        try:
            response = requests.post(SERVER_URL + "/update_state", json=state)
            response.raise_for_status()
            self.last_state_update_time = time.time()
        except requests.RequestException as e:
            print(f"Error with sending to the server: {e}")

    def get_agent_actions(self, game_state, walls):
            start_time = time.time()

            """
            Sends the game state to the agent server and gets the agent's actions.
            """
            try:
                # Convert walls to a list of dictionaries
                wall_dicts = [{"x": wall.x, "y": wall.y, "width": wall.width, "height": wall.height} for wall in walls]
                payload = {"ships": game_state["ships"], "walls": wall_dicts} # Use the ship state dictionaries directly
                response = requests.post(f"{SERVER_URL}/decide/", json=payload)
                response.raise_for_status()  # Raise an exception for bad status codes
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error communicating with agent server: {e}")
                return {"rotate": 0, "thrust": 0, "shoot": False}  # Default actions in case of error
   
    # Shoot a bullet from the specified ship.
    # The bullet is spawned slightly in front of the ship, and its speed is set.
    # The bullet is added to the list of bullets in the game.       
    def shoot(self, ship_index):
        ship = self.ships[ship_index]
        # Spawn bullet slightly in front of the ship
        rad = math.radians(ship.angle)
        bullet_x = ship.x + math.cos(rad) * 15  # Offset by 15 units in the direction of the ship
        bullet_y = ship.y + math.sin(rad) * 15
        bullet = Bullet(bullet_x, bullet_y, ship.angle, owner=ship_index, speed=15)  # Fast bullets
        self.bullets.append(bullet)

    # Draw the bullets on the screen.
    def draw_bullets(self, screen, camera_x, camera_y):
        for bullet in self.bullets:
            screen_x, screen_y = world_to_screen(bullet.x, bullet.y, camera_x, camera_y)
            pygame.draw.circle(screen, (0, 0, 0), (screen_x, screen_y), 3)

    def draw_coins(self, screen, camera_x, camera_y):
        for coin in self.coins:
            coin.draw(screen, camera_x, camera_y)
    
    # Rotate the ship by a specified number of degrees.
    def rotate_ship(self, index, degrees):
        self.ships[index].rotate(degrees)
    
    # Apply thrust to the ship in the direction of its angle.
    def thrust_ship(self, index, amount):
        self.ships[index].thrust(amount)

    # Get the current state of the game.
    # This includes the state of the ships, score, and time.
    # The state is returned as a dictionary. (This is useful for saving or sending the state of the game)

    def get_game_state(self):
        return {
            "ships": [ship.get_state() for ship in self.ships],
            "score": self.score,
            "time": self.time
        }
        
    def _collides(self, bullet, ship):
        dist = math.hypot(bullet.x - ship.x, bullet.y - ship.y)
        return dist < 15  # Simple collision radius


# ------------------------
# Main Game Loop with Pygame
# ------------------------

# Set world size larger than screen
WORLD_WIDTH, WORLD_HEIGHT = 2000, 2000
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600

WHITE = (255, 255, 255)
BLUE = (50, 100, 255)
RED = (255, 50, 50)

background_image = pygame.image.load("galaxie.jpg")  # Load background image
# background_image = pygame.transform.scale(background_image, (WORLD_WIDTH, WORLD_HEIGHT))

# Create a semi-transparent surface
transparent_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
transparent_surface.blit(background_image, (0, 0))  # Draw the background onto the surface
transparent_surface.set_alpha(128)  # Set transparency to 50% (128 out of 255)

# Create a semi-transparent surface for the info box
info_box = pygame.Surface((150, 60), pygame.SRCALPHA)
info_box.fill((128, 128, 128, 128))  # Semi-transparent gray

def world_to_screen(x, y, camera_x, camera_y):
    return int(x - camera_x + SCREEN_WIDTH // 2), int(y - camera_y + SCREEN_HEIGHT // 2)


def draw_ship(screen, ship, color, camera_x, camera_y):
    screen_x, screen_y = world_to_screen(ship.x, ship.y, camera_x, camera_y)
    angle = ship.angle
    length = 20
    rad = math.radians(angle)
    end_x = screen_x + math.cos(rad) * length
    end_y = screen_y + math.sin(rad) * length
    pygame.draw.circle(screen, color, (screen_x, screen_y), 10)
    pygame.draw.line(screen, color, (screen_x, screen_y), (int(end_x), int(end_y)), 2)


def create_labyrinth():
    # A larger labyrinth with multiple paths and dead ends
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
    # try:
    #     response = requests.get(SERVER_URL + "/walls")
    #     response.raise_for_status()
    #     data = response.json()
    #     walls_coords = data.get("walls", [])
    #     walls = [pygame.Rect(wall["x"], wall["y"], wall["width"], wall["height"]) for wall in walls_coords]
    #     return walls
    # except Exception as e:
    #     print(f"Ошибка при получении данных со стены: {e}")
    #     return []
    return walls

def generate_valid_position(walls, world_width, world_height):
    """Generates a random position that is not inside any wall."""
    while True:
        x = random.randint(20, world_width - 20)
        y = random.randint(20, world_height - 20)
        rect = pygame.Rect(x - 10, y - 10, 20, 20)  # Approximate ship size
        is_valid = True
        for wall in walls:
            if rect.colliderect(wall):
                is_valid = False
                break
        if is_valid:
            return x, y

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x - 6, self.y - 8, 12, 16)  # Coin size

    def draw(self, screen, camera_x, camera_y):
        coin_screen_x = self.rect.x - camera_x + SCREEN_WIDTH // 2
        coin_screen_y = self.rect.y - camera_y + SCREEN_HEIGHT // 2
        # pygame.draw.rect(screen, (255, 215, 0), (coin_screen_x, coin_screen_y, self.rect.width, self.rect.height))
        pygame.draw.ellipse(screen, (255, 215, 0), (coin_screen_x, coin_screen_y, self.rect.width, self.rect.height))
        pygame.draw.arc(screen, (230, 200, 0), (coin_screen_x+1, coin_screen_y, self.rect.width, self.rect.height), 120/180*3.14, 240/180*3.14, 2)
        pygame.draw.arc(screen, (255, 230, 0), (coin_screen_x-1, coin_screen_y, self.rect.width, self.rect.height), 300/180*3.14, 60/180*3.14, 2)

    def collides_with(self, ship_rect):
        return self.rect.colliderect(ship_rect)

# ... (vorheriger Code)

def generate_coins(num_coins, walls):
    coins = []
    for _ in range(num_coins):
        while True:
            x = random.randint(20, WORLD_WIDTH - 20)
            y = random.randint(20, WORLD_HEIGHT - 20)
            coin = Coin(x, y)
            is_valid = True
            for wall in walls:
                if coin.rect.colliderect(wall):
                    is_valid = False
                    break
            if is_valid:
                coins.append(coin)
                break
    return coins

def show_start_menu(screen):
    font = pygame.font.SysFont(None, 48)
    text_player = font.render("Play as Player (Press P)", True, (0, 0, 0))
    text_agent = font.render("Watch Agent (Press A)", True, (0, 0, 0))
    text_quit = font.render("Quit (Press Q)", True, (0, 0, 0))
    text_player_rect = text_player.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
    text_agent_rect = text_agent.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    text_quit_rect = text_quit.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))

    running_menu = True
    
    while running_menu:
        screen.fill(WHITE)
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

def move_enemy_randomly(enemy):
    if random.random() < 0.02:  # Small chance to change direction
        enemy.rotate(random.randint(-10, 10))
    if random.random() < 0.05:  # Small chance to thrust
        enemy.thrust(0.5)

def avoid_walls(ship, walls):
    ship_rect = pygame.Rect(ship.x - 10, ship.y - 10, 20, 20)
    for wall in walls:
        if ship_rect.inflate(30, 30).colliderect(wall): # Check a bit ahead
            # Simple avoidance: rotate away from the center of the wall
            wall_center_x = wall.x + wall.width // 2
            wall_center_y = wall.y + wall.height // 2
            angle_to_wall = math.degrees(math.atan2(wall_center_y - ship.y, wall_center_x - ship.x))
            angle_difference = (angle_to_wall - ship.angle + 360) % 360
            if angle_difference > 180:
                ship.rotate(3) # Rotate right
            else:
                ship.rotate(-3) # Rotate left
            break # Only react to the first wall encountered in close proximity

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
                return False  # Wall blocks the view
    return True

def chase_player(enemy, player):
    """
    Makes the enemy rotate and thrust towards the player.
    """
    dx = player.x - enemy.x
    dy = player.y - enemy.y
    angle_to_target = math.degrees(math.atan2(dy, dx))
    angle_difference = (angle_to_target - enemy.angle + 360) % 360
    if angle_difference > 180:
        angle_difference -= 360

    enemy.rotate(angle_difference * 0.1)
    enemy.thrust(0.3)


def chase_and_shoot(enemy, player, walls, engine):
    if can_see_player(enemy, player, walls):
        # Chase the player
        chase_player(enemy, player)

        # Shoot at the player
        if random.random() < 0.02:  # 2% chance per frame
            engine.shoot(engine.ships.index(enemy))  # Enemy shoots
    else:
        # If the player is not visible, move randomly
        move_enemy_randomly(enemy)
        avoid_walls(enemy, walls)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("BotFighters Arena")

    walls = create_labyrinth()
    #coins = generate_coins(20, walls)
    game_over = False  # Game Over Zustand

    while game_over:
        # Game Over Bildschirm anzeigen
        font = pygame.font.SysFont(None, 48)
        game_over_text = font.render("Game Over! Press R to Restart or Q to Quit", True, (255, 0, 0))
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(game_over_text, text_rect)
        pygame.display.flip()

        # Eingaben für Neustart oder Beenden
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                game_over = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Neustart
                    engine = GameEngine(walls)  # Spiel zurücksetzen
                    game_over = False
                elif event.key == pygame.K_q:  # Beenden
                    running = False
                    game_over = False
        clock.tick(60)  # Begrenze die FPS auf 60

    clock = pygame.time.Clock()
    mode = show_start_menu(screen) # Get game mode from the menu
    engine = GameEngine(walls)

    running = True
    while running:
        screen.fill(WHITE)
        player = engine.ships[0]
        enemy = engine.ships[1] if len(engine.ships) > 1 else None

        # Set the camera to follow the player's ship (blue ship)
        camera_x = player.x
        camera_y = player.y

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if game_over:
            while game_over:
                # Game Over screen
                font = pygame.font.SysFont(None, 48)
                game_over_text = font.render("Game Over! Press R to Restart or Q to Quit", True, (255, 0, 0))
                text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                screen.blit(game_over_text, text_rect)
                pygame.display.flip()

                # Handle events for restart or quit
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        game_over = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:  # Restart
                            engine = GameEngine(walls)  # Reset the game
                            game_over = False
                        elif event.key == pygame.K_q:  # Quit
                            running = False
                            game_over = False
        
        # Draw the semi-transparent background relative to the camera
        screen.blit(transparent_surface, (-camera_x + SCREEN_WIDTH // 2, -camera_y + SCREEN_HEIGHT // 2))

        # Draw walls (relative to camera)
        for wall in walls:
            wall_screen = pygame.Rect(
                wall.x - camera_x + SCREEN_WIDTH // 2,
                wall.y - camera_y + SCREEN_HEIGHT // 2,
                wall.width,
                wall.height
            )
            pygame.draw.rect(screen, (80, 80, 80), wall_screen)

        engine.draw_coins(screen, camera_x, camera_y)  # Draw coins

        # Check if the player collects a coin
        player_rect = pygame.Rect(player.x - 10, player.y - 10, 20, 20)
        for coin in engine.coins[:]:
            if coin.collides_with(player_rect):
                engine.coins.remove(coin)
                engine.score[0] += 1

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
            dummy_agent = DummyAgent(ship_index=0)  # Create an instance of DummyAgent
            actions = dummy_agent.decide(engine.get_game_state(), walls)  # Directly use the game state -> makes it much faster!!!
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
        
        # Überprüfen, ob der Spieler HP <= 0 hat
        if player.hp <= 0:
            game_over = True

        # Draw ships relative to camera
        for i, ship in enumerate(engine.ships):
            color = BLUE if i == 0 else RED
            draw_ship(screen, ship, color, camera_x, camera_y)

            # If the ship is an enemy (not the player), draw its HP beside it
            if i != 0:
                enemy_screen_x, enemy_screen_y = world_to_screen(ship.x, ship.y, camera_x, camera_y)
                font = pygame.font.SysFont(None, 24)
                hp_text = font.render(f"{ship.hp}", True, (255, 0, 0))
                screen.blit(hp_text, (enemy_screen_x + 15, enemy_screen_y - 15))

        # Draw the laser for the dummy agent (when in agent mode for player 1)
        if mode == "agent":
            my_ship = engine.ships[0]
            rad = math.radians(my_ship.angle)
            laser_end_x = my_ship.x + math.cos(rad) * 1000
            laser_end_y = my_ship.y + math.sin(rad) * 1000

            # Check for wall collisions
            for wall in walls:
                wall_rect = {
                    "x": wall.x,
                    "y": wall.y,
                    "width": wall.width,
                    "height": wall.height
                }
                if DummyAgent._line_intersects_rect(my_ship.x, my_ship.y, laser_end_x, laser_end_y, wall_rect):
                    # Shorten the laser to the intersection point
                    laser_end_x, laser_end_y = DummyAgent._get_intersection_point(
                        my_ship.x, my_ship.y, laser_end_x, laser_end_y, wall
                    )
                    break

            # Draw the laser
            pygame.draw.line(screen, (255, 0, 0), world_to_screen(my_ship.x, my_ship.y, camera_x, camera_y),
                             world_to_screen(laser_end_x, laser_end_y, camera_x, camera_y), 2)

        # Display HP and Score
        font = pygame.font.SysFont(None, 24)
        p1_hp = engine.ships[0].hp
        hp_text = font.render(f"Player HP: {p1_hp}", True, (0, 0, 0))
        score_text = font.render(f"Score: {engine.score[0]}", True, (0, 0, 0))

        # Draw the semi-transparent rectangle behind the text
        screen.blit(info_box, (10, 10))

        # Draw the text on top of the rectangle
        screen.blit(hp_text, (20, 20))
        screen.blit(score_text, (20, 40))

        engine.draw_bullets(screen, camera_x, camera_y)

        pygame.display.flip()
        clock.tick(60)  # Begrenze die FPS auf 60

    pygame.quit()

if __name__ == "__main__":
    main()
