import pygame
import requests
import time

# Настройки окна
SCALED_WIDTH, SCALED_HEIGHT = 500, 500
MAP_WIDTH, MAP_HEIGHT = 2000, 2000  # исходный размер карты

SCALE_X = SCALED_WIDTH / MAP_WIDTH
SCALE_Y = SCALED_HEIGHT / MAP_HEIGHT
SCALE = min(SCALE_X, SCALE_Y)  # для равномерного масштабирования

FPS = 30

# Цвета
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLUE = (50, 150, 255)
RED = (255, 50, 50)
YELLOW = (255, 255, 50)
BLACK = (0, 0, 0)

# URL API
WALLS_URL = "http://localhost:8000/walls"
GAME_STATE_URL = "http://localhost:8000/game_state"

def fetch_walls():
    response = requests.get(WALLS_URL)
    response.raise_for_status()
    data = response.json()
    return data["walls"]

def fetch_game_state():
    response = requests.get(GAME_STATE_URL)
    response.raise_for_status()
    data = response.json()
    return data

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
    for ship in ships:
        pos = pygame.math.Vector2(*scale_point(ship["x"], ship["y"]))
        angle = ship["angle"]
        # размеры тоже масштабируем
        points = [
            pos + pygame.math.Vector2(20 * SCALE, 0).rotate_rad(angle),
            pos + pygame.math.Vector2(-10 * SCALE, 10 * SCALE).rotate_rad(angle),
            pos + pygame.math.Vector2(-10 * SCALE, -10 * SCALE).rotate_rad(angle),
        ]
        pygame.draw.polygon(surface, BLUE, points)

def draw_bullets(surface, bullets):
    for bullet in bullets:
        x, y = scale_point(bullet["x"], bullet["y"])
        pygame.draw.circle(surface, RED, (int(x), int(y)), max(1, int(4 * SCALE)))

def draw_coins(surface, coins):
    for coin in coins:
        x, y = scale_point(coin["x"], coin["y"])
        pygame.draw.circle(surface, YELLOW, (int(x), int(y)), max(2, int(8 * SCALE)))

def draw_score(surface, score):
    font = pygame.font.SysFont(None, max(24, int(36 * SCALE)))
    text = font.render(f"Score: Player {score[0]} - Enemy {score[1]}", True, BLACK)
    surface.blit(text, (10, 10))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCALED_WIDTH, SCALED_HEIGHT))
    pygame.display.set_caption("Game map (scaled, auto update)")
    clock = pygame.time.Clock()

    walls = []
    game_state = {"ships": [], "bullets": [], "coins": [], "score": [0, 0]}

    running = True
    last_update_time = 0
    update_interval = 0.2

    while running:
        now = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if now - last_update_time > update_interval:
            try:
                walls = fetch_walls()
                game_state = fetch_game_state()
            except Exception as e:
                print("Error obtaining the data:", e)
            last_update_time = now

        screen.fill(WHITE)
        draw_walls(screen, walls)
        draw_coins(screen, game_state.get("coins", []))
        draw_ships(screen, game_state.get("ships", []))
        draw_bullets(screen, game_state.get("bullets", []))
        draw_score(screen, game_state.get("score", [0, 0]))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
