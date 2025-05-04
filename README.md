# Botfighter
Liza and Meret's Version of the Scientific Python for Engineering Project

## Included documents:

* **`Instruction + Demo Launch.md`**:
    * Instruction how to install and launch a demo version

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
