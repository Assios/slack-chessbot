import chess.uci
import chess
import inspect

engine = chess.uci.popen_engine("./stockfish-8-64")

board = chess.Board()

engine.position(board)

print inspect.getargspec(engine.go)

print engine.go(movetime=50, depth=1)[0]