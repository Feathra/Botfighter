At the beginning, our first goal was to build a working basic game from which we could make modifications, build the dummy_agend, etc.
The first week we both worked on this. We decided to use Meret's version of the 2D world with the basic physics, a maze and enemies, coins and bullets.
At that point it was only possible to control the game by yourself .

Then we talk about improvements we want to do and exercises we need to do and who will do them:

* FastAPI server: Liza  - Creating the file that exposes various endpoints to real-time interact with the game state (with FastAPI and Pydantic). It also integrates a Dummy_Agent.
* Dummy_Agend: Meret - The red laser was introduced to simulate the dummy agent's vision. If an enemy crosses it, it is detected and shot down. 
* MiniMap: Liza  - This file's code creates a 2D game map visualizer using the Pygame library. The map depends on a server running on localhost:8000 that exposes the necessary endpoints /walls and /game_state. Also, minimap could be assesed through the HTML-based minimap interface /minimap.
* Improve enemies, bullets, engine: Meret - Enemies should not be able to see and shoot through walls, Growing number of enemies, world visualizer, game over, menu with game mode selection, score board
* Collision of enemy: Liza - Ships' detection of each other to avoid collision and not to overlap while running.
