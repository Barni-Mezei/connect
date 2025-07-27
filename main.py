import asyncio
import configparser
import paramiko # type: ignore
import threading
import queue
import time

output_queue = queue.Queue()
input_queue = queue.Queue()
stop_event = threading.Event()
ssh_thread = None

input_queue.put("ls")

def ssh_main(host, username, password):
    print(f"Connecting to '{host}' as '{username}' with password '{password}'")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, username = username, password = password)
    except Exception as e:
        print("SSH error:", e)
        return

    # Open a session
    channel = client.invoke_shell(term="tty", width=80, height=25, width_pixels=800, height_pixels=250)
    
    while not stop_event.is_set():
        if not input_queue.empty():
            command = input_queue.get()
            if len(command) == 0 or not command[-1] == "\n": command += "\n"

            channel.send(command)
    
        if channel.recv_ready():
            output = channel.recv(1022)
            if output:
                output_queue.put(output)
                time.sleep(0.01)

            #Print the output
            while not output_queue.empty():
                data = output_queue.get()
                #fout.write(data)
                #print(data)
                
                parsed_text = processDataChunk(data)

            if len(parsed_text) > 0:
               printParsedText(parsed_text)


def decodeANSI(ansi):
    #print(f"ANSI: {repr(ansi)}")
    if len(ansi) <= 2: return "\033[m"

    values = ansi[1:-1].split(";")

    return f"\033[{';'.join(values)}m"


def processDataChunk(data):
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

def printParsedText(parsed_text):
    for l in parsed_text:
        if l["type"] == "ansi":
            l["value"] = decodeANSI(l["value"])

        print(l["value"], end="")

def main():
    # Create a ConfigParser object
    config = configparser.ConfigParser()

    config.read('ssh_data.ini')
    host = config['DEFAULT']['host']
    username = config['DEFAULT']['username']
    password = config['DEFAULT']['password']


    # Start ssh clinet on a new thread
    ssh_thread = threading.Thread(target=ssh_main, args=(host, username, password))
    ssh_thread.start()

    fout = open("outout.txt", "bw")

    try:
        while True:
            command = input()
            if command.lower() == 'exit':
                break

            input_queue.put(command)

            fout.flush()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt. Exiting")
        pass

    fout.close()

    stop_event.set()
    ssh_thread.join()

if __name__ == "__main__":
    main()
