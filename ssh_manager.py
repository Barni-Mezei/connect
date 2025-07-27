import paramiko # type: ignore
import threading
import queue
import time

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

    def __init__(self, host, port, username, password, terminal = "tty"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.terminal = terminal

    # Starts a new thread, and an SSh connection
    def create(self):
        self.ssh_thread = threading.Thread(target = self.ssh_main)
        self.ssh_thread.start()

    # Stops the thread, and the ssh connection
    def stop(self):
        self.stop_event.set()
        self.ssh_thread.join()

    # Sends a command to the connected ssh
    def send_command(self, command):
        self.input_queue.put(command)


    # Establishes a new ssh connection, and listens to it
    def ssh_main(self):
        print(f"Connecting to {self.username}@{self.host}:{self.port} with password '{self.password}'")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client.connect(self.host, self.port, self.username, self.password)
        except Exception as e:
            raise SSHError(f"Connection to {self.host} failed, reason: {e}")

        # Open a new terminal
        channel = client.invoke_shell(term = self.terminal, width = 80, height = 25)
        
        while not self.stop_event.is_set():
            if not self.input_queue.empty():
                command = self.input_queue.get()
                if len(command) == 0 or not command[-1] == "\n": command += "\n"

                channel.send(command)
        
            if channel.recv_ready():
                output = channel.recv(1022)
                if output:
                    self.output_queue.put(output)
                    time.sleep(0.01)

                #Print the output
                while not self.output_queue.empty():
                    data = self.output_queue.get()
                    #fout.write(data)
                    #print(data)
                    
                    parsed_text = self.processDataChunk(data)

                if len(parsed_text) > 0:
                    self.printParsedText(parsed_text)

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
                    # print(f"|{escape}|")# ANSI Escape
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
        #print(f"ANSI: {repr(ansi)}")
        if len(ansi) <= 2: return "\033[m"

        values = ansi[1:-1].split(";")

        return f"\033[{';'.join(values)}m"

    # Decodes an ansi escape equence into it's base components
    def decodeANSI(self, ansi):
        if len(ansi) <= 2: return "reset"

        values = ansi[1:-1].split(";")

        return values

    # Creates a HTML span from the difference of the 2 ansi escape values (from 2, 3, 4 to 3, 5 it will be </span><span class="">)
    def createSpanFromDiff(self, oldAnsi, newAnsi):
        pass

    def printParsedText(self, parsed_text):
        ansi_values = {}

        for l in parsed_text:
            if l["type"] == "ansi":
                l["value"] = self.decodeANSI(l["value"])

            print(l["value"], end="")
