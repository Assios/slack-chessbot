#!/usr/bin/env python
# -*- coding: utf-8 -*-

import chess
import chess.uci
import re
import urllib
import datetime
from datetime import datetime
import math

stockfish = chess.uci.popen_engine("./stockfish-8-64")

def handle_move(games, results, ratings, user_move, user, show_board=True):
    user_move = replace_moves(user_move)

    try:
        current_game = games[user]
    except:
        return ("Du spiller ikke mot meg, %s!" % user)
    current_game.push_san(user_move)

    board_image = get_board_image(games[user].fen())

    if current_game.is_insufficient_material():
        level = str(games[user + "_level"])
        ratings[user], ratings[level] = calculate_new_ratings(ratings[user], ratings[level], 0.5)
        games.pop(user, None)
        games.pop(user + "_level", None)
        results[user]["draw"] += 1
        return "%s\n\nIkke nok materiell. Remis! Din nye rating er %s og sjakkbot-level-%s sin nye rating er %s" % (board_image, ratings[user], level, ratings[level])
    elif current_game.is_stalemate():
        level = str(games[user + "_level"])
        ratings[user], ratings[level] = calculate_new_ratings(ratings[user], ratings[level], 0.5)
        games.pop(user, None)
        games.pop(user + "_level", None)
        results[user]["draw"] += 1
        return "%s\n\nPatt! Din nye rating er %s og sjakkbot-level-%s sin nye rating er %s" % (board_image, ratings[user], level, ratings[level])
    elif current_game.is_game_over():
        level = str(games[user + "_level"])
        ratings[user], ratings[level] = calculate_new_ratings(ratings[user], ratings[level], 1)
        games.pop(user, None)
        games.pop(user + "_level", None)
        results[user]["win"] += 1
        return "%s\n\nSjakk matt, gratulerer! Din nye rating er %s og sjakkbot-level-%s sin nye rating er %s" % (board_image, ratings[user], level, ratings[level])

    computer_move = get_computer_move(current_game, level=games[user + "_level"])

    if show_board:
        m = current_game.variation_san([chess.Move.from_uci(m) for m in [str(computer_move)]])
        current_game.push(computer_move)
        response = "%s\n\n%s" % (m, get_board_image(current_game.fen()))
    else:
        response = current_game.variation_san([chess.Move.from_uci(m) for m in [str(computer_move)]])
        current_game.push(computer_move)

    if current_game.is_insufficient_material():
        level = str(games[user + "_level"])
        ratings[user], ratings[level] = calculate_new_ratings(ratings[user], ratings[level], 0.5)
        games.pop(user, None)
        games.pop(user + "_level", None)
        results[user]["draw"] += 1
        return "%s\n\nIkke nok materiell. Remis! Din nye rating er %s og sjakkbot-level-%s sin nye rating er %s" % (board_image, ratings[user], level, ratings[level])
    elif current_game.is_stalemate():
        level = str(games[user + "_level"])
        ratings[user], ratings[level] = calculate_new_ratings(ratings[user], ratings[level], 0.5)
        results[user]["draw"] += 1
        games.pop(user, None)
        games.pop(user + "_level", None)
        return "%s\n\nPatt! Din nye rating er %s og sjakkbot-level-%s sin nye rating er %s" % (board_image, ratings[user], level, ratings[level])
    elif current_game.is_game_over():
        level = str(games[user + "_level"])
        ratings[user], ratings[level] = calculate_new_ratings(ratings[user], ratings[level], 0)
        games.pop(user, None)
        games.pop(user + "_level", None)
        results[user]["loss"] += 1
        return "%s\n\nSjakk matt, du tapte! Din nye rating er %s og sjakkbot-level-%s sin nye rating er %s" % (board_image, ratings[user], level, ratings[level])

    return response

def get_board_image(fen):
    fen = urllib.quote(fen.encode("utf-8"))
    t = datetime.now().microsecond
    return 'http://webchess.freehostia.com/diag/chessdiag.php?fen=%s&size=large&coord=yes&cap=yes&stm=yes&fb=no&theme=smart&format=png&color1=ffffff&color2=fd5158&color3=000000t=%s.png' % (fen, t)

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

def get_evaluation(board):
    info_handler = chess.uci.InfoHandler()
    stockfish.info_handlers.append(info_handler)
    stockfish.position(board)
    stockfish.go(movetime=400)
    score = info_handler.info["score"][1]

    if score.mate:
        if score.mate < 0:
            score.mate = abs(score.mate)
            prefix = "Jeg"
        else:
            prefix = "Du"
        return "%s har matt i %s!!" % (prefix, score.mate)
    else:
        cp = float(score.cp)

        prefix = "Du"
        if cp < 0:
            prefix = "Jeg"

        p = abs(cp) / 100

        return "%s har en fordel på %s bønder." % (prefix, p)


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

def get_k_factor(rating):
    if rating < 2100:
        return 32
    elif rating < 2400:
        return 24
    else:
        return 16


def calculate_new_ratings(rating_a, rating_b, score_a):
    e_a = 1 / (1 + math.pow(10, (rating_b - rating_a) / 400.))
    e_b = 1 - e_a
    a_k = get_k_factor(rating_a)
    b_k = get_k_factor(rating_b)
    new_rating_a = rating_a + a_k * (score_a - e_a)
    score_b = 1.0 - score_a
    new_rating_b = rating_b + b_k * (score_b - e_b)
    return new_rating_a, new_rating_b
