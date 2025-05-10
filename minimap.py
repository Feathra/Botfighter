import pygame
import requests
import time
import sys
import random

# Window settings
SCALED_WIDTH, SCALED_HEIGHT = 500, 500
MAP_WIDTH, MAP_HEIGHT = 2000, 2000  # original map size

SCALE_X = SCALED_WIDTH / MAP_WIDTH
SCALE_Y = SCALED_HEIGHT / MAP_HEIGHT
SCALE = min(SCALE_X, SCALE_Y)  # for uniform scaling

FPS = 30

# Colors
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLUE = (50, 150, 255)
RED = (255, 50, 50)
YELLOW = (255, 255, 50)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)  # Purple color for player

# Try all possible server URLs
SERVER_URLS = [
    "http://localhost:8080",  # Primary server port from server_2.py
    "http://localhost:8000",  # Default port from engine_2.py
    "http://localhost:8888",
    "http://localhost:9000"
]

# Current server URL - will be set after successful connection
CURRENT_SERVER = None

def find_active_server():
    """Try to find an active server from the list of possible URLs"""
    global CURRENT_SERVER
    
    print("Searching for active server...")
    for url in SERVER_URLS:
        try:
            print(f"Trying {url}...")
            response = requests.get(f"{url}/status", timeout=0.5)
            if response.status_code == 200:
                CURRENT_SERVER = url
                print(f"Connected to server at {CURRENT_SERVER}")
                return True
        except Exception as e:
            print(f"Failed to connect to {url}: {e}")
    
    print("No active server found")
    return False

def fetch_walls():
    """Fetch walls data from server"""
    if not CURRENT_SERVER:
        if not find_active_server():
            return []
    
    try:
        response = requests.get(f"{CURRENT_SERVER}/walls", timeout=0.5)
        response.raise_for_status()
        data = response.json()
        return data["walls"]
    except Exception as e:
        print(f"Error fetching walls: {e}")
        return []

def fetch_game_state():
    """Fetch current game state from server"""
    if not CURRENT_SERVER:
        if not find_active_server():
            return {"ships": [], "bullets": [], "coins": [], "score": [0, 0]}
    
    try:
        response = requests.get(f"{CURRENT_SERVER}/game_state", timeout=0.5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching game state: {e}")
        return {"ships": [], "bullets": [], "coins": [], "score": [0, 0]}

def scale_point(x, y):
    return x * SCALE, y * SCALE

def scale_rect(rect):
    x, y = scale_point(rect["x"], rect["y"])
    width = rect["width"] * SCALE
    height = rect["height"] * SCALE
    return pygame.Rect(x, y, width, height)

def draw_walls(surface, walls):
    for wall in walls:
        rect = scale_rect(wall)
        pygame.draw.rect(surface, GRAY, rect)

def draw_ships(surface, ships):
    for i, ship in enumerate(ships):
        pos = pygame.math.Vector2(*scale_point(ship["x"], ship["y"]))
        angle = ship["angle"]
        # Scale dimensions as well
        points = [
            pos + pygame.math.Vector2(20 * SCALE, 0).rotate_rad(angle),
            pos + pygame.math.Vector2(-10 * SCALE, 10 * SCALE).rotate_rad(angle),
            pos + pygame.math.Vector2(-10 * SCALE, -10 * SCALE).rotate_rad(angle),
        ]
        # Use purple for the player (first ship), blue for others
        color = PURPLE if i == 0 else BLUE
        pygame.draw.polygon(surface, color, points)

def draw_bullets(surface, bullets):
    for bullet in bullets:
        x, y = scale_point(bullet["x"], bullet["y"])
        pygame.draw.circle(surface, RED, (int(x), int(y)), max(1, int(4 * SCALE)))

def draw_coins(surface, coins):
    for coin in coins:
        x, y = scale_point(coin["x"], coin["y"])
        pygame.draw.circle(surface, YELLOW, (int(x), int(y)), max(2, int(8 * SCALE)))

def draw_score(surface, score):
    font = pygame.font.SysFont(None, 24)
    # Player score in purple
    player_text = font.render(f"Player: {score[0]}", True, PURPLE)
    surface.blit(player_text, (10, 10))
    
    # Enemy score in blue
    enemy_text = font.render(f"Enemy: {score[1]}", True, BLUE)
    surface.blit(enemy_text, (10, 40))

def draw_debug_info(surface, walls_count, ships_count, bullets_count, coins_count):
    """Draw debug information about what's being displayed"""
    font = pygame.font.SysFont(None, 20)
    server_text = font.render(f"Server: {CURRENT_SERVER}", True, BLACK)
    counts_text = font.render(f"Walls: {walls_count} | Ships: {ships_count} | Bullets: {bullets_count} | Coins: {coins_count}", True, BLACK)
    
    surface.blit(server_text, (10, SCALED_HEIGHT - 40))
    surface.blit(counts_text, (10, SCALED_HEIGHT - 20))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCALED_WIDTH, SCALED_HEIGHT))
    pygame.display.set_caption("Game Map")
    clock = pygame.time.Clock()

    # Initial connection to server
    find_active_server()

    walls = []
    game_state = {"ships": [], "bullets": [], "coins": [], "score": [0, 0]}
    
    # Counters for connection retries
    retry_count = 0
    max_retries = 5
    
    # Update interval management
    running = True
    last_update_time = 0
    update_interval = 0.2  # Update every 200ms
    last_server_check = 0
    server_check_interval = 5.0  # Check server every 5 seconds

    while running:
        current_time = time.time()
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Refresh on 'R' key
                    find_active_server()
                    last_update_time = 0  # Force immediate update

        # Check if we need to find a new server
        if CURRENT_SERVER is None or (current_time - last_server_check > server_check_interval):
            find_active_server()
            last_server_check = current_time

        # Update game state from server
        if current_time - last_update_time > update_interval:
            try:
                # First try to get walls if we don't have them
                if not walls:
                    walls = fetch_walls()
                    if walls:
                        print(f"Loaded {len(walls)} walls from server")
                
                # Then get the current game state
                new_state = fetch_game_state()
                
                # Check if we got valid data before updating
                if new_state and "ships" in new_state and len(new_state["ships"]) > 0:
                    game_state = new_state
                    retry_count = 0  # Reset retry counter on success
                else:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print("Too many failed data fetches, trying to find server again...")
                        find_active_server()
                        retry_count = 0
            except Exception as e:
                print(f"Error updating data: {e}")
                retry_count += 1
            
            last_update_time = current_time

        # Clear screen with white background
        screen.fill(WHITE)
        
        # Draw game elements
        draw_walls(screen, walls)
        draw_coins(screen, game_state.get("coins", []))
        draw_ships(screen, game_state.get("ships", []))
        draw_bullets(screen, game_state.get("bullets", []))
        draw_score(screen, game_state.get("score", [0, 0]))
        
        # Draw debug information
        draw_debug_info(
            screen, 
            len(walls), 
            len(game_state.get("ships", [])),
            len(game_state.get("bullets", [])), 
            len(game_state.get("coins", []))
        )

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
