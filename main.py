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

input_queue.put("ls\n")

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
            channel.send(command + '\n')
    
        if channel.recv_ready():
            output = channel.recv(1022)
            if output:
                output_queue.put(output)
                time.sleep(0.1)

def main():
    # Create a ConfigParser object
    config = configparser.ConfigParser()

    config.read('ssh_data.ini')
    host = config['DEFAULT']['host']
    username = config['DEFAULT']['username']
    password = config['DEFAULT']['password']


    # Start ssh clinet on a new thread
    ssh_thread = threading.Thread(target=ssh_main, args=(host, username, password)).start()

    fout = open("outout.txt", "bw")

    try:
        while True:
            #command = input("Enter command to execute (or 'exit' to close): ")
            #if command == "" or command.lower() == 'exit':
            #    break

            #input_queue.put(command)

            while not output_queue.empty():
                data = output_queue.get()
                fout.write(data)
                print(data)
                
                escape = ""

                for b in data:
                    if escape == "":
                        if b == 0x1b:
                            escape = ""
                            continue
                    else:

                        print("||")#ANSI Escape

                    if b < 10: pass
                    if b == 10: print()
                    if b > 10 and b < 32: pass
                    if b >= 32 and b <= 126: print(chr(b), end="")
                    if b > 126: pass

            fout.flush()
    except KeyboardInterrupt:
        print("\nExited")
        pass

    fout.close()

    stop_event.set()
    time.sleep(0.1)
    ssh_thread.join()


# Run the main function using asyncio
if __name__ == '__main__':
    asyncio.run(main())
