<br>

<div align="center">Git-Link to the repositorie: https://github.com/Feathra/Botfighter.git</div> 

<br><br>



# <div align="center">“BOTFIGHTERS: Space Duel Arena”</div> 



<div align="center"> Real-time 2D space labyrinth shooter where you pilot a spaceship through waves of enemies. The survival comes down to collecting as many coin as possible, while encountering and shooting the enemies. But the enemies will also shoot at you! As you play, the number of enemies increases, and you’ll need to keep adjusting your strategy. The game focuses on keeping you on your toes and forcing you to think quickly. Each run feels different, and you’ll get better the more you play. Play it yourself, or let the Dummy Agent take control. Are you ready to face the battle and see how long you can last?</div>

<br><br>

   
# <div align="center"> Instruction</div>

<div align="center"> This instruction explains how to install, use, and compete the “BOTFIGHTERS: Space Duel Arena”.</div>




<br><br>






## <div align="center"> 1) System Requirements</div>


- Python 3.x+
 
- Python libraries to run the game and the server. These imports require installation via pip:
    * 'pygame' for the game environment.
	 * 'fastapi' for the server-side logic.
	 * 'uvicorn' to serve the FastAPI application.
	 * 'requests' to send HTTP requests.
	 * 'pydantic' for data validation.

To install these, run the following command in the terminal:

```bash
pip install pygame fastapi uvicorn pydantic requests
```

<br>


!! IMPORTANT: The code should be run only as the .py file. Since the game runs an event loop (pygame) and doesn’t return control, the notebook .ipynb file hangs or freezes.

<br>


## <div align="center"> 2) Launch the Game </div>



-	Ensure you have the following files in the same directory or Python path:
    *	engine.py
    *	minimap.py
    *	dummy_agent.py
    *	server.py
    *	server_demo.html
    *	galaxie.jpg
<br>

-	Start the server (optional):

To start the server, run the following command in the terminal:

```bash
python server.py
```


If you are using an agent or game state server, ensure it's running at http://localhost:8000.

<br>


-	Run the game (in the 2nd terminal, if the server is started):

```bash
python engine.py
```


<br>

A Pygame window will open, displaying the game. You are presented with a start menu with the following options:


>Press 'P' to play as player
>
>Press 'A' to watch the dummy agent play
>
>Press 'Q' to quit




<br>




-	Run the map (in the 3rd terminal, if the server and game are started):

```bash
python minimap.py
```

<br>


-	Running the agent (optional, for external agents): if you want to run the Dummy Agent (or your own agent) in a separate process, run the following command (ensure the server is running before starting).

```bash
python agent_process.py
```
 	
This script will continuously communicate with the server to get the game state and send back agent actions.

<br>

## <div align="center"> 3) Game Environment </div>


🛸 Ships: player-controlled and AI-controlled ships that can rotate, thrust, and shoot.

🧱 Walls: static rectangular obstacles that block movement, bullets, and vision.

💥 Bullets: projectiles fired by ships. They cause damage on impact and vanish when colliding or going off-screen.

💰 Coins: collectible items scattered in the arena. Ships can fly over coins to collect them (likely for scoring or rewards).

🌌 Arena: A bounded space where all action unfolds.

<br>



## <div align="center"> 4) Game Control </div>

These apply only if the engine run for a player (human) input; otherwise, agents control the ships.

- Player 1: Player (Human).
- Player 2: Dummy Agent (AI).

If keyboard input is enabled:

- Arrow UP (or W) for thrust.
- Arrow LEFT (or A) / Arrow RIGHT (or D) for rotation.
- Spacebar to shoot.

<br>


<br>

## <div align="center"> 5) Game Objective </div>

For Player to survive and destroy the enemy ship while avoiding enemies' bullets and collecting coins to maximize your score.

- Score of coins: the Player starts with a Score of 0.

- Enemy Health Points: each enemy ship has 100 Health Points, and each bullet fired from your ship reduces their Health Points by 10.

- Enemy respawn: after each enemy is destroyed, new, larger waves of enemies will appear, increasing the challenge.

- Coins collection: collecting coins increases Players score. Each coin adds 1 point to your score.

- Game Over: the game ends when the Player’s Health Points reach 0.

>
>Press 'R' to restart the lost game
>


<br>



## <div align="center"> 6) Game Server API documentation </div>


The FastAPI server provides several endpoints to interact with the game:

- http://localhost:8000 Displays a welcome message.

- http://localhost:8000/walls Returns the layout of walls in the game. Ships: The position, angle, and status of each ship. Bullets: The position and trajectory of projectiles fired by ships. Coins: The location of collectible items. Walls: The location and dimensions of walls in the environment.

- http://localhost:8000/game_state Retrieves the current game state. 

- http://localhost:8000/minimap Displays a minimap of the game environment via an HTML interface.

<br><br>


# <div align="center"> Demo Launch </div>


There are 2 ways to test the mechanics of the game:

On the one hand, it is possible to control the ship yourself. This allows you to test certain mechanics (such as doubling enemies when one dies) directly.

The other is to observe the integrated dummy_agent. It is equipped with a random movement control. It uses sensor data to collect coins, search for enemies or to detect walls.

The basic mechanics are:

- A ship (self-controllable, or as a dummy_agend), it can shoot and always moves in the direction in which the nose points  
- A shooting mechanic that allows you to kill enemies  
- The minimap on which the ship, enemies, walls and coins can be observed  
- Enemies that shoot at you when they see you in a direct line and otherwise move randomly. When an enemy dies, two new ones follow  
- Coins that earn you points when you collect them  


<br><br>

# <div align="center"> Appendix: File Descriptions</div>

* **`engine_2.py`**:
    * Core game engine with improved enemy movement logic
    * Defines the `SpaceObject`, `Bullet`, `Coin`, and `GameEngine` classes
    * Implements state-machine based enemy patrol behavior with three states:
      * Forward motion with consistent thrust
      * Gradual turning with momentum
      * Intelligent wall avoidance
    * Features automatic server connection with fallback options
    * Handles dynamic coin generation and collection mechanics
    * Provides purple coloring for the player ship

* **`dummy_agent_2.py`**:
    * Sophisticated AI agent that uses sensor data to navigate
    * Features enhanced stuck detection and escape mechanisms
    * Implements memory of recent targets for consistent goal-seeking
    * Contains optimized wall avoidance with progressive turning
    * Uses gentle turning for coin collection (reduced turn rates)
    * Provides combat strategies including circling and evasive maneuvers
    * Falls back to random exploration when no targets are detected

* **`server_2.py`**:
    * FastAPI server with English-language wall data comments
    * Implements automatic port selection (8080, 8000, 8888, 9000)
    * Provides sensor simulation endpoints:
      * Laser sensors for wall detection
      * Radar sensors for enemy and coin detection
    * Includes visibility checking through walls
    * Features CORS middleware for browser compatibility
    * Maintains game state synchronization between engine and clients
    * Provides status endpoint for server detection

* **`minimap_2.py`**:
    * Visualization tool showing the entire game arena
    * Dynamically detects and connects to available server
    * Shows player ship in purple, enemy ships in blue
    * Displays walls, bullets, coins, and scores
    * Includes debug information panel with entity counts
    * Provides error handling for network failures
    * Features refresh functionality with the 'R' key

* **`server_demo.html`**:
    * Web interface for observing game state via the server
    * Establishes connection with the active server
    * Displays real-time game information
    * To use: open in a browser while the server is running

<br><br>

# Botfighter
Liza and Meret's Version of the Scientific Python for Engineering Project

## Included documents:

* **`Instruction + Demo Launch.md`**:
    * Instructions on how to install and launch a demo version

* **`engine.py`**:
    * This file contains the core game logic using Pygame.
    * It defines the `SpaceObject` (ships), `Bullet`, `Coin`, and `GameEngine` classes.
    * Handles ship movement, physics, collisions, bullet mechanics, and the main game loop.
    * Implements a sophisticated labyrinth with wall collision detection.
    * Features intelligent enemy movement with state machine-based patrol patterns.
    * Includes coin generation and collection mechanics with score tracking.
    * Supports both player-controlled and agent-controlled gameplay modes.
    * Communicates with the server to synchronize game state.

* **`dummy_agent.py`**:
    * An enhanced AI agent that controls a ship using sensor-based decision making.
    * Features sophisticated stuck detection and escape mechanisms.
    * Implements target memory to track objects even when they're temporarily out of view.
    * Contains intelligent wall avoidance with progressive turning based on proximity.
    * Uses a prioritized decision system (enemies → coins → exploration).
    * Includes combat strategies such as circling and evasive maneuvers.
    * Adapts its behavior based on the situation (gentle turns for coins, aggressive for combat).

* **`server.py`**:
    * A FastAPI server that handles game state synchronization and agent decision making.
    * Defines robust API endpoints for:
        * `/game_state`: Returns the current state of the game (ships, bullets, coins, scores).
        * `/walls`: Provides the labyrinth wall data.
        * `/decide/`: Processes game state and returns agent decisions.
        * `/sense`: Simulates sensors (laser, radar) for realistic agent perception.
        * `/status`: Simple endpoint to check if server is running.
    * Implements port fallback to find an available port automatically.
    * Handles CORS for browser compatibility.
    * Simulates physical sensors like lasers and radar for more realistic AI.

* **`minimap.py`**:
    * Provides a real-time visualization of the entire game world.
    * Automatically detects and connects to the game server.
    * Displays ships (player in purple, enemies in blue), bullets, walls, and coins.
    * Shows score information and debug data.
    * Features automatic server detection across multiple ports.
    * Implements retry logic for connection resilience.
    * Includes a debug display with entity counts and server information.
    * Can be refreshed with the 'R' key.

* **`server_demo.html`**:
    * Provides a basic web interface for interacting with or observing the game server.
    * Establishes a connection with the server and displays real-time information.
    * To use this interface, open the file in a web browser while the server is running.





