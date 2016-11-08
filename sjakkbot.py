#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import time
from slackclient import SlackClient
import chess
import random
import urllib
from keys import SLACK_ID, BOT_ID, BOT_NAME

slack_client = SlackClient(SLACK_ID)
AT_BOT = "<@" + BOT_ID + ">"
games = {}
results = {}
config = {}

def get_board_image(fen):
    fen = urllib.quote(fen.encode("utf-8"))
    return 'http://webchess.freehostia.com/diag/chessdiag.php?fen=%s&size=large&coord=yes&cap=yes&stm=yes&fb=no&theme=classic&format=auto&color1=E3CEAA&color2=635147&color3=000000&.png' % fen

def handle_move(user_move, user, show_board=True):
    try:
        current_game = games[user]
    except:
        return ("Du spiller ikke mot meg, %s!" % user)
    current_game.push_san(user_move)

    if current_game.is_insufficient_material():
        games.pop(user, None)
        results[user]["draw"] += 1
        return ("Ikke nok materiell. Remis!")
    elif current_game.is_stalemate():
        results[user]["draw"] += 1
        games.pop(user, None)
        return ("Patt!")
    elif current_game.is_game_over():
        games.pop(user, None)
        results[user]["win"] += 1
        return ("Sjakk matt, gratulerer!")

    computer_move = random.choice([move for move in current_game.legal_moves])
    if show_board:
        current_game.push(computer_move)
        response = get_board_image(current_game.fen())
    else:
        response = current_game.variation_san([chess.Move.from_uci(m) for m in [str(computer_move)]])
        current_game.push(computer_move)

    if current_game.is_insufficient_material():
        games.pop(user, None)
        results[user]["draw"] += 1
        return ("Ikke nok materiell. Remis!")
    elif current_game.is_stalemate():
        results[user]["draw"] += 1
        games.pop(user, None)
        return ("Patt!")
    elif current_game.is_game_over():
        games.pop(user, None)
        results[user]["loss"] += 1
        return ("Sjakk matt, jeg vant!")

    return response


def handle_command(command, channel, user):
    response = "Kjente ikke igjen kommandoen."

    if command.startswith("start"):
        if user in games.keys():
            response = "Du spiller allerede et parti mot meg!"
        else:
            games.update({user: chess.Board()})
            if not user in results:
                results[user] = {}
                results[user]["win"] = 0
                results[user]["draw"] = 0
                results[user]["loss"] = 0

        response = "Starter sjakkparti med %s!" % user
    elif command.startswith("hjelp"):
        response = "Kommandoer: "
    elif command.startswith("vis"):
        board = games[user]
        response = get_board_image(board.fen())
    elif command.startswith("result"):
        if user in results.keys():
            response = "%s har vunnet %s, spilt %s remis og tapt %s partier mot meg." % (user, results[user]["win"], results[user]["draw"], results[user]["loss"])
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
    #get_users = slack_client.api_call("users.list")
    #users = get_users.get('members')

    if slack_client.rtm_connect():
        print("Sjakkbot!")

        while True:
            command, channel, user = parse_slack(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel, user)
            time.sleep(0.5)
    else:
        print("Connection failed.")
