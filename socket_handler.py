#!/usr/bin/env python

#Tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi
import tornado.websocket
import json
import string

from random import randint
from time import time, sleep

#Import other files
from color import Color

idLength = 10

#Handles the websocket requests
class SocketHandler(tornado.websocket.WebSocketHandler):
    clients = []

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
    Socket handling methods
    """

    def check_origin(self, origin) -> bool:
        return True

    def open(self):
        newId = SocketHandler.getUID()

        # Add user to clients list, send them their ID
        SocketHandler.clients.append({
            "socket": self,
            "data": {
                "id": newId,
            }
        })

        if SocketHandler.logMode != "off": #on / reduced
            print(f"\r{Color.paint(f'User joined', Color.aqua)}")


    def on_message(self, message):
        msg = json.loads(message)

        if not "type" in msg: return

        # Somebody executed a command
        if msg["type"] == "command":
            if SocketHandler.getUserDataByID(msg["id"]) == None: return

            # TODO terminal
            return

        if msg["type"] == "connect":
            # Initialise user data
            clientId = SocketHandler.getUserData(self)["id"]

            # Validate input
            if msg["address"] == "":
                self.write_message({"event": "validate", "state": "fail", "reason": "Address cannot be empty!"})
                return

            if msg["port"] == "":
                self.write_message({"event": "validate", "state": "fail", "reason": "Port cannot be empty!"})
                return

            if len(msg["port"]) > 5:
                self.write_message({"event": "validate", "state": "fail", "reason": "Invalid port!"})
                return

            numericPort = 0
            try:
                numericPort = int(msg["port"])
            except:
                self.write_message({"event": "validate", "state": "fail", "reason": "Invalid port!"})
                return

            if msg["username"] == "":
                self.write_message({"event": "validate", "state": "fail", "reason": "Username cannot be empty!"})
                return

            if msg["password"] == "":
                self.write_message({"event": "validate", "state": "fail", "reason": "Password cannot be empty!"})
                return

            SocketHandler.setUserData(self, {"id": clientId, "address": msg["address"], "port": numericPort, "username": msg["username"], "password": msg["password"]})

            if SocketHandler.logMode == "on":
                print(f"\rUser '{Color.paint(msg['name'], Color.aqua)}' connected to '{Color.paint(msg['address'], Color.gray)}'")

            return # Do not brodcast this

        ######################################################################
        # Add timestamp & broadcast message to all clients (except for self) #
        ######################################################################
        #msg["time"] = time()
        for c in SocketHandler.clients:
            if msg["event"] != "death" and c["socket"] == self: continue
            try: c["socket"].write_message(msg)
            except: pass


    def on_close(self):
        leavingUserData = SocketHandler.getUserData(self)

        if leavingUserData != None and "id" in leavingUserData and "username" in leavingUserData and "address" in leavingUserData:
            if SocketHandler.logMode != "off": #on / reduced
                print(f"\r{Color.paint(leavingUserData['username'], Color.aqua)} \
({Color.paint(leavingUserData['id'], Color.gray)}) \
disconnected from {Color.paint(leavingUserData['addres'], Color.gray)}")

        SocketHandler.clients = SocketHandler.removeUser(self)