const socket = io({transports:["websocket", "polling"]});

let playerName = "";
let roomId = "";

function setName() {
    playerName = document.getElementById("nameInput").value.trim();
    if (!playerName) return alert("Enter name");

    document.getElementById("nameSection").style.display = "none";
    document.getElementById("roomSection").style.display = "block";
}

function createRoom() {
    socket.emit("create_room", { name: playerName, sid: socket.id });
}

function joinRoom() {
    roomId = document.getElementById("roomInput").value.trim();
    if (!roomId) return alert("Enter Room ID");

    socket.emit("join_room", { room_id: roomId, name: playerName, sid: socket.id });
}

function submitSecret() {
    const secret = document.getElementById("secretInput").value.trim();
    if (secret.length !== 4) return alert("Secret must be 4 digits");

    socket.emit("submit_secret", { room_id: roomId, sid: socket.id, secret });
}

function submitGuess() {
    const guess = document.getElementById("guessInput").value.trim();
    if (!guess) return;

    socket.emit("submit_guess", { room_id: roomId, sid: socket.id, guess });
    document.getElementById("guessInput").value = "";
}

socket.on("room_created", data => {
    roomId = data.room_id;
    document.getElementById("roomSection").style.display = "none";
    document.getElementById("lobby").style.display = "block";
    document.getElementById("roomId").innerText = roomId;
});

socket.on("room_update", data => {
    document.getElementById("roomSection").style.display = "none";
    document.getElementById("lobby").style.display = "block";
    document.getElementById("roomId").innerText = roomId;

    const list = document.getElementById("players");
    list.innerHTML = "";

    data.players.forEach(p => {
        const li = document.createElement("li");
        li.innerText = p;
        list.appendChild(li);
    });

    if (data.players.length < 2) {
        document.getElementById("waitingLoader").style.display = "block";
    } else {
        document.getElementById("waitingLoader").style.display = "none";
        document.getElementById("secretSection").style.display = "block";
    }
});

socket.on("secret_saved", () => {
    document.getElementById("secretInput").disabled = true;
});

socket.on("start_game", data => {
    document.getElementById("secretSection").style.display = "none";
    document.getElementById("gameSection").style.display = "block";
    document.getElementById("turnStatus").innerText =
        `Current Turn: ${data.current_player}`;
});

socket.on("your_turn", () => {
    const turn = document.getElementById("turnStatus");
    turn.innerText = "Your Turn";
    turn.classList.add("turn-glow");

    document.getElementById("guessInput").disabled = false;
    document.getElementById("guessBtn").disabled = false;
});

socket.on("wait_turn", () => {
    const turn = document.getElementById("turnStatus");
    turn.innerText = "Opponent's Turn";
    turn.classList.remove("turn-glow");

    document.getElementById("guessInput").disabled = true;
    document.getElementById("guessBtn").disabled = true;
});

socket.on("guess_result", data => {
    const tableId = data.player_sid === socket.id
        ? "myGuessTable"
        : "opponentGuessTable";

    const row = document.createElement("tr");
    row.classList.add("new-guess-row");

    row.innerHTML = `
        <td>${data.guess}</td>
        <td>${data.bulls}</td>
        <td>${data.cows}</td>
    `;

    document.getElementById(tableId).appendChild(row);
});

socket.on("game_over", data => {
    document.getElementById("gameSection").style.display = "none";
    document.getElementById("gameOverSection").style.display = "block";

    document.getElementById("winnerText").innerText = `🏆 Winner: ${data.winner}`;
    document.getElementById("yourSecretText").innerText = data.your_secret;
    document.getElementById("opponentSecretText").innerText = data.opponent_secret;
});

function exitGame() {
    location.reload();
}
