from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict
from dummy_agent import DummyAgent

import traceback

walls_data = [
    {"x": 50, "y": 50, "width": 1900, "height": 20},     # Верхняя стена
    {"x": 50, "y": 50, "width": 20, "height": 1900},     # Левая стена
    {"x": 50, "y": 1930, "width": 1900, "height": 20},   # Нижняя стена
    {"x": 1930, "y": 50, "width": 20, "height": 1900},   # Правая стена

    {"x": 200, "y": 200, "width": 20, "height": 400},    # Вертикальная стена в левом верхнем углу
    {"x": 200, "y": 600, "width": 400, "height": 20},    # Горизонтальная стена в левом верхнем углу
    {"x": 600, "y": 200, "width": 20, "height": 400},    # Вертикальная стена в центре сверху
    {"x": 600, "y": 600, "width": 400, "height": 20},    # Горизонтальная стена в центре сверху
    {"x": 1000, "y": 200, "width": 20, "height": 800},   # Вертикальная стена справа сверху
    {"x": 200, "y": 1000, "width": 800, "height": 20},   # Горизонтальная стена в центре
    {"x": 1200, "y": 200, "width": 20, "height": 800},   # Вертикальная стена справа в центре
    {"x": 1200, "y": 1000, "width": 400, "height": 20},  # Горизонтальная стена справа в центре
    {"x": 1600, "y": 200, "width": 20, "height": 800},   # Вертикальная стена справа вверху
    {"x": 200, "y": 1400, "width": 400, "height": 20},   # Горизонтальная стена внизу слева
    {"x": 600, "y": 1400, "width": 20, "height": 400},   # Вертикальная стена внизу в центре
    {"x": 600, "y": 1800, "width": 400, "height": 20},   # Горизонтальная стена внизу в центре
    {"x": 1000, "y": 1400, "width": 20, "height": 400},  # Вертикальная стена внизу справа
    {"x": 1200, "y": 1400, "width": 400, "height": 20},  # Горизонтальная стена внизу справа
    {"x": 1600, "y": 1400, "width": 20, "height": 400},  # Вертикальная стена внизу справа далеко

    # Тупики
    {"x": 300, "y": 300, "width": 100, "height": 20},
    {"x": 1500, "y": 1500, "width": 100, "height": 20},
    {"x": 800, "y": 800, "width": 20, "height": 100},
]

# Initialize FastAPI app
app = FastAPI()

# Game state model
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

# Initialize DummyAgent with ship_index 0
agent = DummyAgent(ship_index=0)

game_state = {
    "ships": [],
    "bullets": [],
    "coins": [],
    "score": []
}

@app.get("/walls")
async def walls():
    # Return an example game state with ships and walls
    return {
        "walls": walls_data
    }
@app.post("/decide/")
async def decide(game_state: GameState):
    # Get actions from DummyAgent
    actions = agent.decide(game_state.dict(), game_state.walls)
    return actions

@app.post("/update_state")
async def update_state(state: GameState):
    global game_state
    game_state = state

@app.get("/game_state")
async def get_game_state():
    # Return an example game state with ships and walls
    return game_state

@app.get("/minimap", response_class=HTMLResponse)
async def minimap(request: Request):
    # Читаем файл server_demo.html из папки static и возвращаем его содержимое
    html_path = "server_demo.html"
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
