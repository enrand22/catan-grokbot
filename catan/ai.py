"""Jugador IA sencillo y honesto: solo usa el estado público y SU propia mano."""
from collections import Counter
from .engine import COST, RES, VHEX, EDGES, ADJ, edge_of, RuleError


def _settle_score(g, v):
    terr = {g.s["hexes"][l]["terreno"] for l in VHEX[v]} - {"desierto"}
    return g.vertex_pips(v) * 10 + len(terr)


def setup_move(g, name):
    opts = g.legal_moves(name)["aldeas"]
    v = max(opts, key=lambda x: (_settle_score(g, x), -x))
    # camino hacia el vecino con mejor potencial
    best = max(ADJ[v], key=lambda n: max([_settle_score(g, m) for m in ADJ[n] if m != v and g.can_settle(m)] or [0]))
    return v, edge_of(v, best)


def _road_target(g, i):
    """Camino legal que acerque a la mejor esquina libre."""
    best, be = -1, None
    for e in range(len(EDGES)):
        if not g.can_road(e, i): continue
        sc = max([_settle_score(g, v) for v in EDGES[e] if g.can_settle(v)] +
                 [_settle_score(g, m) // 2 for v in EDGES[e] for m in ADJ[v] if g.can_settle(m)] + [0])
        if sc > best: best, be = sc, e
    return be


def play_turn(g, name, log=print):
    """Juega un turno completo de la IA `name`. Devuelve la lista de eventos."""
    ev = []
    say = lambda m: (ev.append(m), log(m))
    i = g.idx(name)
    if g.s["fase"] == "colocacion":
        v, e = setup_move(g, name); say(g.place(name, v, e)); return ev
    if not g.s["tirado"]:
        say(g.roll(name))
    if resolve_pending(g, say, ai_only=True):
        say("⏸️ Esperando a que los humanos resuelvan descartes/ladrón; luego vuelve a ejecutar `ai`.")
        return ev
    for _ in range(20):
        if g.s["ganador"] is not None: return ev
        m = g.legal_moves(name)
        if m["ciudades"]:
            say(g.build(name, "ciudad", max(m["ciudades"], key=lambda v: g.vertex_pips(v)))); continue
        if m["aldeas"]:
            say(g.build(name, "aldea", max(m["aldeas"], key=lambda v: _settle_score(g, v)))); continue
        if m["caminos"] and g.count("aldea", i) + g.count("ciudad", i) < 9:
            # construir camino solo si no hay sitio para aldea alcanzable
            e = _road_target(g, i)
            if e is not None and not any(g.can_settle(v, i, True) for v in VHEX):
                say(g.build(name, "camino", e)); continue
        if _trade(g, name, say): continue
        break
    if g.s["ganador"] is None:
        say(g.end_turn(name))
    return ev


def _trade(g, name, say):
    h = g.players[g.idx(name)]["mano"]
    goal = "ciudad" if h["mineral"] >= 2 and g.count("aldea", g.idx(name)) else "aldea"
    need = [r for r, c in COST[goal].items() if h[r] < c]
    if not need: need = [r for r, c in COST["camino"].items() if h[r] < c]
    rate = g.best_rate()
    # solo cambia sobrantes: nunca entrega cartas que necesita para su objetivo
    spare = sorted((r for r in RES if r not in need and h[r] - COST[goal].get(r, 0) >= rate),
                   key=lambda r: -(h[r] - COST[goal].get(r, 0)))
    if need and spare:
        say(g.trade_bank(name, spare[0], need[0], rate)); return True
    return False


def discard_choice(hand, n):
    """Descarta lo más abundante primero."""
    h = Counter(hand); out = Counter()
    for _ in range(n):
        r = max(RES, key=lambda x: h[x]); h[r] -= 1; out[r] += 1
    return dict(out)


def robber_choice(g, i):
    """Bloquea el hexágono más productivo de los rivales (información pública)."""
    def score(lab):
        if lab == g.s["ladron"]: return -999
        sc = 0
        from .engine import HEXV, PIPS
        for v in HEXV[lab]:
            o = g.owner_v(v)
            if o == i: sc -= 100
            elif o is not None: sc += PIPS.get(g.s["hexes"][lab]["numero"], 0) * (1 + g.points(o))
        return sc
    lab = max(g.s["hexes"], key=score)
    vs = g.robber_victims(i, lab)
    victim = max(vs, key=lambda j: g.points(j)) if vs else None
    return lab, (g.players[victim]["nombre"] if victim is not None else None)


def resolve_pending(g, say, ai_only=False):
    """Resuelve descartes/ladrón de los asientos IA. Devuelve True si queda algo de humanos."""
    p = g.s["pendiente"]
    if not p: return False
    for j in list(p["descartes"]):
        pl = g.players[int(j)]
        if pl["tipo"] == "ia" or not ai_only:
            say(g.discard(pl["nombre"], discard_choice(pl["mano"], p["descartes"][j])))
    if p["descartes"]: return True
    mover = g.players[p["mover_ladron"]]
    if mover["tipo"] == "ia" or not ai_only:
        lab, vic = robber_choice(g, p["mover_ladron"])
        say(g.move_robber(mover["nombre"], lab, vic)); return False
    return True
