"""Motor de Catan (versión base simplificada) — solo biblioteca estándar.

Reglas incluidas: tablero aleatorio de 19 hexágonos (sin 6/8 adyacentes), colocación
inicial en serpiente, dados, producción, ladrón (descarte con >7 cartas, mover, robar),
caminos, aldeas, ciudades, comercio con el banco 4:1, camino más largo (+2) y victoria
a 10 puntos (configurable). No incluye: cartas de desarrollo, puertos ni comercio entre
jugadores (ver README).
"""
import json, math, random
from collections import defaultdict

RES = ["madera", "ladrillo", "oveja", "trigo", "mineral"]
TERRAINS = ["madera"]*4 + ["oveja"]*4 + ["trigo"]*4 + ["ladrillo"]*3 + ["mineral"]*3 + ["desierto"]
NUMBERS = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
PIPS = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}
COST = {
    "camino": {"madera": 1, "ladrillo": 1},
    "aldea": {"madera": 1, "ladrillo": 1, "oveja": 1, "trigo": 1},
    "ciudad": {"trigo": 2, "mineral": 3},
}
LIMITS = {"camino": 15, "aldea": 5, "ciudad": 4}
HEX_COORDS = [(0, -2), (1, -2), (2, -2), (-1, -1), (0, -1), (1, -1), (2, -1),
              (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-2, 1), (-1, 1), (0, 1), (1, 1),
              (-2, 2), (-1, 2), (0, 2)]
LABELS = [chr(65 + i) for i in range(19)]
SEAT_TYPES = ("humano", "bot", "ia")
EMOJI = {"madera": "🌲", "oveja": "🐑", "trigo": "🌾", "ladrillo": "🧱", "mineral": "⛰️", "desierto": "🏜️"}


class RuleError(Exception):
    pass


def _graph():
    """Vértices numerados 0..53 y aristas 0..71 a partir de la geometría real."""
    keys, vhex, hexv = {}, defaultdict(set), {}
    edges = set()
    for lab, (q, r) in zip(LABELS, HEX_COORDS):
        cx, cy = math.sqrt(3) * (q + r / 2), 1.5 * r
        ids = []
        for i in range(6):
            a = math.radians(60 * i - 30)
            k = (round(cx + math.cos(a), 2) + 0.0, round(cy + math.sin(a), 2) + 0.0)
            if k not in keys:
                keys[k] = len(keys)
            ids.append(keys[k]); vhex[keys[k]].add(lab)
        hexv[lab] = ids
        for i in range(6):
            edges.add(tuple(sorted((ids[i], ids[(i + 1) % 6]))))
    edges = sorted(edges)
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b); adj[b].add(a)
    return ({v: sorted(h) for v, h in vhex.items()}, hexv, edges, {v: sorted(n) for v, n in adj.items()})


VHEX, HEXV, EDGES, ADJ = _graph()
EDGE_ID = {e: i for i, e in enumerate(EDGES)}
HEX_NB = {}
_coord = dict(zip(LABELS, HEX_COORDS)); _inv = {c: l for l, c in _coord.items()}
for _l, (_q, _r) in _coord.items():
    HEX_NB[_l] = [_inv[(_q + dq, _r + dr)] for dq, dr in [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
                  if (_q + dq, _r + dr) in _inv]


def edge_of(a, b):
    e = tuple(sorted((a, b)))
    if e not in EDGE_ID:
        raise RuleError(f"los vértices {a} y {b} no están conectados")
    return EDGE_ID[e]


def random_board(rng):
    while True:
        t = TERRAINS[:]; n = NUMBERS[:]
        rng.shuffle(t); rng.shuffle(n)
        hexes, it = {}, iter(n)
        for lab, ter in zip(LABELS, t):
            hexes[lab] = {"terreno": ter, "numero": None if ter == "desierto" else next(it)}
        red = [l for l, h in hexes.items() if h["numero"] in (6, 8)]
        if all(hexes[nb]["numero"] not in (6, 8) for l in red for nb in HEX_NB[l]):
            return hexes


class Game:
    def __init__(self, state):
        self.s = state

    # ---------- creación / persistencia ----------
    @classmethod
    def new(cls, seats, seed=None, target=10):
        """seats: lista de (nombre, tipo) con tipo en humano|bot|ia. 2 a 4 asientos."""
        if not 2 <= len(seats) <= 4:
            raise RuleError("se necesitan de 2 a 4 jugadores")
        names = [n for n, _ in seats]
        if len(set(names)) != len(names):
            raise RuleError("los nombres deben ser únicos")
        for _, t in seats:
            if t not in SEAT_TYPES:
                raise RuleError(f"tipo inválido {t!r}; usa {SEAT_TYPES}")
        rng = random.Random(seed)
        hexes = random_board(rng)
        desert = next(l for l, h in hexes.items() if h["terreno"] == "desierto")
        order = list(range(len(seats))); rng.shuffle(order)
        players = [{"nombre": seats[i][0], "tipo": seats[i][1], "mano": {r: 0 for r in RES}} for i in order]
        n = len(players)
        st = {
            "version": 1, "meta": target, "hexes": hexes, "ladron": desert,
            "jugadores": players, "aldeas": {}, "ciudades": {}, "caminos": {},
            "fase": "colocacion", "colocacion": list(range(n)) + list(range(n - 1, -1, -1)),
            "paso_colocacion": 0, "esperando": "aldea", "ultima_aldea": None,
            "turno": 0, "tirado": False, "dados": None, "pendiente": None,
            "camino_largo": None, "ganador": None, "ronda": 0,
            "rng": rng.randrange(2**31), "tiradas": 0,
            "log": [],
        }
        return cls(st)

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.s, f, indent=1, ensure_ascii=False)

    def _rand(self, n):
        r = random.Random(self.s["rng"] + self.s["tiradas"]); self.s["tiradas"] += 1
        return r.randrange(n)

    # ---------- utilidades ----------
    @property
    def players(self):
        return self.s["jugadores"]

    def idx(self, name):
        for i, p in enumerate(self.players):
            if p["nombre"].lower() == str(name).lower():
                return i
        raise RuleError(f"no existe el jugador {name!r}")

    def current(self):
        s = self.s
        if s["fase"] == "colocacion":
            return s["colocacion"][s["paso_colocacion"]]
        return s["turno"]

    def owner_v(self, v):
        v = str(v)
        if v in self.s["aldeas"]: return self.s["aldeas"][v]
        if v in self.s["ciudades"]: return self.s["ciudades"][v]
        return None

    def log(self, msg):
        self.s["log"].append(msg)
        return msg

    def points(self, i, public=False):
        pts = sum(1 for o in self.s["aldeas"].values() if o == i) + 2 * sum(1 for o in self.s["ciudades"].values() if o == i)
        if self.s["camino_largo"] == i: pts += 2
        return pts

    def count(self, kind, i):
        return sum(1 for o in self.s[{"aldea": "aldeas", "ciudad": "ciudades", "camino": "caminos"}[kind]].values() if o == i)

    def _check_turn(self, i, phase):
        if self.s["ganador"] is not None: raise RuleError("la partida ya terminó")
        if self.s["fase"] != phase: raise RuleError(f"no estamos en fase {phase}")
        if self.current() != i: raise RuleError(f"no es turno de {self.players[i]['nombre']}")

    def _pay(self, i, cost):
        h = self.players[i]["mano"]
        if any(h[r] < c for r, c in cost.items()): raise RuleError(f"faltan recursos: cuesta {cost}")
        for r, c in cost.items(): h[r] -= c

    def can_settle(self, v, i=None, need_road=False):
        v = int(v)
        if v not in VHEX: return False
        if self.owner_v(v) is not None: return False
        if any(self.owner_v(n) is not None for n in ADJ[v]): return False
        if need_road and not any(self.s["caminos"].get(str(edge_of(v, n))) == i for n in ADJ[v]): return False
        return True

    def can_road(self, e, i):
        e = int(e)
        if not 0 <= e < len(EDGES) or str(e) in self.s["caminos"]: return False
        for v in EDGES[e]:
            o = self.owner_v(v)
            if o == i: return True
            if o is None and any(self.s["caminos"].get(str(edge_of(v, n))) == i for n in ADJ[v] if edge_of(v, n) != e):
                return True
        return False

    # ---------- colocación inicial ----------
    def place(self, name, vertex, edge):
        i = self.idx(name); self._check_turn(i, "colocacion")
        vertex, edge = int(vertex), int(edge)
        if not self.can_settle(vertex): raise RuleError(f"no se puede poner aldea en {vertex} (ocupado o regla de distancia)")
        if not (0 <= edge < len(EDGES)) or vertex not in EDGES[edge]: raise RuleError("el camino debe tocar la aldea nueva")
        if str(edge) in self.s["caminos"]: raise RuleError("camino ocupado")
        self.s["aldeas"][str(vertex)] = i; self.s["caminos"][str(edge)] = i
        s = self.s; msg = f"{self.players[i]['nombre']} coloca aldea en {vertex} y camino {edge}"
        if s["paso_colocacion"] >= len(self.players):  # segunda ronda: cobra
            got = defaultdict(int)
            for lab in VHEX[vertex]:
                t = s["hexes"][lab]["terreno"]
                if t != "desierto": self.players[i]["mano"][t] += 1; got[t] += 1
            msg += f" y recibe {dict(got)}"
        s["paso_colocacion"] += 1
        if s["paso_colocacion"] >= len(s["colocacion"]):
            s["fase"] = "juego"; s["turno"] = 0; s["ronda"] = 1
        return self.log(msg)

    # ---------- juego ----------
    def roll(self, name, dice=None):
        i = self.idx(name); self._check_turn(i, "juego")
        if self.s["tirado"]: raise RuleError("ya tiraste los dados este turno")
        if self.s["pendiente"]: raise RuleError("hay una acción pendiente del ladrón")
        a, b = dice if dice else (self._rand(6) + 1, self._rand(6) + 1)
        t = a + b; self.s["tirado"] = True; self.s["dados"] = [a, b]
        msg = f"{self.players[i]['nombre']} tira {a}+{b}={t}"
        if t == 7:
            disc = {str(j): sum(p["mano"].values()) // 2 for j, p in enumerate(self.players) if sum(p["mano"].values()) > 7}
            self.s["pendiente"] = {"descartes": disc, "mover_ladron": i}
            if disc: msg += "; deben descartar: " + ", ".join(f"{self.players[int(j)]['nombre']} {n}" for j, n in disc.items())
            msg += "; mueve el ladrón"
        else:
            gains = self._produce(t)
            msg += "; " + ("; ".join(f"{self.players[j]['nombre']} recibe {g}" for j, g in gains.items()) or "nadie cobra")
        return self.log(msg)

    def _produce(self, t):
        gains = defaultdict(lambda: defaultdict(int))
        for lab, h in self.s["hexes"].items():
            if h["numero"] != t or lab == self.s["ladron"]: continue
            for v in HEXV[lab]:
                o = self.owner_v(v)
                if o is not None:
                    gains[o][h["terreno"]] += 2 if str(v) in self.s["ciudades"] else 1
        for j, g in gains.items():
            for r, c in g.items(): self.players[j]["mano"][r] += c
        return {j: dict(g) for j, g in gains.items()}

    def discard(self, name, cards):
        i = self.idx(name); p = self.s["pendiente"]
        if not p or str(i) not in p["descartes"]: raise RuleError("no tienes que descartar")
        need = p["descartes"][str(i)]
        if sum(cards.values()) != need: raise RuleError(f"debes descartar exactamente {need}")
        self._pay(i, cards); del p["descartes"][str(i)]
        return self.log(f"{self.players[i]['nombre']} descarta {need} cartas")

    def move_robber(self, name, hexlab, victim=None):
        i = self.idx(name); p = self.s["pendiente"]
        if not p or p["mover_ladron"] != i: raise RuleError("no te toca mover el ladrón")
        if p["descartes"]: raise RuleError("faltan descartes de: " + ", ".join(self.players[int(j)]["nombre"] for j in p["descartes"]))
        hexlab = str(hexlab).upper()
        if hexlab not in self.s["hexes"] or hexlab == self.s["ladron"]: raise RuleError("hexágono inválido (debe ser otro)")
        victims = self.robber_victims(i, hexlab)
        self.s["ladron"] = hexlab; self.s["pendiente"] = None
        msg = f"{self.players[i]['nombre']} mueve el ladrón a {hexlab}"
        if victims:
            j = self.idx(victim) if victim is not None else victims[0]
            if j not in victims: raise RuleError("esa víctima no tiene edificio en el hexágono")
            pool = [r for r, c in self.players[j]["mano"].items() for _ in range(c)]
            if pool:
                r = pool[self._rand(len(pool))]
                self.players[j]["mano"][r] -= 1; self.players[i]["mano"][r] += 1
                msg += f" y roba 1 carta a {self.players[j]['nombre']}"  # recurso oculto
        return self.log(msg)

    def robber_victims(self, i, hexlab):
        return sorted({o for v in HEXV[hexlab] for o in [self.owner_v(v)] if o is not None and o != i
                       and sum(self.players[o]["mano"].values()) > 0})

    def _ready(self, i):
        self._check_turn(i, "juego")
        if not self.s["tirado"]: raise RuleError("primero tira los dados")
        if self.s["pendiente"]: raise RuleError("resuelve primero el ladrón")

    def build(self, name, kind, where):
        i = self.idx(name); self._ready(i); where = int(where)
        if self.count(kind, i) >= LIMITS[kind]: raise RuleError(f"ya no te quedan piezas de {kind}")
        if kind == "camino":
            if not self.can_road(where, i): raise RuleError(f"camino {where} no es legal")
            self._pay(i, COST[kind]); self.s["caminos"][str(where)] = i
        elif kind == "aldea":
            if not self.can_settle(where, i, need_road=True): raise RuleError(f"aldea en {where} no es legal")
            self._pay(i, COST[kind]); self.s["aldeas"][str(where)] = i
        elif kind == "ciudad":
            if self.s["aldeas"].get(str(where)) != i: raise RuleError("la ciudad debe reemplazar una aldea tuya")
            self._pay(i, COST[kind]); del self.s["aldeas"][str(where)]; self.s["ciudades"][str(where)] = i
        else:
            raise RuleError("tipo de construcción: camino | aldea | ciudad")
        msg = self.log(f"{self.players[i]['nombre']} construye {kind} en {where}")
        if kind != "ciudad": self._update_longest()
        self._check_win(i)
        return msg

    def trade_bank(self, name, give, get):
        i = self.idx(name); self._ready(i)
        if give not in RES or get not in RES or give == get: raise RuleError("recursos inválidos")
        self._pay(i, {give: 4}); self.players[i]["mano"][get] += 1
        return self.log(f"{self.players[i]['nombre']} cambia 4 {give} por 1 {get} con el banco")

    def end_turn(self, name):
        i = self.idx(name); self._ready(i)
        self.s["turno"] = (i + 1) % len(self.players); self.s["tirado"] = False; self.s["dados"] = None
        if self.s["turno"] == 0: self.s["ronda"] += 1
        return self.log(f"{self.players[i]['nombre']} termina su turno → {self.players[self.s['turno']]['nombre']}")

    # ---------- camino más largo ----------
    def road_length(self, i):
        mine = [EDGES[int(e)] for e, o in self.s["caminos"].items() if o == i]
        nbrs = defaultdict(list)
        for k, (a, b) in enumerate(mine):
            nbrs[a].append((k, b)); nbrs[b].append((k, a))
        best = 0

        def dfs(v, used):
            nonlocal best
            best = max(best, len(used))
            o = self.owner_v(v)
            if used and o is not None and o != i: return  # bloqueado por rival
            for k, w in nbrs[v]:
                if k not in used:
                    used.add(k); dfs(w, used); used.remove(k)
        for v in list(nbrs):
            dfs(v, set())
        return best

    def _update_longest(self):
        lens = [self.road_length(i) for i in range(len(self.players))]
        cur = self.s["camino_largo"]
        if cur is not None and lens[cur] < 5: cur = None
        top = max(lens)
        if top >= 5:
            leaders = [i for i, l in enumerate(lens) if l == top]
            if cur is None or lens[cur] < top:
                cur = leaders[0] if len(leaders) == 1 else (cur if cur in leaders else None)
        self.s["camino_largo"] = cur
        for j in range(len(self.players)): self._check_win(j)

    def _check_win(self, i):
        if self.s["ganador"] is None and self.current() == i and self.points(i) >= self.s["meta"]:
            self.s["ganador"] = i; self.s["fase"] = "fin"
            self.log(f"🏆 ¡{self.players[i]['nombre']} gana con {self.points(i)} puntos!")

    # ---------- vistas ----------
    def public_view(self):
        """Todo lo que cualquier jugador puede ver (sin cartas ocultas)."""
        s = self.s; out = ["=== CATAN ==="]
        rows = [[0, 1, 2], [3, 4, 5, 6], [7, 8, 9, 10, 11], [12, 13, 14, 15], [16, 17, 18]]
        for row in rows:
            pad = " " * (5 - len(row)) * 7
            cells = []
            for k in row:
                lab = LABELS[k]; h = s["hexes"][lab]
                num = "--" if h["numero"] is None else f"{h['numero']:>2}"
                cells.append(f"{lab}{EMOJI[h['terreno']]}{num}{'🦹' if s['ladron'] == lab else '  '}")
            out.append(pad + "   ".join(cells))
        out.append("")
        for i, p in enumerate(s["jugadores"]):
            mark = "▶" if s["fase"] != "fin" and self.current() == i else " "
            al = sorted(int(v) for v, o in s["aldeas"].items() if o == i)
            ci = sorted(int(v) for v, o in s["ciudades"].items() if o == i)
            out.append(f"{mark} {p['nombre']} ({p['tipo']}): {self.points(i)} pts | cartas {sum(p['mano'].values())} | "
                       f"aldeas {al} ciudades {ci} | caminos {self.count('camino', i)} (largo {self.road_length(i)})"
                       + (" 🛣️+2" if s["camino_largo"] == i else ""))
        if s["fase"] == "colocacion":
            out.append(f"Fase: colocación inicial — {self.players[self.current()]['nombre']} pone aldea + camino")
        elif s["fase"] == "juego":
            out.append(f"Ronda {s['ronda']} — turno de {self.players[s['turno']]['nombre']}; "
                       + (f"dados {s['dados']}" if s["tirado"] else "aún no tira"))
            if s["pendiente"]:
                out.append(f"Pendiente: {s['pendiente']}")
        else:
            out.append(f"Fin: ganó {self.players[s['ganador']]['nombre']}")
        out.append("Últimos eventos: " + " | ".join(s["log"][-4:]))
        return "\n".join(out)

    def hand(self, name):
        p = self.players[self.idx(name)]
        return f"Mano de {p['nombre']}: " + ", ".join(f"{EMOJI[r]} {r} {c}" for r, c in p["mano"].items())

    def vertex_info(self, v):
        hs = ", ".join(f"{l}({self.s['hexes'][l]['terreno']} {self.s['hexes'][l]['numero'] or '-'})" for l in VHEX[v])
        return f"vértice {v}: {hs}; pips {self.vertex_pips(v)}"

    def vertex_pips(self, v):
        return sum(PIPS.get(self.s["hexes"][l]["numero"], 0) for l in VHEX[v] if l != self.s["ladron"])

    def legal_moves(self, name):
        """Opciones legales del jugador (solo usa información pública + su propia mano)."""
        i = self.idx(name); s = self.s; m = {}
        if s["fase"] == "colocacion":
            m["aldeas"] = [v for v in VHEX if self.can_settle(v)]
        elif s["fase"] == "juego":
            h = self.players[i]["mano"]
            afford = lambda k: all(h[r] >= c for r, c in COST[k].items()) and self.count(k, i) < LIMITS[k]
            m["caminos"] = [e for e in range(len(EDGES)) if self.can_road(e, i)] if afford("camino") else []
            m["aldeas"] = [v for v in VHEX if self.can_settle(v, i, True)] if afford("aldea") else []
            m["ciudades"] = [int(v) for v, o in s["aldeas"].items() if o == i] if afford("ciudad") else []
            m["comercio"] = [r for r in RES if h[r] >= 4]
        return m
