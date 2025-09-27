#!/usr/bin/env python3

'''
Buzz server
Server code assumes that there is a single thread.
'''
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import random
import string
from urllib.parse import parse_qs, urlencode


def gen_key():
    """
    Generate a new game ID or session key. 8 character string all caps.
    :return: The new key
    :rtype: str
    """
    return ''.join(random.choices(string.ascii_uppercase, k=8))


# Stores game data
GAMES = {
    'BASEMENT': {
        'q': 1,
        'ps': {
            gen_key(): {
                'username': f'creator',
                'is_creator': True,
            },
            gen_key(): {
                'username': f'user1',
                'is_creator': False,
            },
            gen_key(): {
                'username': f'user2',
                'is_creator': False,
            },
            gen_key(): {
                'username': f'user3',
                'is_creator': False,
            },
        },
        'b_ord': []
    }
}


def template_landing_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Buzz Lobby</title>
        <style>
            body {
                Font-family: sans-serif;
            }
            input, button {
                margin: 0.25em auto
            }
            .section {
                border-color: grey;
                border-radius: 3px;
                border-style: solid;
                border-width: medium;
                display: inline-block;
                margin: 1em auto;
                padding: 0 1em 1em;
            }
        </style>
    </head>
    <body>
        <h1>Buzz Lobby</h1>
        <form class="section" action="/join" method="POST">
            <h2>Join Game</h2>
            <label for="username">Username:</label>
            <input id="username" type="text" name="username" placeholder="Username" required pattern="[^\\s].{1,30}" autofocus />
            <br>
            <label for="game_id">Game ID:</label>
            <input id="game_id" type="text" name="game_id" placeholder="Game ID" required pattern="[a-zA-Z]{8}"/>
            <br>
            <input type="submit" value="Join Game" />
        </form>
        <br>
        <form class="section" action="/create" method="POST">
            <h2>Create Game</h2>
            <label for="username_create">Username:</label>
            <input id="username_create" type="text" name="username" placeholder="Username" required pattern="[^\\s].{1,30}" autofocus />
            <br>
            <input type="submit" value="Create Game" />
        </form>
    </body>
    """


def template_game_page(status, player_key):
    is_creator = status['ps'][player_key]['is_creator'] if player_key in status['ps'] else False
    create_button_html = '<button onclick="clearBuzzes()">Clear Buzzes</button>' if is_creator else ""
    minus_q_button_html = '<button onclick="changeQuestion(-1)">-</button>' if is_creator else ""
    plus_q_button_html = '<button onclick="changeQuestion(1)">+</button>' if is_creator else ""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Buzz Game</title>
        <style>
            body {{
                Font-family: sans-serif;
                max-width: 600px;
            }}
            input, button {{
                margin: 0.25em auto;
                padding: 1em;
                font-size: 1.2em;
            }}
            .section {{
                border-color: grey;
                border-radius: 3px;
                border-style: solid;
                border-width: medium;
                display: inline-block;
                margin: 1em auto;
                padding: 0 1em 1em;
            }}
        </style>
    </head>
    <body>
        <h1>Buzz Game</h1>
        <div class="section">
            <h3>Question number</h3>
            <div>
                {minus_q_button_html}
                <span id="questionNumber">1</span>
                {plus_q_button_html}
            </div>
        </div>
        <br>
        <button onclick="buzz()">Buzz</button>
        {create_button_html}
        <br>
        <div class="section">
            <h3>Players</h3>
            <div id="playersList" class="loading">Loading players...</div>
        </div>

        <div class="section">
            <h3>Buzz Order</h3>
            <div id="buzzOrder" class="loading">No buzzes yet...</div>
        </div>
        <script>
            // Get Game ID from URL
            let gameID = null;
            const path = window.location.pathname;
            const segments = path.split('/');
            if (segments.length >= 3 && segments[1] === 'g') {{
              gameID = segments[2];
            }}
            
            // Get player key from cookie if available
            // If not available, post form to /join to get player key
            let playerKey = null;
            const cookies = document.cookie.split(';');
            for (const cookie of cookies) {{
                if (cookie.includes('k=')) {{
                    playerKey = cookie.split('=')[1];
                    break;
                }}
            }}
            if (!playerKey) {{
                let username = prompt('Enter your username');
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = '/join';
                form.style.display = 'none';
                let userIn = document.createElement('input');
                userIn.type = 'hidden';
                userIn.name = 'username';
                userIn.value = username;
                form.appendChild(userIn);
                let gameIDIn = document.createElement('input');
                gameIDIn.type = 'hidden';
                gameIDIn.name = 'game_id';
                gameIDIn.value = gameID;
                form.appendChild(gameIDIn);
                document.body.appendChild(form);
                form.submit();
            }}
            
            function changeQuestion(delta) {{
                var q = document.getElementById("questionNumber");
                q.innerHTML = String(Number(q.innerHTML) + delta);
                fetch('/a/q/' + gameID, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        k: playerKey,
                        q: Number(q.innerHTML)
                    }})
                }});
                updateStatus();
            }}
            function buzz() {{
                fetch('/a/b/' + gameID, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        k: playerKey
                    }})
                }});
                updateStatus();
            }}
            function clearBuzzes() {{
                fetch('/a/c/' + gameID, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        k: playerKey
                    }})
                }});
                updateStatus();
            }}
            var status = null;
            function updateStatus() {{
                fetch('/a/s/' + gameID)
                    .then(response => response.json())
                    .then(data => updateDisplay(data));
            }}
            function updateDisplay(data) {{
                document.getElementById("questionNumber").innerHTML = data.q;
                
                var playerList = "";
                var buzzOrder = "";
                
                data.p.sort((a, b) => a.b_o - b.b_o);
                
                data.p.forEach(function(player) {{
                    var playerName = player.u;
                    if (player.c) playerName += " (Host)";
                    if (player.b_o >= 0) {{
                        playerList += `<div style="background-color: lightblue">`;
                    }} else {{
                        playerList += `<div>`;
                    }}
                    playerList += playerName;
                    playerList += "</div>";
                    
                    if (player.b_o >= 0) {{
                        buzzOrder += (player.b_o + 1) + ". " + player.u + "<br>";
                    }}
                }});
                
                document.getElementById("playersList").innerHTML = playerList;
                document.getElementById("buzzOrder").innerHTML = buzzOrder || "No buzzes yet...";
            }}
            updateStatus();
            setInterval(updateStatus, 1000);
        </script>
    </body>
    """


class BuzzAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            return self.send_html(200, template_landing_page())
        elif self.path.startswith('/a/s/'):
            # This is the game status api - like /a/s/BASEMENT
            # extract game ID from path
            game_id = self.path.split('/')[3]
            if game_id not in GAMES:
                return self.send_json(404, json.dumps({'msg': 'Game not found'}))
            status = GAMES[game_id]
            send_status = {
                'q': status['q'],
                'p': [
                    {
                        'u': v['username'],
                        'c': v['is_creator'],
                        'b_o': status['b_ord'].index(k) if k in status['b_ord'] else -1,
                    }
                    for k, v in status['ps'].items()
                ]
            }
            return self.send_json(200, json.dumps(send_status))
        elif self.path.startswith('/g/'):
            # This is a game page - like /g/BASEMENT
            # TODO game page
            game_id = self.path.split('/')[2]
            if game_id not in GAMES:
                self.send_response(302)
                self.send_header('Location', f'/?{urlencode({"msg": "Game not found"})}')
                self.end_headers()
                return
            status = GAMES[game_id]
            # Get player key from cookie
            player_key = None
            cookies = self.headers.get('Cookie', '').split(';')
            for cookie in cookies:
                if cookie.startswith('k='):
                    player_key = cookie.split('=')[1]
                    break
            return self.send_html(200, template_game_page(status, player_key))

        else:
            return self.send_html(404, "Not found")

    def do_POST(self):
        global GAMES
        if self.path.startswith('/create'):
            # This is the game creation api - like /create

            # Parse form data to get username
            content_length = int(self.headers['Content-Length'])
            form_data = self.rfile.read(content_length).decode('utf-8')
            form_data = parse_qs(form_data)
            try:
                username = form_data.get('username', [None])[0]
            except IndexError:
                username = None
            if not username or not username.strip():
                return self.send_html(400, "Missing username")
            username = username.strip()

            game_id = gen_key()
            GAMES[game_id] = {
                'q': 1,
                'ps': {},
                'b_ord': [],
            }
            player_key = gen_key()
            player = {
                'username': username,
                'is_creator': True,
            }
            GAMES[game_id]['ps'][player_key] = player

            # Send redirect response with cookie
            self.send_response(302)
            self.send_header('Location', f'/g/{game_id}')
            self.send_header('Set-Cookie', f'k={player_key}; Path=/')
            self.end_headers()
            return
        elif self.path.startswith('/join'):
            # This is the game join api - like /join

            # Parse form data to get username and game ID
            content_length = int(self.headers['Content-Length'])
            form_data = self.rfile.read(content_length).decode('utf-8')
            form_data = parse_qs(form_data)
            try:
                username = form_data.get('username', [None])[0]
            except IndexError:
                username = None
            if not username or not username.strip():
                return self.send_html(400, "Missing username")
            username = username.strip()
            try:
                game_id = form_data.get('game_id', [None])[0]
            except IndexError:
                game_id = None
            if not game_id or game_id not in GAMES:
                return self.send_html(400, "Missing game ID")
            if any(player['username'] == username for player in GAMES[game_id]['ps'].values()):
                self.send_response(302)
                self.send_header('Location', f'/?{urlencode({"msg": "Username already taken"})}')
                self.end_headers()
                return

            player_key = gen_key()
            player = {
                'username': username,
                'is_creator': False,
            }
            GAMES[game_id]['ps'][player_key] = player

            # Send redirect response with cookie
            self.send_response(302)
            self.send_header('Location', f'/g/{game_id}')
            self.send_header('Set-Cookie', f'k={player_key}; Path=/')
            self.end_headers()
            return
        elif self.path.startswith('/a/b/'):
            # This is the buzz api - like /a/b/BASEMENT
            # extract game ID from path
            game_id = self.path.split('/')[3]
            if game_id not in GAMES:
                return self.send_json(404, json.dumps({'msg': 'Game not found'}))
            status = GAMES[game_id]
            # extract session key from payload
            payload = self.json_payload()
            if not payload or 'k' not in payload:
                return self.send_json(400, json.dumps({'msg': 'Invalid JSON payload'}))
            session_key = payload['k']
            if session_key not in status['ps']:
                return self.send_json(400, json.dumps({'msg': 'Invalid session key'}))
            if session_key not in status['b_ord']:
                status['b_ord'].append(session_key)
            GAMES[game_id] = status
            return self.send_json(200, json.dumps({'msg': 'Buzzed'}))
        elif self.path.startswith('/a/c/'):
            # This is the buzz clear api - like /a/c/BASEMENT
            # extract game ID from path
            game_id = self.path.split('/')[3]
            if game_id not in GAMES:
                return self.send_json(404, json.dumps({'msg': 'Game not found'}))
            status = GAMES[game_id]
            # extract session key from payload
            payload = self.json_payload()
            if not payload or 'k' not in payload:
                return self.send_json(400, json.dumps({'msg': 'Invalid JSON payload'}))
            session_key = payload['k']
            if session_key not in status['ps']:
                return self.send_json(400, json.dumps({'msg': 'Invalid session key'}))
            if not status['ps'][session_key]['is_creator']:
                return self.send_json(401, json.dumps({'msg': 'Not authorized'}))
            status['b_ord'] = []
            GAMES[game_id] = status
            return self.send_json(200, json.dumps({'msg': 'Buzzes cleared'}))
        elif self.path.startswith('/a/q/'):
            # This is the set q_num api - like /a/q/BASEMENT
            # extract game ID from path
            game_id = self.path.split('/')[3]
            if game_id not in GAMES:
                return self.send_json(404, json.dumps({'msg': 'Game not found'}))
            status = GAMES[game_id]
            # extract session key from payload
            payload = self.json_payload()
            if not payload or 'k' not in payload:
                return self.send_json(400, json.dumps({'msg': 'Invalid JSON payload'}))
            session_key = payload['k']
            if session_key not in status['ps']:
                return self.send_json(400, json.dumps({'msg': 'Invalid session key'}))
            if not status['ps'][session_key]['is_creator']:
                return self.send_json(401, json.dumps({'msg': 'Not authorized'}))
            if 'q' not in payload:
                return self.send_json(400, json.dumps({'msg': 'Invalid JSON payload'}))
            status['q'] = payload['q']
            GAMES[game_id] = status
            return self.send_json(200, json.dumps({'msg': 'Question number set to {q_num}'.format(q_num=status['q'])}))
        else:
            return self.send_html(404, "Not found")

    def log_message(self, format, *args):
        # Override to customize logging or suppress it
        print(f"[{self.log_date_time_string()}] {format % args}")

    def json_payload(self):
        try:
            return json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        except json.JSONDecodeError:
            return None

    def send_html(self, status: int, data: str):
        self.send_response(status)

        # Send headers
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Send message body
        self.wfile.write(data.encode('utf-8'))

    def send_json(self, status: int, data: str):
        self.send_response(status)

        # Send headers
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        # Send message body
        self.wfile.write(data.encode('utf-8'))

def run_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, BuzzAPI)  # type: ignore

    print(f"Starting server on port {port}...")
    print(f"Visit http://localhost:{port}/ to see 'Hello World'")
    print("Press Ctrl+C to stop the server")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server...")
        httpd.shutdown()
        httpd.server_close()

if __name__ == '__main__':
    run_server(8080)