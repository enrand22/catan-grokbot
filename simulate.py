"""Simula partidas solo con IAs / simulate AI-only games: python3 simulate.py [games] [players] [es|en]"""
import sys
from catan.engine import Game
from catan import ai


def run(seed, n=4, max_turns=2000, quiet=True, house_2to1=True, lang="es"):
    g = Game.new([(f"IA{k+1}", "ia") for k in range(n)], seed=seed, house_2to1=house_2to1, lang=lang)
    turns = 0
    while g.s["ganador"] is None and turns < max_turns:
        ai.play_turn(g, g.players[g.current()]["nombre"], log=(lambda m: None) if quiet else print)
        turns += 1
    return g, turns


if __name__ == "__main__":
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    lang = sys.argv[3] if len(sys.argv) > 3 else "es"
    for s in range(games):
        g, t = run(s, n, quiet=games > 1, lang=lang)
        w = g.s["ganador"]
        print(f"seed {s}: winner={g.players[w]['nombre'] if w is not None else 'NONE'} pts={g.points(w) if w is not None else 0} "
              f"round={g.s['ronda']} turns={t}")
    if games == 1: print(g.public_view())
