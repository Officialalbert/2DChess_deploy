const API = "/api";
const CELL = 20;
const GRID = 21; // 0..20

let userId = null;
let currentGameId = null;
let pollTimer = null;

const loginScreen = document.getElementById("login-screen");
const mapScreen = document.getElementById("map-screen");
const arenaScreen = document.getElementById("arena-screen");
const canvas = document.getElementById("map-canvas");
const ctx = canvas.getContext("2d");

document.getElementById("login-btn").onclick = async () => {
  const username = document.getElementById("username-input").value.trim();
  if (!username) return;

  const res = await fetch(`${API}/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username }),
  });
  if (!res.ok) {
    alert("Не удалось войти (возможно, имя занято)");
    return;
  }
  const user = await res.json();
  userId = user.id;

  loginScreen.classList.add("hidden");
  mapScreen.classList.remove("hidden");
  startMapLoop();
};

document.addEventListener("keydown", async (e) => {
  if (mapScreen.classList.contains("hidden")) return;
  const map = { ArrowUp: [0, -1], ArrowDown: [0, 1], ArrowLeft: [-1, 0], ArrowRight: [1, 0],
                w: [0, -1], s: [0, 1], a: [-1, 0], d: [1, 0] };
  const delta = map[e.key];
  if (!delta) return;

  await fetch(`${API}/map/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, dx: delta[0], dy: delta[1] }),
  });
});

function startMapLoop() {
  drawMap();
  pollTimer = setInterval(drawMap, 500);
}

async function drawMap() {
  const res = await fetch(`${API}/map/players`);
  const data = await res.json();

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#2a2a3d";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // арена
  ctx.font = "18px sans-serif";
  ctx.fillText("🏰", data.arena.x * CELL, data.arena.y * CELL + 16);

  let me = null;
  for (const [uid, pos] of Object.entries(data.players)) {
    ctx.fillStyle = Number(uid) === userId ? "#00d4ff" : "#ff6b6b";
    ctx.beginPath();
    ctx.arc(pos.x * CELL + CELL / 2, pos.y * CELL + CELL / 2, 6, 0, Math.PI * 2);
    ctx.fill();
    if (Number(uid) === userId) me = pos;
  }

  // если игрок дошёл до арены — предлагаем начать партию
  if (me && me.x === data.arena.x && me.y === data.arena.y && !currentGameId) {
    clearInterval(pollTimer);
    await startGame();
  }
}

async function startGame() {
  const opponent = prompt("Имя второго игрока (хотсит на одном экране):", "Player2");
  const res = await fetch(`${API}/games`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ white_name: "Player1", black_name: opponent || "Player2" }),
  });
  const game = await res.json();
  currentGameId = game.id;

  mapScreen.classList.add("hidden");
  arenaScreen.classList.remove("hidden");
  renderBoard(game.fen);
}

document.getElementById("move-btn").onclick = async () => {
  const san = document.getElementById("move-input").value.trim();
  if (!san || !currentGameId) return;

  const res = await fetch(`${API}/games/${currentGameId}/moves`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ san }),
  });

  if (!res.ok) {
    const err = await res.json();
    document.getElementById("game-status").textContent = "Ошибка: " + err.detail;
    return;
  }

  const game = await res.json();
  document.getElementById("move-input").value = "";
  renderBoard(game.fen);

  if (game.status === "finished") {
    document.getElementById("game-status").textContent = `Партия окончена: ${game.result}. Ждём анализ Stockfish...`;
    pollAnalysis();
  }
};

async function pollAnalysis() {
  const timer = setInterval(async () => {
    const res = await fetch(`${API}/games/${currentGameId}/analysis`);
    const rows = await res.json();
    if (rows.length > 0) {
      clearInterval(timer);
      const div = document.getElementById("analysis");
      div.innerHTML = rows
        .map((r) => `Ход ${r.move_number}: оценка ${r.eval_cp ?? "?"} cp, лучший ход: ${r.best_move ?? "-"}`)
        .join("<br/>");
    }
  }, 1500);
}

document.getElementById("leave-arena-btn").onclick = () => {
  arenaScreen.classList.add("hidden");
  mapScreen.classList.remove("hidden");
  currentGameId = null;
  document.getElementById("game-status").textContent = "";
  document.getElementById("analysis").innerHTML = "";
  startMapLoop();
};

const PIECE_UNICODE = {
  K: "♔", Q: "♕", R: "♖", B: "♗", N: "♘", P: "♙",
  k: "♚", q: "♛", r: "♜", b: "♝", n: "♞", p: "♟",
};

function renderBoard(fen) {
  const board = document.getElementById("board");
  board.innerHTML = "";
  const rows = fen.split(" ")[0].split("/");

  for (let r = 0; r < 8; r++) {
    let col = 0;
    for (const ch of rows[r]) {
      if (/\d/.test(ch)) {
        for (let i = 0; i < Number(ch); i++) {
          board.appendChild(makeSquare(r, col, ""));
          col++;
        }
      } else {
        board.appendChild(makeSquare(r, col, PIECE_UNICODE[ch] || ""));
        col++;
      }
    }
  }
}

function makeSquare(r, c, content) {
  const sq = document.createElement("div");
  sq.className = "square " + ((r + c) % 2 === 0 ? "light" : "dark");
  sq.textContent = content;
  return sq;
}
