import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room
import random
import string

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

rooms = {}

def generate_room_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def is_valid_code(code):
    return (
        code.isdigit()
        and len(code) == 4
        and all(d in "123456789" for d in code)
        and len(set(code)) == 4
    )

def calculate_bulls_cows(secret, guess):
    bulls = 0
    cows = 0
    for i in range(4):
        if guess[i] == secret[i]:
            bulls += 1
        elif guess[i] in secret:
            cows += 1
    return bulls, cows

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("create_room")
def create_room(data):
    room_id = generate_room_id()

    rooms[room_id] = {
        "players": {
            data["sid"]: {
                "name": data["name"],
                "secret": None
            }
        },
        "current_turn": None,
        "guesses": {}
    }

    join_room(room_id)

    emit("room_created", {"room_id": room_id})
    emit("room_update", {
        "players": [data["name"]]
    }, room=room_id)


@socketio.on("join_room")
def join_room_event(data):
    room_id = data["room_id"]

    if room_id not in rooms:
        emit("room_error", {"message": "Room does not exist"})
        return

    if len(rooms[room_id]["players"]) >= 2:
        emit("room_error", {"message": "Room is full"})
        return

    rooms[room_id]["players"][data["sid"]] = {
        "name": data["name"],
        "secret": None
    }

    join_room(room_id)

    emit("room_update", {
        "players": [p["name"] for p in rooms[room_id]["players"].values()]
    }, room=room_id)


@socketio.on("submit_secret")
def submit_secret(data):
    room_id = data["room_id"]
    sid = data["sid"]
    secret = data["secret"]

    if not is_valid_code(secret):
        emit("secret_error", {"message": "Invalid secret"})
        return

    rooms[room_id]["players"][sid]["secret"] = secret
    emit("secret_saved", room=sid)

    # Start game when both secrets submitted
    if all(p["secret"] for p in rooms[room_id]["players"].values()):
        for psid in rooms[room_id]["players"]:
            rooms[room_id]["guesses"][psid] = []

        current_turn = random.choice(list(rooms[room_id]["players"].keys()))
        rooms[room_id]["current_turn"] = current_turn

        emit("start_game", {
            "current_player": rooms[room_id]["players"][current_turn]["name"]
        }, room=room_id)

        for psid in rooms[room_id]["players"]:
            if psid == current_turn:
                emit("your_turn", room=psid)
            else:
                emit("wait_turn", room=psid)


@socketio.on("submit_guess")
def submit_guess(data):
    room_id = data["room_id"]
    sid = data["sid"]
    guess = data["guess"]

    if room_id not in rooms:
        return

    game = rooms[room_id]

    if game["current_turn"] != sid:
        emit("invalid_turn", {"message": "Not your turn"}, room=sid)
        return

    if not is_valid_code(guess):
        emit("invalid_turn", {"message": "Invalid guess"}, room=sid)
        return

    opponent_sid = [p for p in game["players"] if p != sid][0]
    opponent_secret = game["players"][opponent_sid]["secret"]

    bulls, cows = calculate_bulls_cows(opponent_secret, guess)
    
    if bulls == 4:
        winner_sid = game["current_turn"]
        winner_name = game["players"][winner_sid]["name"]

        for psid in game["players"]:
            emit("game_over", {
                "winner": winner_name,
                "your_secret": game["players"][psid]["secret"],
                "opponent_secret": game["players"][
                    opponent_sid if psid == winner_sid else winner_sid
                ]["secret"]
            }, room=psid)

        del rooms[room_id]
        return

    game["guesses"][sid].append({
        "guess": guess,
        "bulls": bulls,
        "cows": cows
    })

    emit("guess_result", {
        "player_sid": sid,
        "guess": guess,
        "bulls": bulls,
        "cows": cows
    }, room=room_id)

    game["current_turn"] = opponent_sid
    emit("your_turn", room=opponent_sid)
    emit("wait_turn", room=sid)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), allow_unsafe_werkzeug=True)