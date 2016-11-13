#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import time
from slackclient import SlackClient
import chess
import chess.uci
from datetime import datetime
import urllib
import chess.uci
from keys import SLACK_ID, BOT_ID, BOT_NAME
import re
import json

def save():
    json.dump(results, open("results.json", "w"))

def load_results():
    try:
        with open('results.json', 'r')as f:
            results = json.load(f)
    except IOError:
        results = {}

    return results

slack_client = SlackClient(SLACK_ID)
AT_BOT = "<@" + BOT_ID + ">"
games = {}
results = load_results()
stockfish = chess.uci.popen_engine("./stockfish-8-64")

def replace_moves(string):
    moves = {
        "0-0": "O-O",
        "kort rokade": "O-O",
        "0-0-0": "O-O-O",
        "lang rokade": "O-O-O",
        "S": "N",
        "L": "B",
        "T": "R",
        "D": "Q"
    }

    for k in moves:
        string = re.sub(k, moves[k], string)
    return string

def get_ids_and_usernames():
    get_users = slack_client.api_call("users.list")
    users = get_users.get('members')

    slack_users = {}

    for user in users:
        slack_users[user["id"]] = user["name"]

    return slack_users

def get_computer_move(board, level):
    stockfish.position(board)

    if level == 1:
        stockfish.setoption({"Skill Level": 1})
        return stockfish.go(movetime=50, depth=1)[0]
    elif level == 2:
        stockfish.setoption({"Skill Level": 6})
        return stockfish.go(movetime=100, depth=2)[0]
    elif level == 3:
        stockfish.setoption({"Skill Level": 11})
        return stockfish.go(movetime=200, depth=4)[0]
    elif level == 4:
        stockfish.setoption({"Skill Level": 17})
        return stockfish.go(movetime=250, depth=8)[0]
    elif level == 5:
        stockfish.setoption({"Skill Level": 20})
        return stockfish.go(movetime=400, depth=12)[0]

def get_board_image(fen):
    fen = urllib.quote(fen.encode("utf-8"))
    t = datetime.now().microsecond
    return 'http://webchess.freehostia.com/diag/chessdiag.php?fen=%s&size=large&coord=yes&cap=yes&stm=yes&fb=no&theme=smart&format=png&color1=ffffff&color2=fd5158&color3=000000t=%s.png' % (fen, t)

def handle_move(user_move, user, show_board=True):

    user_move = replace_moves(user_move)

    try:
        current_game = games[user]
    except:
        return ("Du spiller ikke mot meg, %s!" % user)
    current_game.push_san(user_move)

    if current_game.is_insufficient_material():
        games.pop(user, None)
        games.pop(user + "_level", None)
        results[user]["draw"] += 1
        return ("Ikke nok materiell. Remis!")
    elif current_game.is_stalemate():
        results[user]["draw"] += 1
        games.pop(user, None)
        games.pop(user + "_level", None)
        return ("Patt!")
    elif current_game.is_game_over():
        games.pop(user, None)
        games.pop(user + "_level", None)
        results[user]["win"] += 1
        return ("Sjakk matt, gratulerer!")

    computer_move = get_computer_move(current_game, level=games[user + "_level"])
    if show_board:
        current_game.push(computer_move)
        response = get_board_image(current_game.fen())
    else:
        response = current_game.variation_san([chess.Move.from_uci(m) for m in [str(computer_move)]])
        current_game.push(computer_move)

    if current_game.is_insufficient_material():
        games.pop(user, None)
        games.pop(user + "_level", None)
        results[user]["draw"] += 1
        return ("Ikke nok materiell. Remis!")
    elif current_game.is_stalemate():
        results[user]["draw"] += 1
        games.pop(user, None)
        games.pop(user + "_level", None)
        return ("Patt!")
    elif current_game.is_game_over():
        games.pop(user, None)
        games.pop(user + "_level", None)
        results[user]["loss"] += 1
        return ("Sjakk matt, jeg vant!")

    return response


def handle_command(command, channel, user):
    response = "Kjente ikke igjen kommandoen."

    if command.startswith("start"):
        try:
            level = int(command[-1])
        except:
            level = 1

        if not level in range(1, 6):
            level = 1

        if user in games.keys():
            response = "Du spiller allerede et parti mot meg!"
        else:
            games.update({user: chess.Board()})
            games.update({user + "_level": level})
            if not user in results:
                results[user] = {}
                results[user]["win"] = 0
                results[user]["draw"] = 0
                results[user]["loss"] = 0

            response = "Starter sjakkparti med %s, vanskelighetsgrad %s av 5!\n\n%s\n\nDin tur!" % (users[user], level, get_board_image(games[user].fen()))
    elif command.startswith("hjelp"):
        response = "Kommandoer: \n\n*start [1-5]* — _start et parti med vanskelighetsgrad 1-5 (1 er default)_" \
                   "            \n*Nf3* — _flytt en springer til f3 (se https://en.wikipedia.org/wiki/Algebraic_notation_(chess)#Notation_for_moves)_" \
                   "            \n*resign* — _gi opp_" \
                   "            \n*vis* — _vis brett_" \
                   "            \n*score* — _vis dine resultater mot meg_" \
                   "            \n*elo* — _vis ratingen din_" \
                   "            \n*elo alle — _vis ratingen til alle_* "

    elif command.startswith("vis") or command.startswith("show"):
        if user in games:
            board = games[user]
            response = get_board_image(board.fen())
        else:
            response = "Vi spiller ikke!"
    elif "resign" in command or "gir opp" in command:
        board = get_board_image(games[user].fen())
        games.pop(user, None)
        games.pop(user + "_level", None)
        results[user]["loss"] += 1
        response = "Greit, n00b\n\n%s" % board
    elif command.startswith("result"):
        if user in results.keys():
            response = "%s har vunnet %s, spilt %s remis og tapt %s partier mot meg." % (users[user], results[user]["win"], results[user]["draw"], results[user]["loss"])
        else:
            response = "%s har ikke spilt ferdig noen partier mot meg." % user
    else:
        try:
            response = handle_move(command, user)
        except:
            response = "Det der er ikke et gyldig trekk, ass!"

    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack(slack_rtm_output):
    messages = slack_rtm_output
    if messages and len(messages) > 0:
        for message in messages:
            if message and 'text' in message and AT_BOT in message['text']:
                return message['text'].split(AT_BOT)[1].strip(), message['channel'], message['user']
    return None, None, None

if __name__ == "__main__":

    users = get_ids_and_usernames()

    if slack_client.rtm_connect():
        print("Sjakkbot!")

        while True:
            command, channel, user = parse_slack(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel, user)
            time.sleep(0.5)
            save()
    else:
        print("Connection failed.")
