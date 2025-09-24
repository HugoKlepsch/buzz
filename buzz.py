#!/usr/bin/env python3

'''
Buzz server
Server code assumes that there is a single thread.
'''
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import random
import string
from urllib.parse import parse_qs


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


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # TODO landing page
            return self.send_html(200, "Hello World!")
        elif self.path.startswith('/a/s/'):
            # This is the game status api - like /a/s/BASEMENT
            # extract game ID from path
            game_id = self.path.split('/')[3]
            if game_id in GAMES:
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
            else:
                return self.send_json(404, json.dumps({'msg': 'Game not found'}))
        elif self.path.startswith('/g/'):
            # This is a game page - like /g/BASEMENT
            # TODO
            return self.send_html(200, "Game page")

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
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)  # type: ignore

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