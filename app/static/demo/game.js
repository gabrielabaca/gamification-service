const characters = [
  { name: "Ale", src: "/assets/ale_1.png" },
  { name: "Ari", src: "/assets/ari_1.png" },
  { name: "Cony 1", src: "/assets/cony_1.png" },
  { name: "Cony 2", src: "/assets/cony_2.png" },
  { name: "Gaby", src: "/assets/gaby_1.png" },
  { name: "Juan 1", src: "/assets/juan_1.png" },
  { name: "Juan 2", src: "/assets/juan_2.png" },
  { name: "Lucio", src: "/assets/lucio_1.png" },
];

const monsterSprites = [
  "/assets/monsters/monster_1.png",
  "/assets/monsters/monster_2.png",
  "/assets/monsters/monster_3.png",
  "/assets/monsters/monster_4.png",
  "/assets/monsters/monster_5.png",
  "/assets/monsters/monster_6.png",
];

const storageKeys = {
  playerName: "gamificationDemoPlayerName",
  playerIds: "gamificationDemoPlayerIds",
  character: "gamificationDemoCharacter",
};

const gridSize = 42;

const state = {
  userId: "",
  playerName: "",
  selectedCharacter: localStorage.getItem(storageKeys.character) || characters[0].src,
  balance: { points: 0, coins: 0 },
  connected: false,
  playing: false,
  keys: new Set(),
  player: { x: 70, y: 220, width: 64, height: 78, speed: 245 },
  collectible: { x: 260, y: 200, width: 30, height: 30 },
  monsters: [],
  combo: 1,
  collected: 0,
  timeLeft: 60,
  lastFrame: 0,
  comboTimer: null,
  gameTimer: null,
  hitCooldownUntil: 0,
  socket: null,
  reconnectTimer: null,
  heartbeatTimer: null,
  leaderboardTimer: null,
  soundEnabled: false,
};

const elements = {
  connectionStatus: document.getElementById("connectionStatus"),
  playerNameInput: document.getElementById("playerNameInput"),
  generatedUserId: document.getElementById("generatedUserId"),
  newUserButton: document.getElementById("newUserButton"),
  connectButton: document.getElementById("connectButton"),
  characterGrid: document.getElementById("characterGrid"),
  arena: document.getElementById("arena"),
  playerSprite: document.getElementById("playerSprite"),
  collectible: document.getElementById("collectible"),
  floatingLayer: document.getElementById("floatingLayer"),
  timeLeft: document.getElementById("timeLeft"),
  comboValue: document.getElementById("comboValue"),
  collectedValue: document.getElementById("collectedValue"),
  pointsValue: document.getElementById("pointsValue"),
  coinsValue: document.getElementById("coinsValue"),
  convertAmount: document.getElementById("convertAmount"),
  convertButton: document.getElementById("convertButton"),
  convertHint: document.getElementById("convertHint"),
  refreshLeaderboardButton: document.getElementById("refreshLeaderboardButton"),
  leaderboardList: document.getElementById("leaderboardList"),
  startButton: document.getElementById("startButton"),
  soundButton: document.getElementById("soundButton"),
  activityLog: document.getElementById("activityLog"),
  arcadeSound: document.getElementById("arcadeSound"),
};

function init() {
  elements.playerNameInput.value = localStorage.getItem(storageKeys.playerName) || "";
  elements.playerSprite.src = state.selectedCharacter;
  renderCharacters();
  createMonsters();
  moveCollectible();
  bindEvents();
  updateHud();
  updateConnection("Sin conectar");
  requestAnimationFrame(gameLoop);
}

function bindEvents() {
  elements.newUserButton.addEventListener("click", () => {
    elements.playerNameInput.value = "";
    elements.generatedUserId.textContent = "UUID generado al conectar.";
    elements.playerNameInput.focus();
    logActivity("Ingresa un nombre para generar un jugador.");
  });

  elements.connectButton.addEventListener("click", connectPlayer);
  elements.playerNameInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      connectPlayer();
    }
  });
  elements.startButton.addEventListener("click", startGame);
  elements.convertButton.addEventListener("click", convertPoints);
  elements.refreshLeaderboardButton.addEventListener("click", refreshLeaderboard);
  elements.soundButton.addEventListener("click", toggleSound);

  window.addEventListener("keydown", (event) => {
    if (isTextInput(event.target)) return;

    const direction = keyToDirection(event.key);
    if (!direction) return;
    event.preventDefault();
    state.keys.add(direction);
    elements.arena.focus();
  });

  window.addEventListener("keyup", (event) => {
    if (isTextInput(event.target)) return;

    const direction = keyToDirection(event.key);
    if (direction) state.keys.delete(direction);
  });

  document.querySelectorAll("[data-move]").forEach((button) => {
    const direction = button.dataset.move;
    button.addEventListener("pointerdown", () => state.keys.add(direction));
    button.addEventListener("pointerup", () => state.keys.delete(direction));
    button.addEventListener("pointercancel", () => state.keys.delete(direction));
    button.addEventListener("pointerleave", () => state.keys.delete(direction));
  });
}

function renderCharacters() {
  elements.characterGrid.innerHTML = "";
  characters.forEach((character) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "character-option";
    button.title = character.name;
    button.setAttribute("aria-label", `Elegir ${character.name}`);
    button.innerHTML = `<img src="${character.src}" alt="${character.name}" />`;
    if (character.src === state.selectedCharacter) {
      button.classList.add("selected");
    }
    button.addEventListener("click", () => {
      state.selectedCharacter = character.src;
      localStorage.setItem(storageKeys.character, character.src);
      elements.playerSprite.src = character.src;
      renderCharacters();
      logActivity(`Personaje elegido: ${character.name}.`);
    });
    elements.characterGrid.appendChild(button);
  });
}

function createMonsters() {
  state.monsters = monsterSprites.slice(0, 4).map((src, index) => {
    const monster = document.createElement("img");
    monster.className = "monster";
    monster.src = src;
    monster.alt = "";
    elements.arena.appendChild(monster);

    return {
      element: monster,
      x: 190 + index * 116,
      y: 92 + (index % 2) * 170,
      width: 58,
      height: 58,
      vx: index % 2 === 0 ? 110 : -95,
      vy: index % 2 === 0 ? 80 : -105,
    };
  });
}

async function connectPlayer() {
  const playerName = normalizePlayerName(elements.playerNameInput.value);
  if (!playerName) {
    logActivity("Ingresa tu nombre para conectar.");
    updateConnection("Falta nombre", "error");
    return;
  }

  state.playerName = playerName;
  state.userId = getOrCreateUserIdForName(playerName);
  localStorage.setItem(storageKeys.playerName, playerName);
  elements.playerNameInput.value = playerName;
  elements.generatedUserId.textContent = `UUID: ${state.userId}`;
  elements.connectButton.disabled = true;

  try {
    const result = await apiFetch("/api/v1/demo/players/connect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: state.userId, display_name: playerName }),
    });
    updateBalance(result.balance);
    renderLeaderboard(result.leaderboard);
    state.connected = true;
    updateConnection("Conectado", "connected");
    startPresenceUpdates();
    connectWebSocket();
    logActivity(`${playerName} conectado. Ya puedes iniciar la partida.`);
  } catch (error) {
    state.connected = false;
    updateConnection("Error de API", "error");
    logActivity(error.message);
  } finally {
    elements.connectButton.disabled = false;
    updateHud();
  }
}

function startGame() {
  if (!state.connected) {
    logActivity("Conecta un jugador antes de iniciar.");
    return;
  }

  state.playing = true;
  state.timeLeft = 60;
  state.combo = 1;
  state.collected = 0;
  state.player.x = 70;
  state.player.y = Math.max(40, getArenaBounds().height / 2 - state.player.height / 2);
  moveCollectible();
  resetTimer();
  elements.arena.focus();
  logActivity("Partida iniciada. Recolecta cristales para ganar puntos.");
  updateHud();
}

function resetTimer() {
  clearInterval(state.gameTimer);
  state.gameTimer = setInterval(() => {
    if (!state.playing) return;
    state.timeLeft -= 1;
    if (state.timeLeft <= 0) {
      state.timeLeft = 0;
      state.playing = false;
      resetCombo();
      logActivity("Tiempo terminado. Puedes iniciar otra partida.");
    }
    updateHud();
  }, 1000);
}

function gameLoop(timestamp) {
  const delta = Math.min((timestamp - (state.lastFrame || timestamp)) / 1000, 0.05);
  state.lastFrame = timestamp;

  if (state.playing) {
    updatePlayer(delta);
    updateMonsters(delta);
    detectCollectibleCollision();
    detectMonsterCollision();
  }

  renderGameObjects();
  requestAnimationFrame(gameLoop);
}

function updatePlayer(delta) {
  if (performance.now() < state.hitCooldownUntil) return;

  const bounds = getArenaBounds();
  let dx = 0;
  let dy = 0;

  if (state.keys.has("left")) dx -= 1;
  if (state.keys.has("right")) dx += 1;
  if (state.keys.has("up")) dy -= 1;
  if (state.keys.has("down")) dy += 1;

  if (dx !== 0 && dy !== 0) {
    dx *= Math.SQRT1_2;
    dy *= Math.SQRT1_2;
  }

  state.player.x = clamp(state.player.x + dx * state.player.speed * delta, 0, bounds.width - state.player.width);
  state.player.y = clamp(state.player.y + dy * state.player.speed * delta, 0, bounds.height - state.player.height);
}

function updateMonsters(delta) {
  const bounds = getArenaBounds();
  state.monsters.forEach((monster) => {
    monster.x += monster.vx * delta;
    monster.y += monster.vy * delta;

    if (monster.x <= 0 || monster.x >= bounds.width - monster.width) {
      monster.vx *= -1;
      monster.x = clamp(monster.x, 0, bounds.width - monster.width);
    }
    if (monster.y <= 0 || monster.y >= bounds.height - monster.height) {
      monster.vy *= -1;
      monster.y = clamp(monster.y, 0, bounds.height - monster.height);
    }
  });
}

function renderGameObjects() {
  elements.playerSprite.style.transform = `translate(${state.player.x}px, ${state.player.y}px)`;
  elements.collectible.style.left = `${state.collectible.x}px`;
  elements.collectible.style.top = `${state.collectible.y}px`;
  state.monsters.forEach((monster) => {
    monster.element.style.transform = `translate(${monster.x}px, ${monster.y}px)`;
  });
}

function detectCollectibleCollision() {
  if (!collides(state.player, state.collectible)) return;
  collectCrystal();
}

async function collectCrystal() {
  const amount = Math.min(30, 10 + (state.combo - 1) * 5);
  state.collected += 1;
  showFloat(`+${amount} puntos`, state.collectible.x, state.collectible.y);
  moveCollectible();
  bumpCombo();
  updateHud();

  try {
    const balance = await apiFetch(`/api/v1/users/${state.userId}/points/auto`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount }),
    });
    updateBalance(balance);
    refreshLeaderboard();
    logActivity(`Cristal recolectado: +${amount} puntos.`);
  } catch (error) {
    logActivity(error.message);
  }
}

function detectMonsterCollision() {
  if (performance.now() < state.hitCooldownUntil) return;

  const hit = state.monsters.some((monster) => collides(state.player, monster));
  if (!hit) return;

  state.hitCooldownUntil = performance.now() + 900;
  elements.playerSprite.classList.remove("hit");
  void elements.playerSprite.offsetWidth;
  elements.playerSprite.classList.add("hit");
  showFloat("Combo perdido", state.player.x, state.player.y, true);
  resetCombo();
  logActivity("Tocaste un monstruo: combo reiniciado.");
  updateHud();
}

function moveCollectible() {
  const bounds = getArenaBounds();
  const candidates = getCollectibleSpawnPoints(bounds).filter((point) => {
    const candidate = { ...point, width: state.collectible.width, height: state.collectible.height };
    return (
      !collides(candidate, state.player) &&
      state.monsters.every((monster) => !collides(candidate, monster))
    );
  });
  const nextPoint = candidates.length > 0
    ? candidates[randomBetween(0, candidates.length - 1)]
    : { x: gridSize * 3, y: gridSize * 3 };

  state.collectible.x = nextPoint.x;
  state.collectible.y = nextPoint.y;
}

function getCollectibleSpawnPoints(bounds) {
  const points = [];
  const minColumn = 2;
  const maxColumn = Math.max(minColumn, Math.floor((bounds.width - gridSize * 2) / gridSize));
  const minRow = 2;
  const maxRow = Math.max(minRow, Math.floor((bounds.height - gridSize * 2) / gridSize));

  for (let column = minColumn; column <= maxColumn; column += 1) {
    for (let row = minRow; row <= maxRow; row += 1) {
      points.push({
        x: column * gridSize + (gridSize - state.collectible.width) / 2,
        y: row * gridSize + (gridSize - state.collectible.height) / 2,
      });
    }
  }

  return points;
}

function bumpCombo() {
  state.combo = Math.min(5, state.combo + 1);
  clearTimeout(state.comboTimer);
  state.comboTimer = setTimeout(() => {
    resetCombo();
    updateHud();
  }, 3200);
}

function resetCombo() {
  state.combo = 1;
  clearTimeout(state.comboTimer);
}

async function convertPoints() {
  if (!state.connected) {
    logActivity("Conecta un jugador antes de convertir.");
    return;
  }

  const points = Number.parseInt(elements.convertAmount.value, 10);
  if (!Number.isFinite(points) || points <= 0) {
    logActivity("Ingresa una cantidad valida de puntos.");
    return;
  }

  elements.convertButton.disabled = true;
  try {
    const balance = await apiFetch("/api/v1/users/me/convert", {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ points }),
    });
    updateBalance(balance);
    refreshLeaderboard();
    showCoinCelebration();
    showFloat("Coins ganadas", state.player.x, state.player.y);
    logActivity(`${points} puntos convertidos a coins.`);
  } catch (error) {
    logActivity(error.message);
  } finally {
    elements.convertButton.disabled = false;
  }
}

function connectWebSocket() {
  clearTimeout(state.reconnectTimer);
  if (state.socket) {
    state.socket.close();
    state.socket = null;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${protocol}//${window.location.host}/api/v1/ws/${state.userId}`;
  const socket = new WebSocket(url);
  state.socket = socket;

  socket.addEventListener("open", () => updateConnection("Conectado en tiempo real", "connected"));
  socket.addEventListener("message", (event) => {
    try {
      const payload = JSON.parse(event.data);
      updateBalance(payload);
      refreshLeaderboard();
      logActivity(`Evento realtime: ${formatAction(payload.action)}.`);
    } catch {
      logActivity("Evento realtime recibido.");
    }
  });
  socket.addEventListener("close", () => {
    if (!state.connected) return;
    updateConnection("Reconectando...", "error");
    state.reconnectTimer = setTimeout(connectWebSocket, 2500);
  });
  socket.addEventListener("error", () => updateConnection("WebSocket sin conexion", "error"));
}

async function apiFetch(path, options = {}) {
  const response = await fetch(path, options);
  const contentType = response.headers.get("content-type") || "";
  const hasBody = response.status !== 204 && response.headers.get("content-length") !== "0";
  const payload = hasBody && contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok) {
    const detail = payload && payload.detail ? payload.detail : `Error HTTP ${response.status}`;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join(", ") : detail);
  }

  return payload;
}

function updateBalance(payload) {
  state.balance.points = payload.points;
  state.balance.coins = payload.coins;
  updateHud();
}

function updateHud() {
  elements.pointsValue.textContent = state.balance.points;
  elements.coinsValue.textContent = state.balance.coins;
  elements.comboValue.textContent = `x${state.combo}`;
  elements.collectedValue.textContent = state.collected;
  elements.timeLeft.textContent = `${state.timeLeft}s`;
  elements.startButton.textContent = state.playing ? "Reiniciar partida" : "Iniciar partida";
}

function updateConnection(text, mode = "") {
  elements.connectionStatus.textContent = text;
  elements.connectionStatus.className = "status-pill";
  if (mode) elements.connectionStatus.classList.add(mode);
}

function startPresenceUpdates() {
  clearInterval(state.heartbeatTimer);
  clearInterval(state.leaderboardTimer);
  sendHeartbeat();
  state.heartbeatTimer = setInterval(sendHeartbeat, 15000);
  state.leaderboardTimer = setInterval(refreshLeaderboard, 10000);
}

async function sendHeartbeat() {
  if (!state.connected || !state.userId) return;

  try {
    await apiFetch("/api/v1/demo/players/heartbeat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: state.userId }),
    });
  } catch (error) {
    logActivity(`No se pudo enviar presencia: ${error.message}`);
  }
}

async function refreshLeaderboard() {
  try {
    const leaderboard = await apiFetch("/api/v1/demo/leaderboard");
    renderLeaderboard(leaderboard);
  } catch (error) {
    logActivity(`No se pudo actualizar el ranking: ${error.message}`);
  }
}

function renderLeaderboard(leaderboard) {
  if (!leaderboard || leaderboard.length === 0) {
    elements.leaderboardList.innerHTML = '<li class="empty-row">Todavia no hay jugadores en el ranking.</li>';
    return;
  }

  elements.leaderboardList.innerHTML = leaderboard.map((entry) => {
    const currentPlayerClass = entry.user_id === state.userId ? " current-player" : "";
    const status = entry.connected ? "Conectado" : "Sin conexion reciente";
    return `
      <li class="${currentPlayerClass}">
        <span class="rank">#${entry.position}</span>
        <span>
          <span class="player-name">${escapeHtml(entry.display_name)}</span>
          <span class="player-status">${status} · ${entry.points} pts</span>
        </span>
        <span class="coins">
          <img src="/assets/coin.png" alt="" />
          ${entry.coins}
        </span>
      </li>
    `;
  }).join("");
}

function showCoinCelebration() {
  const colors = ["#ffd166", "#68e1fd", "#77f5a9", "#ff6685", "#8b5cf6", "#ffffff"];
  const celebration = document.createElement("div");
  celebration.className = "coin-celebration";
  celebration.innerHTML = '<img src="/assets/coin.png" alt="Coin ganada" />';

  for (let index = 0; index < 24; index += 1) {
    const piece = document.createElement("span");
    const angle = (Math.PI * 2 * index) / 24;
    const distance = randomBetween(54, 132);
    piece.className = "confetti-piece";
    piece.style.setProperty("--confetti-x", `${Math.cos(angle) * distance}px`);
    piece.style.setProperty("--confetti-y", `${Math.sin(angle) * distance}px`);
    piece.style.setProperty("--confetti-rotate", `${randomBetween(0, 180)}deg`);
    piece.style.setProperty("--confetti-color", colors[index % colors.length]);
    celebration.appendChild(piece);
  }

  elements.floatingLayer.appendChild(celebration);
  setTimeout(() => celebration.remove(), 1300);
}

function showFloat(text, x, y, danger = false) {
  const item = document.createElement("span");
  item.className = danger ? "float-text danger" : "float-text";
  item.textContent = text;
  item.style.left = `${x}px`;
  item.style.top = `${y}px`;
  elements.floatingLayer.appendChild(item);
  setTimeout(() => item.remove(), 1000);
}

function logActivity(message) {
  const item = document.createElement("li");
  item.textContent = `${new Date().toLocaleTimeString()} - ${message}`;
  elements.activityLog.prepend(item);

  while (elements.activityLog.children.length > 8) {
    elements.activityLog.lastElementChild.remove();
  }
}

function toggleSound() {
  state.soundEnabled = !state.soundEnabled;
  elements.soundButton.textContent = state.soundEnabled ? "Silenciar" : "Sonido";

  if (state.soundEnabled) {
    elements.arcadeSound.volume = 0.22;
    elements.arcadeSound.play().catch(() => {
      state.soundEnabled = false;
      elements.soundButton.textContent = "Sonido";
      logActivity("El navegador bloqueo el audio automatico.");
    });
  } else {
    elements.arcadeSound.pause();
  }
}

function normalizePlayerName(value) {
  return value.trim().replace(/\s+/g, " ");
}

function getOrCreateUserIdForName(playerName) {
  const playerIds = readPlayerIds();
  const key = playerName.toLocaleLowerCase();

  if (!playerIds[key]) {
    playerIds[key] = createUuid();
    localStorage.setItem(storageKeys.playerIds, JSON.stringify(playerIds));
  }

  return playerIds[key];
}

function readPlayerIds() {
  try {
    return JSON.parse(localStorage.getItem(storageKeys.playerIds)) || {};
  } catch {
    return {};
  }
}

function escapeHtml(value) {
  const element = document.createElement("span");
  element.textContent = value;
  return element.innerHTML;
}

function authHeaders() {
  return { "x-user-id": state.userId };
}

function keyToDirection(key) {
  const normalized = key.toLowerCase();
  if (normalized === "arrowleft" || normalized === "a") return "left";
  if (normalized === "arrowright" || normalized === "d") return "right";
  if (normalized === "arrowup" || normalized === "w") return "up";
  if (normalized === "arrowdown" || normalized === "s") return "down";
  return null;
}

function isTextInput(target) {
  return (
    target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement ||
    target instanceof HTMLSelectElement ||
    target.isContentEditable
  );
}

function getArenaBounds() {
  const rect = elements.arena.getBoundingClientRect();
  return { width: rect.width, height: rect.height };
}

function collides(a, b) {
  return (
    a.x < b.x + b.width &&
    a.x + a.width > b.x &&
    a.y < b.y + b.height &&
    a.y + a.height > b.y
  );
}

function randomBetween(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function createUuid() {
  if (window.crypto && window.crypto.randomUUID) {
    return window.crypto.randomUUID();
  }

  return "10000000-1000-4000-8000-100000000000".replace(/[018]/g, (char) => {
    const value = Number(char) ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (Number(char) / 4)));
    return value.toString(16);
  });
}

function formatAction(action) {
  const labels = {
    assign_points: "puntos asignados",
    convert_points_to_coins: "puntos convertidos a coins",
    deduct_points: "puntos descontados",
    deduct_coins: "coins descontadas",
  };
  return labels[action] || action || "balance actualizado";
}

init();
