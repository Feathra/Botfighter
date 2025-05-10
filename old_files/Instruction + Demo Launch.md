
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
uvicorn server:app --reload
```


If you are using an agent or game state server, ensure it's running at http://localhost:8000.

<br>


-	Run the game (in the 2nd terminal, if the server is started):

```bash
python3 engine.py
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
python3 minimap.py
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

- Player 1: Player (Humain).
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

The other is to observe the integrated dummy_agendt. It is equipped with a random movement control. If an enemy comes into its field of vision (the red laser beam), it tracks it and shoots at it.

The basic mechanics are:

- A ship (self-controllable, or as a dummy_agenda), it can shoot and always moves in the direction in which the nose points  
- A shooting mechanic that allows you to kill enemies  
- The minimap on which the ship, enemies, walls and coins can be observed  
- Enemies that shoot at you when they see you in a direct line and otherwise move randomly. When an enemy dies, two new ones follow  
- Coins that earn you points when you collect them  


<br><br>

# <div align="center"> Appendix: File Descriptions</div>

* **`engine.py`**:
    * This file contains the core game logic using Pygame.
    * It defines the `SpaceObject` (ships), `Bullet`, and `GameEngine` classes.
    * Handles ship movement, physics, collisions, bullet mechanics, and the main game loop.
    * Implements the labyrinth, coin generation, and drawing routines.
    * Provides functionality to run the game in either player or agent-controlled mode.

* **`dummy_agent.py`**:
    * This file defines a basic agent (`DummyAgent`) that controls a ship.
    * The agent can rotate, thrust, and shoot.
    * It includes simple logic for enemy detection (using a laser), wall avoidance, and basic combat.
    * This agent serves as an example and can be replaced with more sophisticated AI.

* **`server.py`**:
    * This file sets up a FastAPI server.
    * It defines API endpoints for:
        * `/game_state`:  Returns the current state of the game (ship positions, wall locations).  *(Note:  Currently returns a static example.)*
        * `/decide/`:  Receives the game state and sends it to the `DummyAgent` to get the agent's actions.
    * This server acts as a communication layer between the game engine and external agents.
 
* **`minimap.py`**:
    * simple visualization of the game world as a minimap
    * interacts with the game state data, received from the game server, to display the positions of entities (ships, objects) within the game environment

* **`server_demo.html`**:
    * provides a basic web interface for interacting with or observing the game server (`server_UPD.py`). Establish a connection with the server (potentially via WebSockets) and display real-time information or allow for simple commands.
    * To use this interface, open the `server_demo.html` file in a web browser. Ensure that the `server_UPD.py` script is running and accessible from your browser's network. The JavaScript within the HTML file will handle the connection and data exchange with the server. Consult the JavaScript code within the file for details on the communication protocol and available features.

<br><br>





