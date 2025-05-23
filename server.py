from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import traceback
import math
import socket
import sys
from fastapi.middleware.cors import CORSMiddleware
from dummy_agent import DummyAgent

# Wall data with translated comments
walls_data = [
    {"x": 50, "y": 50, "width": 1900, "height": 20},     # Top wall
    {"x": 50, "y": 50, "width": 20, "height": 1900},     # Left wall
    {"x": 50, "y": 1930, "width": 1900, "height": 20},   # Bottom wall
    {"x": 1930, "y": 50, "width": 20, "height": 1900},   # Right wall

    {"x": 200, "y": 200, "width": 20, "height": 400},    # Vertical wall in top left corner
    {"x": 200, "y": 600, "width": 400, "height": 20},    # Horizontal wall in top left corner
    {"x": 600, "y": 200, "width": 20, "height": 400},    # Vertical wall in top center
    {"x": 600, "y": 600, "width": 400, "height": 20},    # Horizontal wall in top center
    {"x": 1000, "y": 200, "width": 20, "height": 800},   # Vertical wall in top right
    {"x": 200, "y": 1000, "width": 800, "height": 20},   # Horizontal wall in center
    {"x": 1200, "y": 200, "width": 20, "height": 800},   # Vertical wall in center right
    {"x": 1200, "y": 1000, "width": 400, "height": 20},  # Horizontal wall in center right
    {"x": 1600, "y": 200, "width": 20, "height": 800},   # Vertical wall in top far right
    {"x": 200, "y": 1400, "width": 400, "height": 20},   # Horizontal wall in bottom left
    {"x": 600, "y": 1400, "width": 20, "height": 400},   # Vertical wall in bottom center
    {"x": 600, "y": 1800, "width": 400, "height": 20},   # Horizontal wall in bottom center
    {"x": 1000, "y": 1400, "width": 20, "height": 400},  # Vertical wall in bottom right
    {"x": 1200, "y": 1400, "width": 400, "height": 20},  # Horizontal wall in bottom right
    {"x": 1600, "y": 1400, "width": 20, "height": 400},  # Vertical wall in bottom far right

    # Dead ends
    {"x": 300, "y": 300, "width": 100, "height": 20},
    {"x": 1500, "y": 1500, "width": 100, "height": 20},
    {"x": 800, "y": 800, "width": 20, "height": 100},
]

# Initialize FastAPI app
app = FastAPI(title="BotFighter API", 
              description="Game server for BotFighter with sensor-based agent API",
              version="2.0")

# Add CORS middleware for better performance with browser clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return HTMLResponse("<h1>Welcome to BotFighter!</h1><p>Visit <a href='/docs'>/docs</a> for API documentation.</p>")

# Game state models
class Ship(BaseModel):
    x: float
    y: float
    angle: float

class Wall(BaseModel):
    x: float
    y: float
    width: float
    height: float

class Bullet(BaseModel):
    x: float
    y: float
    angle: float
    lifespan: int
    owner: int

class Coin(BaseModel):
    x: float
    y: float

class GameState(BaseModel):
    ships: List[Ship]
    bullets: List[Bullet]
    coins: List[Coin]
    score: List[int]

# Sensor data models
class SensorRequest(BaseModel):
    ship_id: int
    position: dict
    angle: float

class RadarResult(BaseModel):
    type: str  # "enemy" or "coin"
    distance: float
    angle: float  # Relative to ship's angle

class SensorResponse(BaseModel):
    laser_hit: bool
    laser_distance: Optional[float] = None
    radar_objects: List[RadarResult] = []

# Global game state (in-memory cache)
game_state = {
    "ships": [],
    "bullets": [],
    "coins": [],
    "score": []
}

# Initialize DummyAgent with ship_index 0 (create once, reuse)
agent = DummyAgent(ship_index=0)

# Cache walls data to avoid redundant processing
@app.get("/walls", response_model=Dict)
async def walls():
    return {"walls": walls_data}

@app.post("/decide/")
async def decide(game_data: dict):
    """Makes decisions based only on sensor data"""
    try:
        ship_id = game_data.get("ship_id", 0)  # Default to first ship
            
        # Create sensor request from game data
        sensor_request = SensorRequest(
            ship_id=ship_id,
            position={"x": game_data["ships"][ship_id]["x"], "y": game_data["ships"][ship_id]["y"]},
            angle=game_data["ships"][ship_id]["angle"]
        )
        
        # Get sensor data
        sensor_data = await sense(sensor_request)
        
        # Let agent decide based on sensor data only
        actions = agent.decide_from_sensors(sensor_data)
        return actions
    except Exception as e:
        print(f"Error in decide endpoint: {e}")
        traceback.print_exc()
        return {"rotate": 0, "thrust": 0, "shoot": False}

@app.post("/update_state")
async def update_state(state: GameState):
    global game_state
    game_state = state.dict()
    print(f"Server received state with {len(state.coins)} coins")
    return {"status": "success"}

@app.get("/game_state")
async def get_game_state():
    return game_state

@app.get("/minimap", response_class=HTMLResponse)
async def minimap(request: Request):
    # Read the server_demo.html file and return its contents
    try:
        html_path = "server_demo.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        print(f"Error serving minimap: {e}")
        return HTMLResponse(content=f"<h1>Error: {str(e)}</h1>", status_code=500)

@app.post("/sense")
async def sense(request: SensorRequest):
    """Combined sensor endpoint that returns both laser and radar data"""
    try:
        # Extract ship position data
        ship_id = request.ship_id
        ship_x = request.position["x"]
        ship_y = request.position["y"] 
        ship_angle = request.angle
        
        # Log request details
        print(f"Sense request from ship {ship_id} at ({ship_x:.1f}, {ship_y:.1f}), angle {ship_angle:.1f}")
        
        # 1. Laser sensor - check for walls directly ahead
        laser_hit, laser_distance = check_laser(ship_x, ship_y, ship_angle, walls_data)
        
        # 2. Radar sensor - find nearby enemies and coins
        radar_objects = []
        radar_range = 800  # Radar range in game units
        
        # Process ships (enemies)
        ships = game_state.get("ships", [])
        for i, other_ship in enumerate(ships):
            if i == ship_id:  # Skip self
                continue
                
            # Calculate distance first for early optimization
            dx = other_ship["x"] - ship_x
            dy = other_ship["y"] - ship_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Skip if beyond radar range
            if distance > radar_range:
                continue
            
            # Check if enemy is visible (not behind walls)
            if is_visible(ship_x, ship_y, other_ship["x"], other_ship["y"], walls_data):
                absolute_angle = math.degrees(math.atan2(dy, dx))
                relative_angle = (absolute_angle - ship_angle + 360) % 360
                if relative_angle > 180:
                    relative_angle -= 360
                
                radar_objects.append({
                    "type": "enemy",
                    "distance": distance,
                    "angle": relative_angle
                })
        
        # Process coins
        coins = game_state.get("coins", [])
        print(f"Processing {len(coins)} coins from game state")
        
        detected_coins = 0
        for coin in coins:
            try:
                # Convert to dict if needed
                if not isinstance(coin, dict):
                    if hasattr(coin, "dict"):
                        coin = coin.dict()
                    else:
                        print(f"Skipping coin with invalid format: {type(coin)}")
                        continue
                
                # Calculate distance
                dx = coin["x"] - ship_x
                dy = coin["y"] - ship_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Skip if beyond radar range
                if distance > radar_range:
                    continue
                
                # Debug line for distance
                print(f"Checking coin at ({coin['x']:.1f}, {coin['y']:.1f}), distance: {distance:.1f}")
                    
                # Check if coin is visible (not behind walls)
                if is_visible(ship_x, ship_y, coin["x"], coin["y"], walls_data):
                    absolute_angle = math.degrees(math.atan2(dy, dx))
                    relative_angle = (absolute_angle - ship_angle + 360) % 360
                    if relative_angle > 180:
                        relative_angle -= 360
                    
                    radar_objects.append({
                        "type": "coin",
                        "distance": distance,
                        "angle": relative_angle
                    })
                    detected_coins += 1
            except Exception as e:
                print(f"Error processing coin: {e}")
                print(f"Coin data: {coin}")
        
        print(f"Detected {detected_coins} coins with radar")
        
        # Log radar results
        if radar_objects:
            print(f"Radar found {len(radar_objects)} objects: {[(obj['type'], int(obj['distance']), int(obj['angle'])) for obj in radar_objects]}")
        
        return {
            "laser_hit": laser_hit, 
            "laser_distance": laser_distance,
            "radar_objects": radar_objects
        }
    except Exception as e:
        print(f"Error in sense endpoint: {e}")
        traceback.print_exc()
        return {"laser_hit": False, "radar_objects": []}

# Helper functions for sensors
def check_laser(x, y, angle, walls):
    """Check if there's a wall directly ahead using the laser sensor"""
    max_distance = 50  # Maximum distance to check
    rad = math.radians(angle)
    end_x = x + math.cos(rad) * max_distance
    end_y = y + math.sin(rad) * max_distance
    
    closest_hit = None
    min_distance = max_distance
    
    for wall in walls:
        intersection = line_intersects_rect(x, y, end_x, end_y, wall)
        if intersection:
            hit_x, hit_y = intersection
            distance = math.sqrt((hit_x - x)**2 + (hit_y - y)**2)
            if distance < min_distance:
                min_distance = distance
                closest_hit = intersection
    
    return bool(closest_hit), min_distance if closest_hit else None

def is_visible(from_x, from_y, to_x, to_y, walls):
    """Check if there's a clear line of sight between two points"""
    # Quick distance check first
    distance = math.sqrt((to_x - from_x)**2 + (to_y - from_y)**2)
    
    # For very close objects, always visible
    if distance < 30:
        return True
        
    # For distant objects, check more thoroughly
    for wall in walls:
        # Skip walls that are far from the line of sight
        wall_center_x = wall["x"] + wall["width"] / 2
        wall_center_y = wall["y"] + wall["height"] / 2
        
        # Simple bounding box check first for efficiency
        min_x = min(from_x, to_x) - 20
        max_x = max(from_x, to_x) + 20
        min_y = min(from_y, to_y) - 20
        max_y = max(from_y, to_y) + 20
        
        if (wall_center_x < min_x or wall_center_x > max_x) and (wall_center_y < min_y or wall_center_y > max_y):
            continue
            
        if line_intersects_rect(from_x, from_y, to_x, to_y, wall):
            return False
    return True

def line_intersects_rect(x1, y1, x2, y2, rect):
    """Check if a line intersects with a rectangle"""
    # Rectangle corners
    left = rect["x"]
    top = rect["y"]
    right = left + rect["width"]
    bottom = top + rect["height"]
    
    # Check each edge of the rectangle
    edges = [
        (left, top, right, top),      # Top
        (right, top, right, bottom),  # Right
        (right, bottom, left, bottom),  # Bottom
        (left, bottom, left, top)     # Left
    ]
    
    for x3, y3, x4, y4 in edges:
        # Check if the line segments intersect
        if line_intersects_line(x1, y1, x2, y2, x3, y3, x4, y4):
            # Calculate intersection point
            return get_intersection_point(x1, y1, x2, y2, x3, y3, x4, y4)
    
    return None

def line_intersects_line(x1, y1, x2, y2, x3, y3, x4, y4):
    """Check if two line segments intersect"""
    # Calculate denominators
    den = ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))
    if den == 0:
        return False  # Lines are parallel
    
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / den
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / den
    
    # If ua and ub are both between 0 and 1, lines intersect
    return 0 <= ua <= 1 and 0 <= ub <= 1

def get_intersection_point(x1, y1, x2, y2, x3, y3, x4, y4):
    """Calculate the intersection point of two lines"""
    den = ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))
    if den == 0:
        return None  # Lines are parallel
    
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / den
    
    # Calculate intersection point
    x = x1 + ua * (x2 - x1)
    y = y1 + ua * (y2 - y1)
    
    return (x, y)

@app.get("/status")
async def status():
    """Simple endpoint to check if server is running"""
    return {"status": "running"}

if __name__ == "__main__":
    # Define ports to try
    ports = [8080, 8000, 8888, 9000]
    
    # Try to bind to any available port
    for port in ports:
        try:
            print(f"Attempting to start server on port {port}...")
            uvicorn.run(app, host="localhost", port=port, log_level="warning")
            break  # If successful, exit the loop
        except socket.error as e:
            print(f"Could not bind to port {port}: {e}")
            if port == ports[-1]:
                print("All ports failed. Try specifying an available port manually.")
                sys.exit(1)
            print(f"Trying next port...")