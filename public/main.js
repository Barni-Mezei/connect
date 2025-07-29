let errorMessage = document.getElementById("error_message");
let connnectButton = document.getElementById("connect_button");
let connnectMenu = document.getElementById("connect_menu");
let terminalText = document.getElementById("terminal_text_input");
let terminalColor = document.getElementById("terminal_color");
let colorTheme = document.getElementById("color_theme");
let contextMenu = document.getElementById("context_menu");

//Start by disabling editing on the page, until the connection is made
terminalColor.contentEditable = false;
terminalText.disabled = true;

//Hide context menu
contextMenu.classList.add("hidden");

function changeTheme(fileName = "ubuntu") {
    colorTheme.href = `public/colors/${fileName}.css`
}

//Alias
let setTheme = changeTheme;

function getThemes() {
    console.log("ubuntu", "windows");
}

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

//Synchronises the terminal text to the visual one
function syncTerminalText() {
    let terminalTextDisplay = document.getElementById("terminal_text_display");

    if (!terminalTextDisplay) return;

    let textBeforeCursor = terminalText.value.substring(0, terminalText.selectionStart);
    let textUnderCursor = terminalText.value[terminalText.selectionStart] ?? " ";
    let textAfterCursor = terminalText.value.substring(terminalText.selectionStart + 1, terminalText.value.length + 1);

    terminalTextDisplay.innerHTML = `${textBeforeCursor}<span class="effect-reverse">${textUnderCursor}</span>${textAfterCursor}`;
}

// on blur, re-grab focus
terminalText.onblur = function (e) {
    terminalText.focus();
}

terminalText.onfocus = function (e) {
    terminalText.selectionStart = terminalText.value.length;
    terminalText.selectionEnd = terminalText.value.length;
    syncTerminalText();
}

terminalText.onkeydown = function (e) {
    syncTerminalText();

    if (e.ctrlKey || e.altKey) {
        if (e.key == "Control" || e.key == "Alt") return;

        sendKey({
            "ctrl": e.ctrlKey,
            "alt": e.altKey,
        }, e.key);

        return;
    }

    if (e.key == "Enter") {
        sendCommand(terminalText.value);
        terminalText.value = "";
    }
}

terminalText.onkeyup = function (e) {
    syncTerminalText();
}

//Update visual text on typing
terminalText.onbeforeinput = function (e) {
    syncTerminalText();
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

function sendKey(modifiers, key) {
    let data = {
        "id": sessionStorage.getItem("id"),
        "type": "control",
        "mode": "key",
        "modifiers": modifiers,
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

<span class="effect-slow-blink">Slow</span> \
<span class="effect-fast-blink">Fast</span>

`;
    terminalText.value = "";
};

//Show closing message
ws.onclose = function (e) {
    console.log("Socket closed!", e);

    let reason = e.reason;
    if (reason == "") reason = "Server not responding";

    terminalColor.innerHTML = `<span class="color-fg-red">Websocket connection closed!</span>
Reason: ${reason}`;
    terminalText.value = "";

    terminalColor.contentEditable = false;
    terminalText.disabled = true;
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
                terminalText.value = "";
            }
            break;

        case "ssh_message":
            if (data.category == "error") {
                //SSH Connection error
                console.error("SSH Error", data.message);

                terminalColor.innerHTML += `<span class="color-fg-red">SSH Error: ${data.message}</span>\n`;
                terminalText.value = "";

                terminalColor.contentEditable = false;
                terminalText.disabled = true;
            }

            if (data.category == "info") {
                //SSH Connection information
                //console.log("SSH Info", data.message);

                terminalColor.innerHTML += `SSH Info: <span class="color-fg-bright-green">${data.message}</span>\n`;
                terminalText.value = "Hello, world!";

                terminalColor.contentEditable = false;
                terminalText.disabled = true;
            }

            if (data.category == "data") {
                //SSH Screen data
                //console.log("SSH screen", data.message);

                //Remove previous text display
                document.getElementById("terminal_text_display")?.remove();

                terminalColor.innerHTML += `${data.message}<span id="terminal_text_display"></span>`;
                terminalColor.scrollTop = terminalColor.scrollHeight;

                terminalColor.contentEditable = false;
                terminalText.disabled = false;
                terminalText.focus();
                syncTerminalText();
            }

            break;

        default:
            break;
    }
}