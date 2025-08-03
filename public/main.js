let errorMessage = document.getElementById("error_message");
let connnectButton = document.getElementById("connect_button");
let connnectMenu = document.getElementById("connect_menu");
let terminalColor = document.getElementById("terminal_color");
let colorTheme = document.getElementById("color_theme");
let contextMenu = document.getElementById("context_menu");

let captureAll = true;
let hasSsh = false;

// Disable editing to the terminal
terminalColor.contentEditable = false;

// Hide context menu
contextMenu.classList.add("hidden");

function changeTheme(fileName = "ubuntu") {
    colorTheme.href = `public/colors/${fileName}.css`
}

// Alias to change theme
let setTheme = changeTheme;

function getThemes() {
    console.log("ubuntu", "windows");
}

// Custom right click menu
function contextMenuOpen() {
    contextMenu.classList.remove("hidden");
}

//********
//* MAIN *
//********

let urlSearch = new URLSearchParams(window.location.search);

document.querySelector("#connect_menu #ssh_address").value = urlSearch.get("address") ?? "";
document.querySelector("#connect_menu #ssh_port").value = urlSearch.get("port") ?? "22";
document.querySelector("#connect_menu #ssh_username").value = urlSearch.get("username") ?? "";

//Send SSH connect request to the server
connnectButton.onclick = function () {
    errorMessage.textContent = "";

    let inputs = connnectMenu.querySelectorAll("input");
    let connectData = {};

    inputs.forEach((input, index) => {
        connectData[input.getAttribute("name")] = input.value;
    });

    connectData["type"] = "connect";

    console.log(connectData);

    ws.send(JSON.stringify(connectData));
}

let formInputs = connnectMenu.querySelectorAll("input");

formInputs.forEach(function (f) {
    f.onkeydown = function (e) {
        if (e.key == "Enter") {
            connnectButton.click();
        }
    }
});

// Send every keypres to the server
window.onkeydown = function (e) {
    if (!hasSsh) return;

    //console.log(e);

    // Do not enable F key functions, capture them instead
    if (captureAll) {
        e.preventDefault();
    }

    // Do not send "shift pressed" events
    if (e.key == "Control" || e.key == "Alt" || e.key == "Shift") return;

    let codeOut = "";

    if (e.ctrlKey) {
        let charCode = e.charCode || e.which || e.keyCode;
    
        if (charCode >= 65 && charCode <= 90) { // From A to Z (uppercase)
            codeOut = String.fromCharCode(charCode - 64);
        } else if (charCode === 32) {
            codeOut = "\x00";
        }
    }

    // Special keys
    if (e.key.length > 1) {
        // Replace special keys, do not send event if key was not found
        switch (e.key) {
            case "Backspace":
                codeOut = "\b";
                break;

            case "Delete":
                codeOut = "\x7F";
                break;

            case "Tab":
                codeOut = "\t";
                break;

            case "Enter":
                codeOut = "\n";
                break;

            //Arrow keys
            case "ArrowUp":
                codeOut = "\x1b[A";
                break;

            case "ArrowDown":
                codeOut = "\x1b[B";
                break;

            case "ArrowRight":
                codeOut = "\x1b[C";
                break;

            case "ArrowLeft":
                codeOut = "\x1b[D";
                break;

            //Function keys
            case "F1":
                codeOut = "\x1b[11";
                break;
                
            case "F2":
                codeOut = "\x1b[12";
                break;
                
            case "F3":
                codeOut = "\x1b[13";
                break;
                
            case "F4":
                codeOut = "\x1b[14";
                break;
                
            case "F5":
                codeOut = "\x1b[15";
                break;
                
            case "F6":
                codeOut = "\x1b[17";
                break;
                
            case "F7":
                codeOut = "\x1b[18";
                break;
                
            case "F8":
                codeOut = "\x1b[19";
                break;
                
            case "F9":
                codeOut = "\x1b[20";
                break;
                
            case "F10":
                codeOut = "\x1b[21";
                break;
                
            case "F11":
                codeOut = "\x1b[23";
                break;
                
            case "F12":
                codeOut = "\x1b[24";
                break;

            // Do not send key, it it is special, but not recognised
            default:
                return;
        }
    } else if (codeOut == "") { // No special char was pressed
        // Regular letters
        codeOut = e.key;
    }
    
    sendKey(codeOut);
}

//Create websocket
const server = window.location.host;
ws = new WebSocket(`ws://${server}/websocket`);

//Websocket functions
function sendCommand(command) {
    let data = {
        "id": sessionStorage.getItem("id"),
        "type": "control",
        "mode": "command",
        "value": command,
    }

    ws.send(JSON.stringify(data));
}

function sendKey(key) {
    let data = {
        "id": sessionStorage.getItem("id"),
        "type": "control",
        "mode": "key",
        "value": key,
    }

    ws.send(JSON.stringify(data));
}

//Show availability on open
ws.onopen = function (e) {
    console.log("Socket opened!", e);

    terminalColor.innerHTML = `Websocket connection successful! Please provide ssh credentials to continue.
<span class="color-fg-yellow effect-bold">WARNING: This is NOT an encrypted channel. Meaning, your password can be easily stolen!</span>



<span class="color-fg-black">FG</span> <span class="color-bg-black">BG</span> \
<span class="color-fg-red">FG</span> <span class="color-bg-red">BG</span> \
<span class="color-fg-green">FG</span> <span class="color-bg-green">BG</span> \
<span class="color-fg-yellow">FG</span> <span class="color-bg-yellow">BG</span> \
<span class="color-fg-blue">FG</span> <span class="color-bg-blue">BG</span> \
<span class="color-fg-magenta">FG</span> <span class="color-bg-magenta">BG</span> \
<span class="color-fg-cyan">FG</span> <span class="color-bg-cyan">BG</span> \
<span class="color-fg-white">FG</span> <span class="color-bg-white">BG</span> \

<span class="color-fg-bright-black">FG</span> <span class="color-bg-bright-black">BG</span> \
<span class="color-fg-bright-red">FG</span> <span class="color-bg-bright-red">BG</span> \
<span class="color-fg-bright-green">FG</span> <span class="color-bg-bright-green">BG</span> \
<span class="color-fg-bright-yellow">FG</span> <span class="color-bg-bright-yellow">BG</span> \
<span class="color-fg-bright-blue">FG</span> <span class="color-bg-bright-blue">BG</span> \
<span class="color-fg-bright-magenta">FG</span> <span class="color-bg-bright-magenta">BG</span> \
<span class="color-fg-bright-cyan">FG</span> <span class="color-bg-bright-cyan">BG</span> \
<span class="color-fg-bright-white">FG</span> <span class="color-bg-bright-white">BG</span>

<span class="effect-bold">Bold</span> \
<span>Normal</span> \
<span class="effect-dim">Light</span>

<span class="effect-italic">Italic</span> \
<span class="effect-underline">Underline</span> \
<span class="effect-striketrough">Striketrough</span> \
<span class="effect-reverse color-bg-black">Reverse</span>

Blink <span class="effect-slow-blink">Slow</span> \
<span class="effect-fast-blink">Fast</span>

`;
};

//Show closing message
ws.onclose = function (e) {
    console.log("Socket closed!", e);

    let reason = e.reason;
    if (reason == "") reason = "Server not responding";

    terminalColor.innerHTML = `<span class="color-fg-red">Websocket connection closed!</span>
Reason: ${reason}`;
    terminalColor.contentEditable = false;
    hasSsh = false;
};



ws.onmessage = function (e) {
    //console.log("Message received:", e);

    let data = e.data;

    try {
        data = JSON.parse(e.data);
    } catch {
        console.error("Invalid data received!", e);
        return;
    }

    switch (data.type) {
        case "validate":
            if (data.state == "fail") {
                errorMessage.textContent = data.reason;
            }

            if (data.state == "pass") {
                //Store user id for later usage
                sessionStorage.setItem("id", data.id);
                sessionStorage.setItem("address", data.address);
                sessionStorage.setItem("port", data.port);
                sessionStorage.setItem("username", data.username);

                errorMessage.textContent = "";
                connnectMenu.classList.add("hidden");

                console.log("Logged in with", data.id, e);

                terminalColor.innerHTML = `Connecting to <span class="color-fg-bright-black">${data.username}@${data.address}</span>\n`;
            }
            break;

        case "ssh_message":
            if (data.category == "error") {
                //SSH Connection error
                console.error("SSH Error", data.message);

                terminalColor.innerHTML += `<span class="color-fg-red">SSH Error: ${data.message}</span>\n`;

                hasSsh = false;
            }

            if (data.category == "info") {
                //SSH Connection information
                //console.log("SSH Info", data.message);

                terminalColor.innerHTML += `SSH Info: <span class="color-fg-bright-green">${data.message}</span>\n`;

                hasSsh = true;
            }

            if (data.category == "data") {
                //SSH text data or screen control
                //console.log("SSH message", data.message, `'${data.message}'`);

                switch (data.message.type) {
                    // New text content
                    case "html":
                        console.log(data.message.value);
                        terminalColor.innerHTML += `${data.message.value}`;
                        break;

                    // Screen control commands
                    case "control":
                        switch (data.message.value) {
                            case "clear": // Clears the screen
                                terminalColor.innerHTML = `<span class="color-fg-bright-black">Cleared with mode: ${data.message.mode}</span>\n`;
                                break;

                            case "cursor": // Sets the cursor position
                                terminalColor.innerHTML += `<span class="color-fg-bright-black">Cursor pos X: ${data.message.x} Y: ${data.message.y}</span>\n`;
                                break;
                        }

                    break;
                }

                terminalColor.scrollTop = terminalColor.scrollHeight;
            }

            break;

        default:
            break;
    }
}