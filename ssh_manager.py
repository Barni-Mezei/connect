import tornado
import paramiko # type: ignore
import threading
import queue
import time
import re
import traceback

from color import Color

class SSHError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class SSHManager:
    thread = None
    socket_handler = None
    websocket = None

    output_queue = queue.Queue()
    input_queue = queue.Queue()
    stop_event = threading.Event()

    host = ""
    port = 22
    username = ""
    password = ""
    terminal = "vt100"
    chunk_size = 1024

    # 0: No logs at all
    # 1: Only connection specific logging
    # 2: Basic debug
    # 3: Advanced debug
    log_level = 1 

    ssh_thread = None
    
    def __init__(self, socket_handler, websocket, host, port, username, password, terminal = "vt100", chunk_size = 1024):
        self.socket_handler = socket_handler
        self.websocket = websocket

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.terminal = terminal
        self.chunk_size = chunk_size

        self.stop_event = threading.Event()

    # Starts a new thread, and an SSh connection
    def begin(self):
        self.ssh_thread = threading.Thread(target = self.ssh_main)
        self.ssh_thread.start()

    # Stops the thread, and the ssh connection
    def stop(self):
        if self.log_level > 0: print(f"SSH: Closing connection to {self.username}@{self.host}:{self.port} ({self.terminal})")

        self.stop_event.set()
        self.ssh_thread.join()

    # Sends a command to the connected ssh
    def send_command(self, command):
        if self.log_level > 1: print(f"SSH: Command received on {self.username}@{self.host}:{self.port} $ {Color.paint(f'{command}', Color.aqua)}")

        self.input_queue.put({"type": "command", "value": command})

    # Sends raw data to the connected ssh
    def send_raw(self, data):
        #char = "-"

        #try:
        #    char = "Control" if ord(data) < 32 else "Alt"
        #    char += " + "
        #    char += chr(ord(data) + 96).upper() if ord(data) < 32 else data
        #except: pass

        #print(f"SSH: Raw received on {self.username}@{self.host}:{self.port} {Color.paint(f'{repr(data)} ({char})', Color.aqua)} ")

        self.input_queue.put({"type": "data", "value": data})

    # Establishes a new ssh connection, and listens to it
    def ssh_main(self):
        if self.log_level > 0: print(f"SSH: Connecting to {self.username}@{self.host}:{self.port} ({self.terminal})")

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
                output = shell.recv(self.chunk_size)

                # Parse output
                try:
                    parsed_text = self.processDataChunk(output)
                except Exception as e:
                    if self.log_level > 0: print(f"{Color.paint(f'SSH ERROR [{self.username}@{self.host}:{self.port} ({self.terminal})]:\n{traceback.format_exc()}', Color.red)}")
                    self.socket_handler.sshMessage(self.websocket, "error", str(e))
                    return

                # Output a formatted HTML
                if len(parsed_text) > 0:
                    try:
                        for outputHtml in self.htmlFromParsedText(parsed_text):
                            self.socket_handler.sshMessage(self.websocket, "data", outputHtml)
                        #time.sleep(0.1)
                    except Exception as e:
                        if self.log_level > 0: print(f"{Color.paint(f'SSH ERROR [{self.username}@{self.host}:{self.port} ({self.terminal})]:\n{traceback.format_exc()}', Color.red)}")
                        self.socket_handler.sshMessage(self.websocket, "error", str(e))
                        return

    def processDataChunk(self, data):
        data = data + b"\0\0\0\0\0\0\0\0" # Account for stripped control characters (if they are chopped in half)

        if self.log_level > 2: print("Data", repr(data))

        parsed_text = []

        escape = None
        escape_mode = ""
        text = ""

        for i, b in enumerate(data):
            if escape == None:
                if b == 0x1b: # Escape sequences (like color changing and cursor manipulation)
                    escape = ""
                    escape_mode = data[i + 1]
                    parsed_text.append({"type": "text", "value": text})
                    text = ""

                    if escape_mode == ord("("): # Assign charset
                        parsed_text.append({"type": "ansi", "mode": escape_mode, "value": chr(data[i +2])})
                        escape = None

                    if escape_mode == ord(")"): # Invoke charset
                        charset_id = ""

                        for j in range(2):
                            if chr(data[i + j + 2]).isdigit():
                                charset_id += chr(data[i + j + 2])

                        parsed_text.append({"type": "ansi", "mode": escape_mode, "value": int(charset_id)})
                        escape = None

                    if escape_mode in [ord("="), ord(">")]: # Application keypad mode (on / off)
                        parsed_text.append({"type": "ansi", "mode": escape_mode, "value": ""})
                        escape = None

                    continue

                if b == 0x0f: # (shift in) Charset to G0
                    continue

                if b == 0x0e: # (shift out) Charset to G1
                    continue
            else:
                escape += chr(b)
                # Regular ansi escape sequences can be closed with the following characters (basically all non-number characters)
                if chr(b).lower().isalpha():
                    """ in [
                    ord("m"), # Change color
                    ord("h"),
                    ord("l"),
                    ord("r"),
                    ord("f"), # Same as H
                    ord("A"), # Move cursor UP 
                    ord("B"), # MOve cursor DOWN
                    ord("C"), # Move cursor RIGHT
                    ord("D"), # Move cursor LEFT
                    ord("H"), # Move cursor HOME
                    ord("J"), # Move cursor to pos
                    ord("K"),
                    ord("]")
                ]"""
                    parsed_text.append({"type": "ansi", "mode": escape_mode, "value": escape})
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

    def parseOptionalXYParams(self, full_ansi, ansi_core):
        x = 1
        y = 1

        if ansi_core != "":
            if ";" in ansi_core: # Could be [x;yr OR [;yr
                x, y = [int(1 if n == "" else n) for n in full_ansi[1:-1].split(";")]
            else: # Could be [xr
                return int(ansi_core), 1
        
        return x, y

    def _decodeANSI_91(self, ansi):
        ansi_type = ansi[-1]
        core = ansi[1:-1]
        first_char = core[0] if len(core) > 0 else "0"

        if self.log_level > 1: print("ANSI", repr(ansi), "Core", repr(core), "End", repr(ansi_type), "First char", repr(first_char), end=" | ")

        match ansi_type:
            case "m":
                # Graphics manipulation
                if core == "":
                    return {"type": "graphics", "value": [0]}
                else:
                    return {"type": "graphics", "value": [int(n) for n in ansi[1:-1].split(";")]}

            case "h":
                # Device control enable
                return {"type": "dc_enable", "value": int(core[1::])}

            case "l":
                # Device control disable
                return {"type": "dc_disable", "value": int(core[1::])}

            case "r":
                # Set scroll region
                x, y = self.parseOptionalXYParams(ansi, core)
                
                return {"type": "cursor", "x": x, "y": y}

            case "J":
                # Clear screen from cursor, to cursor, all
                return {"type": "screen", "value": int(first_char)}

            case "K":
                # Clear line from cursor, to cursor, all
                return {"type": "line", "value": int(first_char)}

            case "H":
                # Set cursor position
                x, y = self.parseOptionalXYParams(ansi, core)
                
                return {"type": "cursor", "x": x, "y": y}

            case "]":
                # Operating system commands
                return {"type": "os", "value": core}

            case _: pass

        return {"type": "unknown", "value": None}

    def _decodeANSI_40(self, ansi):
        if self.log_level > 1: print("ANSI", repr(ansi), end=" | ")

        return {"type": "set_charset", "value": ord(ansi)}


    def _decodeANSI_41(self, ansi):
        if self.log_level > 1: print("ANSI", repr(ansi), end=" | ")

        return {"type": "invoke_charset", "value": int(ansi)}

    def _decodeANSI_61(self, ansi):
        if self.log_level > 1: print("ANSI", repr(ansi), end=" | ")

        return {"type": "keypad_mode", "value": True}

    def _decodeANSI_62(self, ansi):
        if self.log_level > 1: print("ANSI", repr(ansi), end=" | ")

        return {"type": "keypad_mode", "value": False}

    # Decodes an ansi escape equence into it's base components (returns a list or a string, if it is a special sequence, like clear)
    def decodeANSI(self, ansi, mode):
        if mode == ord("["): return self._decodeANSI_91(ansi)
        if mode == ord("("): return self._decodeANSI_40(ansi)
        if mode == ord(")"): return self._decodeANSI_41(ansi)
        if mode == ord("="): return self._decodeANSI_61(ansi)
        if mode == ord(">"): return self._decodeANSI_62(ansi)


    # Returnsd with the name of the class, with the color, corresponding with the ansi color code
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

    # Creates a dictionary, from the ansi escape codes
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
        out = ""
        ansi_flags = {}
        first_span = True

        for l in parsed_text:
            if l["type"] == "ansi":
                decoded_ansi = self.decodeANSI(l["value"], l["mode"])

                if self.log_level > 2: print(decoded_ansi)

                match decoded_ansi["type"]:
                    case "unknown": pass

                    # Screen control (like clearing)
                    case "screen":
                        out = ""
                        first_span = True

                        # Send a control message to the page, to clear the screen
                        yield {"type": "control", "value": "clear", "mode": decoded_ansi["value"]}

                    # Moves the cursor to the top left of the screen
                    case "cursor":
                        out = ""
                        first_span = True

                        # Send a control message to the page, to clear the screen
                        yield {"type": "control", "value": "cursor", "x": decoded_ansi["x"], "y": decoded_ansi["y"]}

                    # Color and text style manipulation
                    case "graphics":
                        ansi_flags = self.setFlags(ansi_flags, decoded_ansi["value"])

                        out += self.createSpanFromAnsi(ansi_flags, first_span)
                        first_span = False

                    case _: pass
            
                continue

            out += l["value"]

        # Close span if there is any
        if not first_span: out += "</span>"

        yield {"type": "html", "value": out}