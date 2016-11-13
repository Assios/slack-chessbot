#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import time
from slackclient import SlackClient
from keys import SLACK_ID, BOT_ID, BOT_NAME
from chess_utils import *
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

def get_ids_and_usernames():
    get_users = slack_client.api_call("users.list")
    users = get_users.get('members')

    slack_users = {}

    for user in users:
        slack_users[user["id"]] = user["name"]

    return slack_users


def reply(command, channel, user):
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
        response = handle_move(games, results, command, user)


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
                reply(command, channel, user)
            time.sleep(0.5)
            save()
    else:
        print("Connection failed.")
