import tornado
import paramiko # type: ignore
import threading
import queue
import time

from color import Color

class SSHError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class SSHManager:
    thread = None
    host = ""
    port = 22
    username = ""
    password = ""
    terminal = "tty"

    output_queue = queue.Queue()
    input_queue = queue.Queue()
    stop_event = threading.Event()
    ssh_thread = None

    socket_handler = None
    websocket = None

    def __init__(self, socket_handler, websocket, host, port, username, password, terminal = "tty"):
        self.socket_handler = socket_handler
        self.websocket = websocket

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.terminal = terminal

        self.stop_event = threading.Event()

    # Starts a new thread, and an SSh connection
    def begin(self):
        self.ssh_thread = threading.Thread(target = self.ssh_main)
        self.ssh_thread.start()

    # Stops the thread, and the ssh connection
    def stop(self):
        print(f"SSH: Closing connection to {self.username}@{self.host}:{self.port}")

        self.stop_event.set()
        self.ssh_thread.join()

    # Sends a command to the connected ssh
    def send_command(self, command):
        print(f"SSH: Command received on {self.username}@{self.host}:{self.port} $ {Color.paint(f'{command}', Color.aqua)}")

        self.input_queue.put({"type": "command", "value": command})

    # Sends raw data to the connected ssh
    def send_raw(self, data):
        char = "Control" if ord(data) < 32 else "Alt"
        char += " + "
        char += chr(ord(data) + 96).upper() if ord(data) < 32 else data

        print(f"SSH: Raw received on {self.username}@{self.host}:{self.port} {Color.paint(f'{repr(data)} ({char})', Color.aqua)} ")

        self.input_queue.put({"type": "data", "value": data})

    # Establishes a new ssh connection, and listens to it
    def ssh_main(self):
        print(f"SSH: Connecting to {self.username}@{self.host}:{self.port}")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Get event loop from socket handler, to enable message sending
        loop = tornado.ioloop.IOLoop.current()
        loop.make_current()

        try:
            client.connect(self.host, self.port, self.username, self.password)
        except Exception as e:
            self.socket_handler.sshError(self.websocket, str(e))
            #raise SSHError(f"Connection to {self.host} failed, reason: {e}")
            return

        # Open a new terminal
        shell = client.invoke_shell(term = self.terminal, width = 80, height = 25, width_pixels = 100, height_pixels = 250)
        shell.set_combine_stderr(True)

        self.socket_handler.sshMessage(self.websocket, "info", "SSH Connection successful!")
        self.socket_handler.sshSetting(self.websocket, "has_ssh", True)

        self.input_queue.put({"type": "command", "value": "ls -lha"})

        while not self.stop_event.is_set():
            if not self.input_queue.empty():
                entry = self.input_queue.get()

                if entry["type"] == "command":
                    if len(entry["value"]) == 0 or not entry["value"][-1] == "\n":
                        entry["value"] += "\n"

                shell.send(entry["value"])

            if shell.recv_ready():
                output = shell.recv(1024)
                #if output:
                #    self.output_queue.put(output)

                #Print the output
                #while not self.output_queue.empty():
                #    data = self.output_queue.get()
                    #fout.write(data)
                    #print(data)

                # Parse output
                parsed_text = self.processDataChunk(output)

                # Output a formatted HTML
                if len(parsed_text) > 0:
                    outputHtml = self.htmlFromParsedText(parsed_text)
                    self.socket_handler.sshMessage(self.websocket, "data", outputHtml)
                    #time.sleep(0.01)


    def getHtmlChunk(self):
        if self.output_queue.empty(): return ""

        return self.output_queue.get()

    def processDataChunk(self, data):
        parsed_text = []

        escape = None
        text = ""

        for b in data:
            if escape == None:
                if b == 0x1b:
                    escape = ""
                    parsed_text.append({"type": "text", "value": text})
                    text = ""
                    continue


            else:
                escape += chr(b)
                if b == 0x6d:
                    parsed_text.append({"type": "ansi", "value": escape})
                    escape = None
                    continue

            if escape == None:
                #if b == 32: # Show spaces
                #    text += "\033[90m·\033[m"
                #    continue
                
                #if b == 10: # Show new lines
                #    text += "\033[32m >|\033[m\n"
                #    continue

                if b < 10: continue
                if b > 126: continue
                text += chr(b)


        if not text == "":
            parsed_text.append({"type": "text", "value": text})

        return parsed_text

    # Decodes an ansi escape equence from characters into a real one
    def decodeANSIChars(self, ansi):
        if len(ansi) <= 2: return "\033[m"

        values = ansi[1:-1].split(";")

        return f"\033[{';'.join(values)}m"

    # Decodes an ansi escape equence into it's base components
    def decodeANSI(self, ansi):
        #print("ANSI", repr(ansi))

        if len(ansi) <= 2: return [0]

        values = [int(n) for n in ansi[1:-1].split(";")]

        return values

    def getColorByIndex(self, colorIndex, background = False, bright = False):
        if colorIndex == -1: return "black" if background else "bright-white"

        colors = [
            "black",
            "red",
            "green",
            "yellow",
            "blue",
            "magenta",
            "cyan",
            "white",
        ]

        return ("bright-" if bright else "") + colors[colorIndex]

    def setFlags(self, oldFlags : dict, newFlags : list):
        default = {
            "intensity": "normal",
            "blink": "off",
            "effect": {
                "italic": False,
                "underline": False,
                "striketrough": False,
                "reverse": False,
            },

            "color": {
                "fg": "bright-white",
                "bg": "black",
            }
        }

        if oldFlags == {}:
            out = default
        else:
            out = oldFlags

        for f in newFlags:
            match f:
                case 0: out = default # Reset everything
                case 1: out["intensity"] = "bold"
                case 2: out["intensity"] = "light"
                case 3: out["effect"]["italic"] = True
                case 4: out["effect"]["underline"] = True
                case 5: out["blink"] = "slow"
                case 6: out["blink"] = "rapid"
                case 7: out["effect"]["reverse"] = True
                case 8: pass # Conceal
                case 9: out["effect"]["striketrough"] = True
                case n if 10 <= n <= 21: pass
                case 22: out["intensity"] = "normal"
                case 23: out["effect"]["italic"] = False
                case 24: out["effect"]["underline"] = False
                case 25: out["blink"] = "off"
                case 26: pass 
                case 27: out["effect"]["reverse"] = False
                case 28: pass # Conceal off
                case 29: out["effect"]["striketrough"] = False
                case n if 30 <= n <= 37: out["color"]["fg"] = self.getColorByIndex(n - 30, background = False)
                case 38: pass
                case 39: out["color"]["fg"] = self.getColorByIndex(-1)
                case n if 40 <= n <= 47: out["color"]["bg"] = self.getColorByIndex(n - 40, background = True)
                case 48: pass
                case 49: out["color"]["bg"] = self.getColorByIndex(-1)
                case n if 50 <= n <= 89: pass 
                case n if 90 <= n <= 97: out["color"]["fg"] = self.getColorByIndex(n - 90, background = False, bright = True)
                case n if 98 <= n <= 99: pass 
                case n if 100 <= n <= 107: out["color"]["bg"] = self.getColorByIndex(n - 100, background = True, bright = True)
                case n if 108 <= n <= 127: pass 

                case _: pass

        return out

    # Creates a HTML span from the difference of the 2 ansi escape values (from 2, 3, 4 to 3, 5 it will be </span><span class="">)
    def createSpanFromAnsi(self, ansiFlags, isFirstSpan):
        classes = [
            "color-fg-" + ansiFlags["color"]["fg"],
            "color-bg-" + ansiFlags["color"]["bg"]
        ]

        match ansiFlags["blink"]:
            case "off": pass
            case "slow": classes.append("effect-slow-blink")
            case "rapid": classes.append("effect-fast-blink")

        match ansiFlags["intensity"]:
            case "normal": pass
            case "bold": classes.append("effect-bold")
            case "light": classes.append("effect-dim")

        if ansiFlags["effect"]["italic"]: classes.append("effect-italic")
        if ansiFlags["effect"]["underline"]: classes.append("effect-underline")
        if ansiFlags["effect"]["striketrough"]: classes.append("effect-striketrough")
        if ansiFlags["effect"]["reverse"]: classes.append("effect-reverse")

        return ("" if isFirstSpan else "</span>") + f"<span class=\"{' '.join(classes)}\">"

    def htmlFromParsedText(self, parsed_text):
        out = ""#"<span class=\"start\">"
        ansi_flags = {}
        first_span = True

        for l in parsed_text:
            if l["type"] == "ansi":
                ansi_flags = self.setFlags(ansi_flags, self.decodeANSI(l["value"]))

                out += self.createSpanFromAnsi(ansi_flags, first_span)
                first_span = False

                continue

            out += l["value"]
        
        out += "</span>"

        return out