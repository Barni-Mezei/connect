let errorMessage = document.getElementById("error_message");
let connnectButton = document.getElementById("connect_button");
let connnectMenu = document.getElementById("connect_menu");
let terminalText = document.getElementById("terminal_text");
let terminalColor = document.getElementById("terminal_color");
let colorTheme = document.getElementById("color_theme");
let contextMenu = document.getElementById("context_menu");



//Start by disabling editing on the page, until the connection is made
terminalColor.contentEditable = false;
terminalText.contentEditable = false;
terminalText.classList.add("disabled");

//Hide context menu
contextMenu.classList.add("hidden");

function changeTheme(fileName = "ubuntu") {
    colorTheme.href = `public/colors/${fileName}.css`
}

//********
//* MAIN *
//********

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

//Create websocket
const server = window.location.host;
ws = new WebSocket(`ws://${server}/websocket`);

//Show availability on open
ws.onopen = function (e) {
    console.log("Socket opened!", e);

    terminalColor.innerHTML = `Websocket connection successful! Please provide ssh credentials to continue.
<span class="color-fg-yellow">WARNING: This is NOT an encrypted channel!</span>

Color test:
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
<span class="color-fg-bright-white">FG</span> <span class="color-bg-bright-white">BG</span> \
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
    terminalText.contentEditable = false;
    terminalText.classList.add("disabled");
};



ws.onmessage = function (e) {
    console.log("Message received:", e);

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

                terminalColor.innerHTML = `Connecting to <span class="color-fg-bright-black">${data.username}@${data.address}</span>`;
                terminalText.value = "";
            }
            break;

        default:
            break;
    }
}
