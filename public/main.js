// SSH Connection
let connectMenu = document.getElementById("connect_menu");
let connectMenuButton = document.getElementById("connect_menu_button");
let connectButton = document.getElementById("connect_button");
let errorMessage = document.getElementById("error_message");

// Page settings
let settingsMenu = document.getElementById("settings_menu");
let settingsMenuButton = document.getElementById("settings_menu_button");
let settingsReload = document.getElementById("settings_button_reload");
let settingsClear = document.getElementById("settings_button_clear");
let settingsScroll = document.getElementById("settings_button_scroll");
let settingsTheme = document.getElementById("settings_input_theme");
let settingsCapture = document.getElementById("settings_input_capture");

// Other elements
let navMenu = document.querySelector(".nav"); // Menu button container
let menuContainer = document.querySelector(".menus"); // Menu container
let terminalColor = document.getElementById("terminal_color"); // The terminal text display
let colorTheme = document.getElementById("color_theme"); // Link to the style sheet

// Is there an ssh connection already?
let hasSsh = false;

// Modifies the path to the terminal theme style sheet
function changeTheme(fileName = "ubuntu") {
    colorTheme.href = `public/colors/${fileName}.css`
}

//******
//* UI *
//******

// Toggle connect menu
connectMenuButton.onclick = function (e) {
    connectMenu.classList.remove("hidden");
    connectMenu.classList.toggle("open");
    connectMenu.classList.toggle("close");
}

connectMenu.onanimationend = function (e) {
    if (e.animationName == "menu-close") {
        connectMenu.classList.add("hidden");
    }
}

// Toggle page settings menu
settingsMenuButton.onclick = function (e) {
    settingsMenu.classList.remove("hidden");
    settingsMenu.classList.toggle("open");
    settingsMenu.classList.toggle("close");
}

settingsMenu.onanimationend = function (e) {
    if (e.animationName == "menu-close") {
        settingsMenu.classList.add("hidden");
    }
}

settingsReload.onclick = function (e) {
    window.location.reload();
}

settingsClear.onclick = function (e) {
    if (!hasSsh) return;

    terminalColor.innerHTML = "";
    sendCommand("clear");
}

settingsScroll.onclick = function (e) {
    terminalColor.scrollTop = terminalColor.scrollHeight;
    terminalColor.scrollLeft = 0;
}

settingsTheme.onchange = function (e) {
    changeTheme(settingsTheme.value);
}

// Connect form sent
connectButton.onclick = function () {
    errorMessage.textContent = "";

    let inputs = connectMenu.querySelectorAll("input, select");
    let connectData = {};

    inputs.forEach((input, index) => {
        connectData[input.getAttribute("name")] = input.value;
    });

    connectData["type"] = "connect";

    console.log(connectData);

    ws.send(JSON.stringify(connectData));
}

window.onmousedown = function (e) {
    if (navMenu.contains(e.target)) return;
    if (menuContainer.contains(e.target)) return;

    // Close all menus

    for (let i = 0; i < menuContainer.children.length; i++) {
        menuContainer.children[i].classList.remove("open");
        menuContainer.children[i].classList.add("close");
    }
}

//********
//* MAIN *
//********

let urlSearch = new URLSearchParams(window.location.search);

document.querySelector("#connect_menu #ssh_address").value = urlSearch.get("address") ?? "";
document.querySelector("#connect_menu #ssh_port").value = urlSearch.get("port") ?? "22";
document.querySelector("#connect_menu #ssh_username").value = urlSearch.get("username") ?? "";


// Send form on enter
let formInputs = connectMenu.querySelectorAll("input");

formInputs.forEach(function (f) {
    f.onkeydown = function (e) {
        if (e.key == "Enter") {
            connectButton.click();
        }
    }
});

// Send every keypress to the server
window.onkeydown = function (e) {
    if (!hasSsh) return;

    //console.log(e);

    if (settingsCapture.checked) {
        e.preventDefault();
    }

    // Do not send "shift pressed" events
    if (e.key == "Control" || e.key == "Alt" || e.key == "Shift") return;

    let codeOut = "";

    if (e.ctrlKey) {
        let charCode = e.charCode || e.which || e.keyCode;
    
        // Special: Reload page if Ctrl + F5c was pressed
        if (e.key == "F5") {
            window.location.reload();
            return;
        }

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
                codeOut = "\r";
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
ws = new WebSocket(`wss://${server}/websocket`);

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

    //This text is shown, when the websocket connection is successful to the server
    terminalColor.innerHTML = `Websocket connection successful! Please provide ssh credentials to continue.
<span class="color-fg-green">
============================================================================
============================================================================
     ______                                                       __     
    /      \\                                                     |  \\    
   |  $$$$$$\\  ______   _______   _______    ______    _______  _| $$_   
   | $$   \\$$ /      \\ |       \\ |       \\  /      \\  /       \\|   $$ \\  
   | $$      |  $$$$$$\\| $$$$$$$\\| $$$$$$$\\|  $$$$$$\\|  $$$$$$$ \\$$$$$$  
   | $$   __ | $$  | $$| $$  | $$| $$  | $$| $$    $$| $$        | $$ __ 
   | $$__/  \\| $$__/ $$| $$  | $$| $$  | $$| $$$$$$$$| $$_____   | $$|  \\
    \\$$    $$ \\$$    $$| $$  | $$| $$  | $$ \\$$     \\ \\$$     \\   \\$$  $$
     \\$$$$$$   \\$$$$$$  \\$$   \\$$ \\$$   \\$$  \\$$$$$$$  \\$$$$$$$    \\$$$$

===========================================================================
===========================================================================
</span>                                                 

<span class="color-fg-yellow">┏┫Warning┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓</span>
<span class="color-fg-yellow">┃</span> <span class="effect-bold">This page uses a non-encrypted channel!</span>                      <span class="color-fg-yellow">┃</span>
<span class="color-fg-yellow">┃</span> This means that EVERY data you send or receive is travelling <span class="color-fg-yellow">┃</span>
<span class="color-fg-yellow">┃</span> in plain text. Even your passwords, and ip addresses.        <span class="color-fg-yellow">┃</span>
<span class="color-fg-yellow">┃</span> Be careful, while using this page!                           <span class="color-fg-yellow">┃</span>
<span class="color-fg-yellow">┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛</span>

<span class="color-fg-cyan">┏┫Note┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓</span>
<span class="color-fg-cyan">┃</span> Once the ssh connection is made, every keypress is captured.             <span class="color-fg-cyan">┃</span>
<span class="color-fg-cyan">┃</span> This means if you press for example Ctrl + F to search the page,         <span class="color-fg-cyan">┃</span>
<span class="color-fg-cyan">┃</span> nothing will happen, instead, the terminal gets the keypress information.<span class="color-fg-cyan">┃</span>
<span class="color-fg-cyan">┃</span> Because of this, page reloading is not possible trough F5,               <span class="color-fg-cyan">┃</span>
<span class="color-fg-cyan">┃</span> so to reload the page press Ctrl + F5                                    <span class="color-fg-cyan">┃</span>
<span class="color-fg-cyan">┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛</span>

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

    //Try reopening the connection
    ws = new WebSocket(`wss://${server}/websocket`);
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
                sessionStorage.setItem("terminal", data.terminal);

                errorMessage.textContent = "";
                connectMenu.classList.remove("open");
                connectMenu.classList.add("close");

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
                //console.log("SSH message", data.message);

                switch (data.message.type) {
                    // New text content
                    case "html":
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
