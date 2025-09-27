# Buzz

[Public Buzz server](https://buzz.hugoklepsch.com)

A lightweight HTTP server that hosts a simple multiplayer quiz buzzer. 
Players can create or join a game, buzz in, and the host can manage question 
numbers and clear buzz order.

---

# API

- GET `/` – Landing page with forms to create a new game or join an existing one.
- GET `/g/{GAME_ID}` – Game page UI for a specific game.
- GET `/a/s/{GAME_ID}` – Game status (JSON). Returns current question number `q` 
and players `p` with fields: `u` (username), `c` (is_creator), and `b_o` 
(0-based buzz order, or -1 if not buzzed).
- POST `/create` – Create a new game. Form fields: `username`. Sets a session 
cookie `k` and redirects to `/g/{GAME_ID}`.
- POST `/join` – Join an existing game. Form fields: `username`, `game_id`. 
Sets a session cookie `k` and redirects to `/g/{GAME_ID}`.
- POST `/a/b/{GAME_ID}` – Buzz in. JSON body: `{ "k": "SESSION_KEY" }`. Adds 
the player to the buzz order.
- POST `/a/c/{GAME_ID}` – Clear buzz order (host only). JSON body: `{ "k": "SESSION_KEY" }`.
- POST `/a/q/{GAME_ID}` – Set current question number (host only). JSON body: `{ "k": "SESSION_KEY", "q": NUMBER }`.

Notes:
- The session key is provided via cookie `k` by the server after create/join and must be sent in JSON for API calls under `/a/*`.

# Deployment

* Deployed with docker-compose. It can be as simple as `docker-compose up -d`,
or if you want to deploy it as a systemd service, run `./create-systemd-service.sh`.
* see [HugoKlepsch/reverse-proxy-network](http://github.com/HugoKlepsch/reverse-proxy-network) for files to create network.

