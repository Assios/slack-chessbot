#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import time
from slackclient import SlackClient
from keys import SLACK_ID, BOT_ID, BOT_NAME
from chess_utils import *
import json
import operator

def save():
    json.dump(results, open("results.json", "w"))
    json.dump(ratings, open("ratings.json", "w"))

def load_results():
    try:
        with open('results.json', 'r') as f:
            results = json.load(f)
    except IOError:
        results = {}

    return results

def load_ratings():
    try:
        with open('ratings.json', 'r') as f:
            ratings = json.load(f)
    except IOError:
        ratings = {
            "1": 800,
            "2": 1200,
            "3": 1600,
            "4": 2000,
            "5": 2400
        }

    return ratings

slack_client = SlackClient(SLACK_ID)
AT_BOT = "<@" + BOT_ID + ">"
games = {}
results = load_results()
ratings = load_ratings()

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

        if not user in ratings.keys():
            ratings[user] = 1200

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
                   "            \n*rating* — _vis ratingen din_" \
                   "            \n*ratingliste* — _vis ratingliste_ " \
                   "            \n*stilling* — _vis hvem som står best_ "

    elif command.startswith("vis") or command.startswith("show"):
        if user in games:
            board = games[user]
            response = get_board_image(board.fen())
        else:
            response = "Vi spiller ikke!"
    elif "resign" in command or "gir opp" in command:
        board = get_board_image(games[user].fen())
        level = str(games[user + "_level"])
        games.pop(user, None)
        games.pop(user + "_level", None)
        results[user]["loss"] += 1
        ratings[user], ratings[level] = calculate_new_ratings(ratings[user], ratings[level], 0)
        response = "Greit, n00b\n\n%s\n\nDin nye rating er %s og sjakkbot-level-%s sin nye rating er %s" % (board, ratings[user], level, ratings[level])
    elif command.startswith("result"):
        if user in results.keys():
            response = "%s har vunnet %s, spilt %s remis og tapt %s partier mot meg." % (users[user], results[user]["win"], results[user]["draw"], results[user]["loss"])
        else:
            response = "%s har ikke spilt ferdig noen partier mot meg." % user
    elif "ratingliste" in command or "elo all" in command or "ratings" in command:
        sorted_ratings = sorted(ratings.items(), key=operator.itemgetter(1), reverse=True)

        response = "Ratingliste:\n\n"

        for user, rating in sorted_ratings:
            try:
                username = users[user]
            except:
                username = "sjakkbot-level-%s" % user
            response += "*%s*: %s\n" % (username, int(rating))
    elif "elo" in command or "rating" in command:
        if not user in ratings.keys():
            response = "Vi har ikke spilt noen partier ennå, men du starter med 1200 i rating."
        else:
            response = "%s har %s i rating!" % (users[user], int(ratings[user]))
    elif "stilling" in command:
        game = games[user]
        response = get_evaluation(game)


    else:
        try:
            response = handle_move(games, results, ratings, command, user)
        except:
            response = "Det der er ikke et gyldig trekk, ass."

    save()
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
    else:
        print("Connection failed.")
