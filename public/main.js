let errorMessage = document.getElementById("error_message");
let connnectButton = document.getElementById("connect");
let terminalText = document.getElementById("terminal_text");
let terminalColor = document.getElementById("terminal_color");
let colorTheme = document.getElementById("color_theme");

function setColorTheme(fileName = "ubuntu") {
    colorTheme.href = `public/colors/${fileName}.css`
}

//Start by disabling editing on the page, until the connection is made
terminalColor.contentEditable = false;
terminalText.contentEditable = false;

//Create websocket
const server = window.location.host;
ws = new WebSocket(`ws://${server}/websocket`);

ws.onopen = function (message) {
    console.log("Socket opened!", message);

    terminalColor.innerHTML = `Connected to the server! Please provide ssh credentials to continue. <span class="color-fg-yellow">WARNING: This is NOT an encrytpted channel!<span>`;
    terminalText.value = "";
};

connnectButton.onclick = function () {

}

