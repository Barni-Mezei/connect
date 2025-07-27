let c = document.getElementById("maincv");
let ctx = c.getContext("2d");

resizeWin();

function resizeWin() {
	c.width = c.offsetWidth;
	c.height = c.offsetHeight;
}

window.onresize = resizeWin;

//Synced values
let level = {};
let players = {}; //Other players, stored by id

let id = "";
let player_name = "";
let team = "";
let x = 0;
let y = 0;
let angle = 0;
let hp = 100;
let bullets = [];


let particles = [];

let magazineCapacity = 15;
let ammoInMagazine = magazineCapacity;

let cooldown = 0;
let cooldownType = "";//Not empty if there is a cooldown

const server = window.location.host;
let last_sync_time = 0;
let ping = 0;

let loopRunning = false;

//Input interfaves
let keys = {
	up: false,
	down: false,
	left: false,
	right: false,
	reload: false,
}

let mouse = {
	x: 0,
	y: 0,
	down: 0,
	oldDown: 0,
}

let settings = {
	frendlyFire: false,
}

//Input events
window.onkeydown = function (e) {
	if (e.key == "w" || e.key == "ArrowUp") keys.up = true;
	if (e.key == "a" || e.key == "ArrowLeft") keys.left = true;
	if (e.key == "s" || e.key == "ArrowDown") keys.down = true;
	if (e.key == "d" || e.key == "ArrowRight") keys.right = true;
	if (e.key == "r") keys.reload = true;
}

window.onkeyup = function (e) {
	if (e.key == "w" || e.key == "ArrowUp") keys.up = false;
	if (e.key == "a" || e.key == "ArrowLeft") keys.left = false;
	if (e.key == "s" || e.key == "ArrowDown") keys.down = false;
	if (e.key == "d" || e.key == "ArrowRight") keys.right = false;
	if (e.key == "r") keys.reload = false;
}

function setMousePos(event) {
	mouse.x = event.clientX;
	mouse.y = event.clientY;
}

window.onmousemove = function (e) {
	setMousePos(e);
}

window.onmousedown = function (e) {
	mouse.down = true;
	setMousePos(e);
}

window.onmouseup = function (e) {
	mouse.down = false;
	setMousePos(e);
}

//Disable inputs whn clicked away
window.onblur = function () {
	keys.up = false;
	keys.right = false;
	keys.down = false;
	keys.left = false;
	keys.reload = false;
}

//Load player name
document.getElementById("name").value = localStorage.getItem("name") ?? "";

//*************
//* Main loop *
//*************
let loopCounter = 0;
function mainLoop() {
	loopCounter++;

	if (cooldown > 0) {
		if (cooldownType == "respawn") hp = 100;
		cooldown--;

		if (cooldownType == "reload" && cooldown == 0) ammoInMagazine = magazineCapacity;
		if (cooldown == 0) cooldownType = "";
	}
	
	if (cooldownType != "respawn") {
		let speed = 3;
		if (keys.up) y -= speed;
		if (keys.right) x += speed;
		if (keys.down) y += speed;
		if (keys.left) x -= speed;
	}

	if (cooldownType == "") {
		if (mouse.down && !mouse.oldDown) {
			if (ammoInMagazine > 0) {
				ammoInMagazine--;
				bullets.push(new Bullet(x, y, angle));
			}
			
			if (ammoInMagazine <= 0) {
				cooldown = 50;
				cooldownType = "reload";
			}
		}

		if (keys.reload) {
			cooldown = 30;
			cooldownType = "reload";
		}	
	}

	angle = getAngle(c.width / 2, c.height / 2, mouse.x, mouse.y);
	
	collidePlayer();

	ws_send({
		"event": "sync",
		"id": id,
		"x": Math.round(x*100)/100, //Round to 2 decimal places, for shorter numbers
		"y": Math.round(y*100)/100,
		"angle": Math.round(angle),
		//"name": player_name,
		//"team": team,
		"bullets": bullets.map(b => b.getJSON()),
		"hp": hp,
	});

	//Walking particles
	let r = 5;
	particles.push(new Particle(randFloat(x - r, x + r), randFloat(y - r, y + r)));

	ctx.clearRect(0, 0, c.width, c.height);
	update();
	render();

	mouse.oldDown = mouse.down;

	if (loopRunning) requestAnimationFrame(mainLoop);
}

function lobbyLoop() {
	ws_send({
		"event": "lobby",
	})

	if (!loopRunning) setTimeout(lobbyLoop, 1000);
}

function spawnPlayer() {
	let spawnIndex = randInt(0, level.spawns.length - 1)
	x = level.spawns[spawnIndex].x;
	y = level.spawns[spawnIndex].y;
	hp = 100;
	ammoInMagazine = magazineCapacity;
}

function setLevel(newLevel) {
	level = {};
	level = newLevel;

	level.bounding = {
		x: level.bounding.x * level.scale,
		y: level.bounding.y * level.scale,
		width: level.bounding.width * level.scale,
		height: level.bounding.height * level.scale,
	}

	level.walls.forEach((w, index) => {
		level.walls[index] = {
			x: w.x * level.scale,
			y: w.y * level.scale,
			width: w.width * level.scale,
			height: w.height * level.scale,
		}
	});

	level.spawns.forEach((s, index) => {
		level.spawns[index] = {
			x: s.x * level.scale,
			y: s.y * level.scale,
		}
	});
}

function joinTeam(teamName) {
	player_name = document.getElementById("name").value;
	ws_send({
		"event": "join",
		"team": teamName,
		"name": player_name,
	});

	localStorage.setItem("name", player_name);
}

//*************
//* Websocket *
//*************
if ("WebSocket" in window) {
	websocket = true;
} else {
	//No web socket support
	websocket = false;
}

//Senfd first message (open websocket)
var msg = { event: "register" };
open_ws();

function ws_send(msg) {
	if (websocket == true) {
		// if ws is not open call open_ws, which will call ws_send back
		if (typeof (ws) == 'undefined' || ws.readyState === undefined || ws.readyState > 1) {
			open_ws(msg);
		} else {
			ws.send(JSON.stringify(msg));
			//console.log("ws_send sent");
		}
	}
}


function open_ws(/*msg*/) {
	if (typeof (ws) == 'undefined' || ws.readyState === undefined || ws.readyState > 1) {
		// websocket on same server with address /websocket
		ws = new WebSocket(`ws://${server}/websocket`);

		ws.onopen = function (msg) {
			console.log("Socket opened!");
			lobbyLoop();
		};

		ws.onmessage = function (evt) {
			//console.log(evt.data);
			msg = JSON.parse(evt.data)

			switch (msg.event) {
				case "join":
					pushNotification(`${getColoredPlayer(msg.name, msg.team)} joined the game!`, "side", "#ffffff", "game")
					break;

				case "leave":
					delete players[msg.id];
					pushNotification(`${getColoredPlayer(msg.name, msg.team)} left the game.`, "side", "#ffffff", "game")
					break;

				case "validate":
					if (msg.state == "fail") {
						pushNotification(msg.reason, "top", "#ff0000", "lobby")
						break;
					}

					id = msg.id;
					player_name = msg.name;
					team = msg.team;
					setLevel(msg.level);

					settings = msg.settings;

					spawnPlayer();

					pushNotification(`You are in team ${team}`, "top", teamColors[team], "lobby")

					//Start game if not started yet.
					if (!loopRunning) {
						document.getElementById("lobby").style.display = "none";
						loopRunning = true;
						mainLoop();
					}
					break;

				case "death":
					let victimName = players[msg.id]?.name;
					let victimTeam = players[msg.id]?.team;
					let killerName = players[msg.killer]?.name;
					let killerTeam = players[msg.killer]?.team;

					if (msg.id == id) { victimName = player_name; victimTeam = team; }
					if (msg.killer == id) { killerName = player_name; killerTeam = team; }

					pushNotification(`${getColoredPlayer(killerName, killerTeam)} killed ${getColoredPlayer(victimName, victimTeam)}`, "side", "#ffcccc", "game")
					break;

				case "sync":
					players[msg.id] = {
						name: msg.name,
						team: msg.team,
						x: msg.x,
						y: msg.y,
						angle: msg.angle,
						bullets: msg.bullets,
						hp: msg.hp,
					}

					ping = msg.time - last_sync_time;
					last_sync_time = msg.time;
					break;

				case "syncServer":
					switch (msg.subEvent) {
						case "settings":
							for (let key in msg.settings) {
								settings[key] = msg.settings[key];
							}
							break;

						case "level":
							setLevel(msg.level);
							spawnPlayer();
							pushNotification("Map changed!", "side", "#ddff00", "all");
							break;

						case "hit":
							hp -= 10;

							//Handle respawning
							if (hp <= 0) {
								ws_send({
									"event": "death",
									"id": id,
									"killer": msg.killer,
								});

								spawnPlayer();
								cooldown = 80;
								cooldownType = "respawn";
							}
							break;
						
						case "lobby":
							//Update lobby text
							for (let team in msg.teams) {
								let element = document.querySelector(`.teamChooser .${team}`);
								if (element == null) continue;
								element.querySelector(`#score span`).textContent = padText( msg.teams[team].score, 3, " ");
								element.querySelector(`#players span`).textContent = msg.teams[team].members;
							}
							//FALLTROUGH! Continue with score update
						case "score":
							//Update in-game text
							for (let team in msg.teams) {
								let element = document.querySelector(`#scores span.${team}`);
								if (element == null) continue;
								element.textContent = msg.teams[team].score;
							}
							break;
					}
					break;

					case "kick":
						pushNotification(`You have been kicked.`, "side", "#ff0000", "all")
						console.log("Kicked.", msg.reason);
						document.getElementById("offline").style.display = "block";
						document.getElementById("offline").textContent = msg.reason;
						loopRunning = false;
						websocket = false;
						break;

				default: break;
			}
		};

		ws.onclose = function () {
			pushNotification("Connection is closed.", "top", "#ff0000", "all")
			console.log("Connection is closed.");
			document.getElementById("offline").style.display = "block";
			loopRunning = false;
			websocket = false;
		};
	}
}
