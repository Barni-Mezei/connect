#!/usr/bin/env python

import json
from os import walk, path

from data import Level
from color import Color
from socket_handler import SocketHandler

def execute_cli_line(line):
    if line == "": return
    command = line.split(" ")

    if command[0] == "help":
        print("Log mode:", SocketHandler.logMode)
        print(f"\
{Color.paint('log', Color.gray)} [on|off|reduced]\t\t\t- Sets the logging mode\n\
{Color.paint('list', Color.gray)} [full]\t\t\t\t- Lists all of the players and their data if [full] is typed\n\
{Color.paint('list_maps', Color.gray)} \t\t\t\t- Lists all of the available maps\n\
{Color.paint('list_settings', Color.gray)}\t\t\t\t- Lists all of the available settings, when using 'setting'\n\
{Color.paint('kick|kick_player', Color.gray)} [id4]\t\t\t- Disconnects the selected player\n\
{Color.paint('map', Color.gray)} [map name]\t\t\t\t- Changes the map to [map name]. (A file's name in the ./maps folder, without the file extension)\n\
{Color.paint('teams', Color.gray)}\t\t\t\t\t- Lists all of the teams and their score\n\
{Color.paint('add_score', Color.gray)} [team] [amount]\t\t- Adds [amount] score to [team]\n\
{Color.paint('sub_score', Color.gray)} [team] [amount]\t\t- Removes [amount] score from [team]\n\
{Color.paint('reset_score', Color.gray)} [team]\t\t\t- Resets [team]'s score to 0 (type 'all' to reset all teams)\n\
{Color.paint('setting|set|s', Color.gray)} [setting name] [value]\t- Use 'list_settings' to view all settings\n\
Press {Color.paint('Ctrl + C', Color.aqua)} to close the server.")
        return

    if command[0] == "log":
        if len(command) >= 2:
            SocketHandler.logMode = command[1]
            return

    if command[0] == "list":
        if len(SocketHandler.clients) == 0:
            print("No players connected, yet!")
            return

        print(f"Clients ({len(SocketHandler.clients)}):", end="")
        if SocketHandler.getNumberOfClients() > 0 and len(command) >= 2 and (command[1] == "full"):
            for c in SocketHandler.clients:
                print()
                for key in c["gameData"]:
                    if key == "event": continue
                    if key == "time": continue
                    if key == "bullets":
                        print(f"\tNumber of bullets: {Color.paint(len(c['gameData'][key]), Color.aqua)}")
                    else:
                        if key == "id": print(f"\t{key}: {Color.paint(c['gameData'][key], Color.aqua)}")
                        elif key == "name": print(f"\t{key}: {Color.paint(c['gameData'][key], Color.gray)}")
                        elif key == "hp": print(f"\t{key}: {Color.paint(c['gameData'][key], Color.red)}")
                        elif key == "team": print(f"\tteam: {SocketHandler.getTeamName(c['gameData'][key])}")
                        else: print(f"\t{key}: {c['gameData'][key]}")
        else:
            print()
            for c in SocketHandler.clients:
                id = c['gameData']['id'] if "id" in c['gameData'] else "unknown"
                name = c['gameData']['name'] if "name" in c['gameData'] else "unknown"
                team = c['gameData']['team'] if "team" in c['gameData'] else ""
                hp = c['gameData']['hp'] if "hp" in c['gameData'] else "unknown"

                print(f"\t- {Color.paint(id, Color.aqua)} as {Color.paint(name, Color.gray)}({SocketHandler.getTeamName(team)}) HP: {Color.paint(hp, Color.red)}")
        print("----------")
        return

    if command[0] == "list_settings":
        print("Available settings:")
        for s in SocketHandler.settings:
            print(f"- {Color.paint(s, Color.gray)}: {Color.paint(type(SocketHandler.settings[s]).__name__, Color.aqua)} - value: {SocketHandler.settings[s]}")
            return

    if command[0] == "list_maps":
        print("Available .json files:")
        for fileName in next(walk("./maps"), (None, None, []))[2]:
            print(f"- {fileName}")

    if command[0] == "kick" or command[0] == "kick_player":
        if len(command) >= 2:
            try:
                if len(command) >= 3: SocketHandler.disconnectPlayerByShortID(command[1], " ".join(command[2:]))
                else: SocketHandler.disconnectPlayerByShortID(command[1])
            finally: return

    if command[0] == "map":
        if len(command) >= 2:
            global Level
            newMap = "maps/" + command[1] + ".json"
            if not path.isfile(newMap):
                print(f"{Color.paint('No map found', Color.red)}")
                return
            print(f"Level set to: {Color.paint(newMap, Color.gray)}")
            Level.currentPath = newMap
            SocketHandler.restart_game()
            return

    if command[0] == "teams":
        SocketHandler.logTeamScores()
        return

    if command[0] == "add_score":
        if len(command) >= 3:
            SocketHandler.addTeamScore(command[1], int(command[2]))
            SocketHandler.synchroniseScore()
            return

    if command[0] == "sub_score":
        if len(command) >= 3:
            SocketHandler.removeTeamScore(command[1], int(command[2]))
            SocketHandler.synchroniseScore()
            return

    if command[0] == "reset_score":
        if len(command) >= 2:
            SocketHandler.resetTeamScore(command[1])
            SocketHandler.synchroniseScore()
            return

    if command[0] == "setting" or command[0] == "s" or command[0] == "set":
        if len(command) >= 3:
            if command[1] in SocketHandler.settings:
                SocketHandler.settings[command[1]] = json.loads(command[2])
                SocketHandler.synchroniseSettings()
                return
            else:
                print(Color.paint("Invalid setting name. Type 'list_settings' for more info", Color.red))
                return

    print(Color.paint("Invalid CLI command. Type 'help' for more info.", Color.red))

def execute_cli():
    while True:
        try:
            ln = input(">")
            execute_cli_line(ln.strip())
        except Exception as e:
            print(Color.paint(f"CLI execution error: {e}", Color.red))
        except KeyboardInterrupt:
            return
