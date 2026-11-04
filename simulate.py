"""Simula partidas completas solo con IAs: python3 simulate.py [n_partidas] [jugadores]"""
import sys
from catan.engine import Game
from catan import ai


def run(seed, n=4, max_turns=2000, quiet=True, house_2to1=True):
    g = Game.new([(f"IA{k+1}", "ia") for k in range(n)], seed=seed, house_2to1=house_2to1)
    turns = 0
    while g.s["ganador"] is None and turns < max_turns:
        ai.play_turn(g, g.players[g.current()]["nombre"], log=(lambda m: None) if quiet else print)
        turns += 1
    return g, turns


if __name__ == "__main__":
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    for s in range(games):
        g, t = run(s, n, quiet=games > 1)
        w = g.s["ganador"]
        print(f"seed {s}: {'ganó ' + g.players[w]['nombre'] + f' con {g.points(w)} pts' if w is not None else 'SIN GANADOR'} "
              f"en ronda {g.s['ronda']} ({t} turnos)")
    if games == 1: print(g.public_view())
