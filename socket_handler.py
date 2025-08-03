#!/usr/bin/env python

#Tornado
import tornado.websocket
import json
import string

from random import randint
from time import time, sleep

from color import Color
from ssh_manager import SSHManager

idLength = 10

#Handles the websocket requests
class SocketHandler(tornado.websocket.WebSocketHandler):
    clients = []
    maxClients = 2 # NOTE: Each client requires a new thread 

    logMode = "on"

    """
    Player handling methods
    """

    def getID() -> str:
        characters = string.ascii_letters + string.digits
        returnVal = ""
        for _ in range(0, idLength):
            returnVal += characters[randint(0, len(characters)-1)]

        return returnVal

    def getUID() -> str:
        """Get a unique id, consisting of lower and upprcase english letters + numbers from 0 to 9. The length is determined by the 'idLength' variable"""
        newId = SocketHandler.getID()
        while newId in SocketHandler.clients:
            newId = SocketHandler.getID()

        return newId

    # Sets the game data by socket
    def setUserData(socket, data):
        match = list( filter(lambda a : a[1]["socket"] == socket, enumerate(SocketHandler.clients)) )
        if len(match) == 0: return
        else:
            index = match[0][0]
            SocketHandler.clients[index]["data"] = data

    #Gets the game data by socket
    def getUserData(socket):
        match = list( filter(lambda a : a["socket"] == socket, SocketHandler.clients) )
        if len(match) == 0: return None
        else: return match[0]["data"]

    #Gets the game data by id
    def getUserDataByID(id):
        match = list( filter(lambda a : a["data"]["id"] == id, SocketHandler.clients) )
        if len(match) == 0: return None
        else: return match[0]["data"]

    def removeUser(socket):
        return list( filter(lambda a : a["socket"] != socket, SocketHandler.clients) )

    """
    Server methods
    """

    # Closesd all terminals and disconnects all users from the server
    def fullStop():
        for client in SocketHandler.clients:
            if "data" in client and "term" in client["data"]:
                client["data"]["term"].stop()

            client["socket"].close(reason = f"Server was shut down!")

            SocketHandler.removeUser(client["socket"])


    """
    SSH Manager response functions
    """

    # SSH Connector output
    def sshMessage(socket, type, message):
        socket.write_message({"type": "ssh_message", "category": type, "message": message})

    def sshError(socket, message):
        socket.close(reason = f"SSH Error: {message}")

    # Sets a user's data from the ssh manager
    def sshSetting(socket, param, value):
        userData = SocketHandler.getUserData(socket)
        userData[param] = value

    """
    Socket handling methods
    """

    def check_origin(self, origin) -> bool:
        return True

    def open(self):
        if len(SocketHandler.clients) >= SocketHandler.maxClients:
            if SocketHandler.logMode != "off": #on / reduced
                print(f"\r{Color.paint(f'Maximum number of clients reached! ({SocketHandler.maxClients})', Color.red)}")

            #raise tornado.web.HTTPError(403, "Connection refused.")
            self.close(reason = "Maximum number of clients reached")
            return
    
        newId = SocketHandler.getUID()

        # Add user to clients list, send them their ID
        SocketHandler.clients.append({
            "socket": self,
            "data": {
                "id": newId,
                "has_ssh": False
            }
        })

        if SocketHandler.logMode != "off": #on / reduced
            print(f"\r{Color.paint(f'User joined', Color.aqua)} {Color.paint(f'({len(SocketHandler.clients)}/{SocketHandler.maxClients})', Color.gray)}")


    def on_message(self, message):
        msg = None

        try:
            msg = json.loads(message)
        except:
            return

        if not "type" in msg: return

        # Somebody executed a command or pressed a key
        if msg["type"] == "control":
            userData = SocketHandler.getUserDataByID(msg["id"])
            if userData == None: return
            if userData["has_ssh"] == False: return

            if msg["mode"] == "command":
                userData["term"].send_command(msg["value"])
                return

            if msg["mode"] == "key":
                userData["term"].send_raw(msg['value'])

            return

        if msg["type"] == "connect":
            # Validate input
            if (not "address" in msg) or msg["address"] == "":
                self.write_message({"type": "validate", "state": "fail", "reason": "Address cannot be empty!"})
                return

            if (not "port" in msg) or msg["port"] == "":
                self.write_message({"type": "validate", "state": "fail", "reason": "Port cannot be empty!"})
                return

            if len(msg["port"]) > 5:
                self.write_message({"type": "validate", "state": "fail", "reason": "Invalid port!"})
                return

            numericPort = 0
            try:
                numericPort = int(msg["port"])
            except:
                self.write_message({"type": "validate", "state": "fail", "reason": "Invalid port!"})
                return

            if (not "username" in msg) or msg["username"] == "":
                self.write_message({"type": "validate", "state": "fail", "reason": "Username cannot be empty!"})
                return

            if (not "password" in msg) or msg["password"] == "":
                self.write_message({"type": "validate", "state": "fail", "reason": "Password cannot be empty!"})
                return

            # Get user ID
            userID = SocketHandler.getUserData(self)["id"]

            if SocketHandler.logMode == "on":
                print(f"\rUser '{Color.paint(msg['username'], Color.aqua)}' ({Color.paint(userID, Color.gray)}) connecting to '{Color.paint(msg['address'], Color.gray)}'")

            # Create terminal
            userTerm = SSHManager(SocketHandler, self, msg["address"], numericPort, msg["username"], msg["password"])
            userTerm.begin()

            # Let the client know, it registered successfully, and send them their ID
            self.write_message({
                "type": "validate",
                "state": "pass",
                "id": userID,
                "address": msg["address"],
                "port": numericPort,
                "username": msg["username"],
            })

            SocketHandler.setUserData(self, {
                "id": userID, # Keep the user id
                "login_time": time(),
                "has_ssh": False,
                "term": userTerm,
                "address": msg["address"],
                "port": numericPort,
                "username": msg["username"],
                "password": msg["password"]
            })

            return

    def on_close(self):
        leavingUserData = SocketHandler.getUserData(self)

        if "term" in leavingUserData:
            leavingUserData["term"].stop() # Close ssh terminal and exit the thread

        if leavingUserData != None and "id" in leavingUserData and "username" in leavingUserData and "address" in leavingUserData:
            if SocketHandler.logMode != "off": #on / reduced
                print(f"\rUser '{Color.paint(leavingUserData['username'], Color.aqua)}' ({Color.paint(leavingUserData['id'], Color.gray)}) disconnected {Color.paint(f'({len(SocketHandler.clients)}/{SocketHandler.maxClients})', Color.gray)}")

        elif SocketHandler.logMode != "off":
            print(f"\r{Color.paint(f'User left', Color.aqua)}")

        SocketHandler.clients = SocketHandler.removeUser(self)