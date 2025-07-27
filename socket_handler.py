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
from data import Level
from color import Color

idLength = 10

#Handles the websocket requests
class SocketHandler(tornado.websocket.WebSocketHandler):
    clients = []

    teamScores = {
        "red": 0,
        "blue": 0,
        "green": 0,
        "yellow": 0,
    }

    teamColors = {
        "red": Color.red,
        "blue": Color.blue,
        "green": Color.green,
        "yellow": Color.yellow,
    }

    logMode = "on"

    settings = {
        "frendlyFire": False,
    }

    """
    Settings manager    
    """

    def synchroniseSettings():
        for c in SocketHandler.clients:
            try: c["socket"].write_message({"event": "syncServer", "subEvent": "settings", "settings": SocketHandler.settings})
            except: pass


    """
    Getters
    """

    def getNumberOfClients():
        return len(SocketHandler.clients)

    def getPlayersInTeam(teamName : str) -> list:
        return list( filter(lambda c: c["gameData"]["team"] == teamName if "team" in c["gameData"] else False, SocketHandler.clients) )

    def getNumberOfPlayersInTeam(teamName : str) -> int:
        return len(SocketHandler.getPlayersInTeam(teamName))


    """
    Score managing methods
    """

    def getTeamName(teamName : str) -> str:
        if teamName in SocketHandler.teamScores and teamName in SocketHandler.teamColors:
            return Color.paint(teamName, SocketHandler.teamColors[teamName])
        else:
            return Color.paint("unknown", Color.gray)


    def getColoredName(name : str, teamName : str) -> str:
        """Colors a player's name to it's teams color"""
        if teamName in SocketHandler.teamScores and teamName in SocketHandler.teamColors:
            return Color.paint(name, SocketHandler.teamColors[teamName])
        else:
            return Color.paint(name, Color.gray)

    def logTeamScores():
        #Log the teams by sorted order
        for index, team in enumerate( sorted(SocketHandler.teamScores, key = lambda a : SocketHandler.teamScores[a], reverse = True) ):
            memberColor = Color.gray if SocketHandler.getNumberOfPlayersInTeam(team) == 0 else Color.aqua
            scoreColor = Color.gray if SocketHandler.teamScores[team] == 0 else Color.aqua
            print(f"{SocketHandler.getTeamName(team)}\tMembers: {Color.paint(SocketHandler.getNumberOfPlayersInTeam(team), memberColor)}\tScore: {Color.paint(SocketHandler.teamScores[team], scoreColor)}")


    def setTeamScore(teamName : str, value : int):
        if not teamName in SocketHandler.teamScores: raise KeyError(f"No team found with name: {teamName}")

        SocketHandler.teamScores[teamName] = value
    

    def resetTeamScore(teamName : str):
        if teamName == "all":
            for team in SocketHandler.teamScores:
                SocketHandler.teamScores[team] = 0
        else:
            SocketHandler.setTeamScore(teamName, 0)


    def addTeamScore(teamName : str, value : int):
        if not teamName in SocketHandler.teamScores: raise KeyError(f"No team found with name: {teamName}")

        SocketHandler.teamScores[teamName] += value


    def removeTeamScore(teamName : str, value : int):
        if not teamName in SocketHandler.teamScores: raise KeyError(f"No team found with name: {teamName}")

        SocketHandler.teamScores[teamName] -= value


    def getTeamsJSON() -> dict:
        """Returns a JSON containing all team data (name, score, number of members)"""
        out = SocketHandler.teamScores.copy()
        for team, score in out.items():
            out[team] = {
                "score": score,
                "members": SocketHandler.getNumberOfPlayersInTeam(team)
            }

        return out


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

    #Sets the game data by socket
    def setPlayerData(socket, data):
        match = list( filter(lambda a : a[1]["socket"] == socket, enumerate(SocketHandler.clients)) )
        if len(match) == 0: return
        else:
            index = match[0][0]
            SocketHandler.clients[index]["gameData"] = data

    #Update the game data by socket (updates only the given keys) retuns the matched clients
    def updatePlayerData(socket, data) -> int:
        match = list( filter(lambda a : a[1]["socket"] == socket, enumerate(SocketHandler.clients)) )
        if len(match) == 0: return 0
        else:
            index = match[0][0]
            for key in data:
                SocketHandler.clients[index]["gameData"][key] = data[key]
        return len(match)

    #Gets the game data by socket
    def getPlayerData(socket):
        match = list( filter(lambda a : a["socket"] == socket, SocketHandler.clients) )
        if len(match) == 0: return None
        else: return match[0]["gameData"]

    #Gets the game data by id
    def getPlayerDataByID(id):
        match = list( filter(lambda a : a["gameData"]["id"] == id, SocketHandler.clients) )
        if len(match) == 0: return None
        else: return match[0]["gameData"]

    #Gets the game data by short id (4 characters)
    def getPlayerDataByShortID(shortId):
        match = list( filter(lambda a : a["gameData"]["id"][:4] == shortId, SocketHandler.clients) )
        if len(match) == 0: return None
        else: return match[0]["gameData"]

    #Gets the FULL DATA socket by id
    def getClientDataByID(id):
        match = list( filter(lambda a : a["gameData"]["id"] == id, SocketHandler.clients) )
        if len(match) == 0: return None
        else: return match[0]

    #Gets the FULL DATA socket by short id (4 characters)
    def getClientDataByShortID(shortId):
        match = list( filter(lambda a : a["gameData"]["id"][:4] == shortId, SocketHandler.clients) )
        if len(match) == 0: return None
        else: return match[0]

    def removePlayer(socket):
        return list( filter(lambda a : a["socket"] != socket, SocketHandler.clients) )


    def getPlayersJSON():
        out = {}
        for c in list( map(lambda a : a["gameData"], SocketHandler.clients) ):
            out[c["id"]] = c
        return out


    """
    Game logic handlers
    """

    def restart_game():
        """Starts a new game, with the selected level"""

        SocketHandler.resetTeamScore("all")
        SocketHandler.synchroniseScore()

        #Send new level
        for c in SocketHandler.clients:
            try: c["socket"].write_message({"event": "syncServer", "subEvent": "level", "level": Level.getJSON()})
            except: pass

    def synchroniseScore():
        #Send new scores
        for c in SocketHandler.clients:
            try: c["socket"].write_message({"event": "syncServer", "subEvent": "score", "teams": SocketHandler.getTeamsJSON()})
            except: pass

    """
    Socket handling methods
    """
    def disconnectPlayerByShortID(shortId, reason = "Kicked by the server"):
        """Kicks a player, recognised by the short id"""
        playerData = SocketHandler.getClientDataByShortID(shortId)
        if playerData == None:
            print(f"{Color.paint(f'No player found with short id of: {shortId}', Color.red)}")
            return
        playerData["socket"].write_message({"event": "kick", "reason": reason})
        SocketHandler.clients = SocketHandler.removePlayer(playerData["socket"])
        print(f"{SocketHandler.getColoredName(playerData['gameData']['name'], playerData['gameData']['team'])} was kicked.")
        return

    def check_origin(self, origin) -> bool:
        return True


    def open(self):
        """Someone connects to the server, send initial data to them"""

        newId = SocketHandler.getUID()

        #Add player to clients list
        SocketHandler.clients.append({
            "socket": self,
            "gameData": {
                "id": newId,
            }
        })

        if SocketHandler.logMode != "off": #on / reduced
            print(f"\r### {Color.paint(f'Client joined', Color.aqua)} now serving {SocketHandler.getNumberOfClients()} clients")


    def on_message(self, message):
        msg = json.loads(message)

        if not "event" in msg: return

        #Update player data on the server
        if msg["event"] == "sync":
            if SocketHandler.getPlayerDataByID(msg["id"]) == None: return

            SocketHandler.updatePlayerData(self, msg)
            clientData = SocketHandler.getPlayerData(self)
            msg["name"] = clientData["name"]
            msg["team"] = clientData["team"]

        if msg["event"] == "lobby":
            self.write_message({"event": "syncServer", "subEvent": "lobby", "teams": SocketHandler.getTeamsJSON()})
            return

        #Somebody got hit (do not broadcast it)
        if msg["event"] == "hit":
            hitPlayerData = SocketHandler.getClientDataByID(msg["hitPlayerID"])
            if hitPlayerData == None: return
            killerData = SocketHandler.getClientDataByID(msg["id"])
            if killerData == None: return
            if (not SocketHandler.settings["frendlyFire"]) and killerData["gameData"]["team"] == hitPlayerData["gameData"]["team"]:
                if SocketHandler.logMode != "off":
                    print(f"Frendly fire cheater: {Color.paint(killerData['gameData']['id'], Color.aqua)} as {SocketHandler.getColoredName(killerData['gameData']['name'], killerData['gameData']['team'])}")
                return

            hitPlayerData["socket"].write_message({"event": "syncServer", "subEvent": "hit", "killer": msg["id"]})
            return

        #Somebody got killed!
        if msg["event"] == "death":
            victimData = SocketHandler.getPlayerDataByID(msg["id"])
            killerData = SocketHandler.getPlayerDataByID(msg["killer"])

            SocketHandler.addTeamScore(killerData["team"], 1)

            #Broadcast score change
            for c in SocketHandler.clients:
                try: c["socket"].write_message({"event": "syncServer", "subEvent": "score", "teams": SocketHandler.getTeamsJSON()})
                except: pass

            if SocketHandler.logMode == "on":
                print(f"\r### {SocketHandler.getColoredName(killerData['name'], killerData['team'])} killed {SocketHandler.getColoredName(victimData['name'], victimData['team'])}")

        if msg["event"] == "join":
            #Initialise player data
            clientId = SocketHandler.getPlayerData(self)["id"]
            newName = msg["name"]
            newTeam = msg["team"]

            #Validate input
            if newName == "":
                self.write_message({"event": "validate", "state": "fail", "reason": "Name must not be empty!"})
                return

            if len(newName) > 8:
                self.write_message({"event": "validate", "state": "fail", "reason": "Name is too long! (Max. 8 characters)"})
                return

            if not newTeam in SocketHandler.teamScores:
                self.write_message({"event": "validate", "state": "fail", "reason": f"Invalid team: '{newTeam}'"})
                return

            SocketHandler.setPlayerData(self, {"id": clientId, "name": newName, "team": newTeam})

            if SocketHandler.logMode == "on":
                print(f"\r### {Color.paint(msg['name'], Color.gray)} joined to team {SocketHandler.getTeamName(msg['team'])} ({SocketHandler.getNumberOfPlayersInTeam(msg['team'])})")

            #Broadcast join message
            for c in SocketHandler.clients:
                if c["socket"] == self: self.write_message({"event": "validate", "state": "success", "id": clientId, "name": newName, "team": newTeam, "level": Level.getJSON(), "settings": SocketHandler.settings})
                else: c["socket"].write_message('{"event": "join", "id": "'+clientId+'", "name": "'+newName+'", "team":"'+newTeam+'"}')

            return

        ######################################################################
        # Add timestamp & broadcast message to all clients (except for self) #
        ######################################################################
        #msg["time"] = time()
        for c in SocketHandler.clients:
            if msg["event"] != "death" and c["socket"] == self: continue
            try: c["socket"].write_message(msg)
            except: pass


    def on_close(self):
        leavingClientData = SocketHandler.getPlayerData(self)

        if leavingClientData != None and "id" in leavingClientData and "name" in leavingClientData and "team" in leavingClientData:
            id = leavingClientData["id"]
            name = leavingClientData["name"]
            team = leavingClientData["team"]
            for c in SocketHandler.clients:
                if c["socket"] == self: continue
                try: c["socket"].write_message({"event": "leave", "id": id, "name": name, "team": team})
                except: pass

            if SocketHandler.logMode != "off": #on / reduced
                print(f"\r### {Color.paint(leavingClientData['name'], Color.gray)} {Color.paint(f'left the game', Color.aqua)} now serving {SocketHandler.getNumberOfClients()} clients")

        SocketHandler.clients = SocketHandler.removePlayer(self)