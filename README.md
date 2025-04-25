# BattleShip

---

## Table of Contents
- [Description](#description)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Server Launch](#server-launch)
- [License](#license)

---

## Description

BattleShip is a client-server implementation of the classic Battleship game. The client application allows users to interact with the game through multiple interfaces (terminal-based, file-based, and socket-based) and supports features such as ship placement, turn-based shooting, session management, and error handling. The project is designed to be modular, making use of distinct components for configuration, networking, game logic, user interface, and user management.

---

## Features

- **Multi-Interface Support:**  
  The client supports different modes of interaction including terminal (CLI), file-based, and socket-based admin interfaces.

- **Modular Architecture:**  
  The application is divided into clear modules such as configuration, enums, user interface, game logic, networking, and utilities.

- **Interactive Gameplay:**  
  Players can place ships on a grid, shoot at opponents, and receive immediate visual feedback with a dynamic board display.

- **Session Management:**  
  The client handles session connections, reconnections, and error conditions, ensuring smooth gameplay.

- **Robust Communication:**  
  Uses a custom packet protocol for client-server communication that ensures clear and consistent data transmission.
- **Support for custom server plugins:** 
The server part of the project allows you to expand functionality through custom plugins, which allows developers and users to add new functions, change the logic of data processing or integrate third-party services without modifying the basic server code.

---

## Installation

1. **Clone the Repository:**  
```bash
git clone <repository_url>

cd battleship

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

```

## Usage

To start the BattleShip client, run `python main.py`:
Once started, follow the on-screen prompts to:

Create or update your user information.

Choose a game server.

Place your ships on the board.

And finally, enjoy the game :)

## Server Launch
Navigate to the Server Directory: Ensure you are in the server directory.

Activate the Virtual Environment (if not already activated).

Start the Server: Typically, run `python server.py`:

This will start the server and listen for incoming connections on the configured host and port (see settings in settings.py).

Make sure the server is running before launching the client to ensure successful connections.

## License
This project is licensed under the MIT License. See the LICENSE file for details.