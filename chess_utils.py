#!/usr/bin/env python
# -*- coding: utf-8 -*-

import chess
import chess.uci
import re
import urllib
import datetime
from datetime import datetime

stockfish = chess.uci.popen_engine("./stockfish-8-64")

def handle_move(games, results, user_move, user, show_board=True):
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