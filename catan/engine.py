"""Motor de Catan (versión base simplificada) — solo biblioteca estándar.

Reglas incluidas: tablero aleatorio de 19 hexágonos (sin 6/8 adyacentes), colocación
inicial en serpiente, dados, producción, ladrón (descarte con >7 cartas, mover, robar),
caminos, aldeas, ciudades, comercio con el banco 4:1, camino más largo (+2) y victoria
a 10 puntos (configurable). No incluye: cartas de desarrollo, puertos ni comercio entre
jugadores (ver README).
"""
import json, math, random
from collections import defaultdict
from . import i18n

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
    """Error de reglas con clave traducible: str(e) usa inglés; e.text(lang) localiza."""
    def __init__(self, key, **kw):
        self.key, self.kw = key, kw
        super().__init__(i18n.t("en", key, **kw))

    def text(self, lang):
        return i18n.t(lang, self.key, **self.kw)


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
        raise RuleError("err_not_connected", a=a, b=b)
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
    def new(cls, seats, seed=None, target=10, house_2to1=True, lang=None):
        """seats: lista de (nombre, tipo) con tipo en humano|bot|ia. 2 a 4 asientos."""
        if not 2 <= len(seats) <= 4:
            raise RuleError("err_players")
        names = [n for n, _ in seats]
        if len(set(names)) != len(names):
            raise RuleError("err_unique")
        if lang is None: lang = i18n.default_lang()
        if lang not in i18n.LANGS: raise RuleError("err_lang", l=lang)
        norm = []
        for nm, t in seats:
            if str(t).lower() not in i18n.SEAT_ALIASES: raise RuleError("err_seat", t=t)
            norm.append((nm, i18n.SEAT_ALIASES[str(t).lower()]))
        seats = norm
        rng = random.Random(seed)
        hexes = random_board(rng)
        desert = next(l for l, h in hexes.items() if h["terreno"] == "desierto")
        order = list(range(len(seats))); rng.shuffle(order)
        players = [{"nombre": seats[i][0], "tipo": seats[i][1], "mano": {r: 0 for r in RES}} for i in order]
        n = len(players)
        st = {
            "version": 1, "idioma": lang, "meta": target, "comodin_2a1": bool(house_2to1), "hexes": hexes, "ladron": desert,
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
    def lang(self):
        return i18n.norm_lang(self.s.get("idioma", "es"))  # partidas viejas eran en español

    def set_lang(self, lang):
        if lang not in i18n.LANGS: raise RuleError("err_lang", l=lang)
        self.s["idioma"] = lang

    def t(self, key, **kw):
        return i18n.t(self.lang, key, **kw)

    def kname(self, k):
        return i18n.kind(self.lang, k)

    @property
    def players(self):
        return self.s["jugadores"]

    def idx(self, name):
        for i, p in enumerate(self.players):
            if p["nombre"].lower() == str(name).lower():
                return i
        raise RuleError("err_no_player", n=name)

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
        if self.s["ganador"] is not None: raise RuleError("err_over")
        if self.s["fase"] != phase: raise RuleError("err_phase", p=i18n.phase(self.lang, phase))
        if self.current() != i: raise RuleError("err_turn", n=self.players[i]['nombre'])

    def _pay(self, i, cost):
        h = self.players[i]["mano"]
        if any(h[r] < c for r, c in cost.items()): raise RuleError("err_cost", c=i18n.fmt_res(self.lang, cost))
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
        if not self.can_settle(vertex): raise RuleError("err_place", v=vertex)
        if not (0 <= edge < len(EDGES)) or vertex not in EDGES[edge]: raise RuleError("err_road_touch")
        if str(edge) in self.s["caminos"]: raise RuleError("err_road_taken")
        self.s["aldeas"][str(vertex)] = i; self.s["caminos"][str(edge)] = i
        s = self.s; msg = self.t("place", n=self.players[i]['nombre'], v=vertex, e=edge)
        if s["paso_colocacion"] >= len(self.players):  # segunda ronda: cobra
            got = defaultdict(int)
            for lab in VHEX[vertex]:
                t = s["hexes"][lab]["terreno"]
                if t != "desierto": self.players[i]["mano"][t] += 1; got[t] += 1
            msg += self.t("place_got", g=i18n.fmt_res(self.lang, got))
        s["paso_colocacion"] += 1
        if s["paso_colocacion"] >= len(s["colocacion"]):
            s["fase"] = "juego"; s["turno"] = 0; s["ronda"] = 1
        return self.log(msg)

    # ---------- juego ----------
    def roll(self, name, dice=None):
        i = self.idx(name); self._check_turn(i, "juego")
        if self.s["tirado"]: raise RuleError("err_rolled")
        if self.s["pendiente"]: raise RuleError("err_pending")
        a, b = dice if dice else (self._rand(6) + 1, self._rand(6) + 1)
        t = a + b; self.s["tirado"] = True; self.s["dados"] = [a, b]
        msg = self.t("roll", n=self.players[i]['nombre'], a=a, b=b, t=t)
        if t == 7:
            disc = {str(j): sum(p["mano"].values()) // 2 for j, p in enumerate(self.players) if sum(p["mano"].values()) > 7}
            self.s["pendiente"] = {"descartes": disc, "mover_ladron": i}
            if disc: msg += self.t("must_discard", lst=", ".join(f"{self.players[int(j)]['nombre']} {n}" for j, n in disc.items()))
            msg += self.t("move_robber")
        else:
            gains = self._produce(t)
            msg += "; " + ("; ".join(self.t("gets", n=self.players[j]['nombre'], g=i18n.fmt_res(self.lang, g)) for j, g in gains.items()) or self.t("nobody"))
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
        if not p or str(i) not in p["descartes"]: raise RuleError("err_no_discard")
        need = p["descartes"][str(i)]
        try:
            cards = {i18n.RES_ALIASES[str(r).lower()]: int(c) for r, c in cards.items()}
        except (KeyError, ValueError, AttributeError):
            raise RuleError("err_cards_json")
        if sum(cards.values()) != need: raise RuleError("err_discard_n", n=need)
        self._pay(i, cards); del p["descartes"][str(i)]
        return self.log(self.t("discard", n=self.players[i]['nombre'], k=need))

    def move_robber(self, name, hexlab, victim=None):
        i = self.idx(name); p = self.s["pendiente"]
        if not p or p["mover_ladron"] != i: raise RuleError("err_not_robber")
        if p["descartes"]: raise RuleError("err_wait_discard", names=", ".join(self.players[int(j)]["nombre"] for j in p["descartes"]))
        hexlab = str(hexlab).upper()
        if hexlab not in self.s["hexes"] or hexlab == self.s["ladron"]: raise RuleError("err_hex")
        victims = self.robber_victims(i, hexlab)
        self.s["ladron"] = hexlab; self.s["pendiente"] = None
        msg = self.t("robber", n=self.players[i]['nombre'], h=hexlab)
        if victims:
            j = self.idx(victim) if victim is not None else victims[0]
            if j not in victims: raise RuleError("err_victim")
            pool = [r for r, c in self.players[j]["mano"].items() for _ in range(c)]
            if pool:
                r = pool[self._rand(len(pool))]
                self.players[j]["mano"][r] -= 1; self.players[i]["mano"][r] += 1
                msg += self.t("steal", v=self.players[j]['nombre'])  # recurso oculto
        return self.log(msg)

    def robber_victims(self, i, hexlab):
        return sorted({o for v in HEXV[hexlab] for o in [self.owner_v(v)] if o is not None and o != i
                       and sum(self.players[o]["mano"].values()) > 0})

    def _ready(self, i):
        self._check_turn(i, "juego")
        if not self.s["tirado"]: raise RuleError("err_roll_first")
        if self.s["pendiente"]: raise RuleError("err_robber_first")

    def build(self, name, kind, where):
        i = self.idx(name); self._ready(i); where = int(where)
        kind = i18n.KIND_ALIASES.get(str(kind).lower(), kind)
        if kind not in LIMITS: raise RuleError("err_kind")
        if self.count(kind, i) >= LIMITS[kind]: raise RuleError("err_pieces", k=self.kname(kind))
        if kind == "camino":
            if not self.can_road(where, i): raise RuleError("err_road", w=where)
            self._pay(i, COST[kind]); self.s["caminos"][str(where)] = i
        elif kind == "aldea":
            if not self.can_settle(where, i, need_road=True): raise RuleError("err_settle", w=where)
            self._pay(i, COST[kind]); self.s["aldeas"][str(where)] = i
        elif kind == "ciudad":
            if self.s["aldeas"].get(str(where)) != i: raise RuleError("err_city")
            self._pay(i, COST[kind]); del self.s["aldeas"][str(where)]; self.s["ciudades"][str(where)] = i
        else:
            raise RuleError("err_kind")
        msg = self.log(self.t("build", n=self.players[i]['nombre'], k=self.kname(kind), w=where))
        if kind != "ciudad": self._update_longest()
        self._check_win(i)
        return msg

    def house_2to1(self):
        return self.s.get("comodin_2a1", True)

    def best_rate(self):
        return 2 if self.house_2to1() else 4

    def trade_bank(self, name, give, get, rate=4):
        """Comercio con el banco, solo en tu turno y después de tirar. rate 4 (siempre) o 2 (comodín de la casa)."""
        i = self.idx(name); self._ready(i)
        give = i18n.RES_ALIASES.get(str(give).lower(), give); get = i18n.RES_ALIASES.get(str(get).lower(), get)
        if rate not in (2, 4): raise RuleError("err_rate")
        if rate == 2 and not self.house_2to1(): raise RuleError("err_wild_off")
        if give not in RES or get not in RES or give == get: raise RuleError("err_res")
        self._pay(i, {give: rate}); self.players[i]["mano"][get] += 1
        tag = self.t("wild_tag") if rate == 2 else ""
        return self.log(self.t("trade", n=self.players[i]['nombre'], r=rate, g=i18n.res(self.lang, give), x=i18n.res(self.lang, get)) + tag)

    def end_turn(self, name):
        i = self.idx(name); self._ready(i)
        self.s["turno"] = (i + 1) % len(self.players); self.s["tirado"] = False; self.s["dados"] = None
        if self.s["turno"] == 0: self.s["ronda"] += 1
        return self.log(self.t("end", n=self.players[i]['nombre'], m=self.players[self.s['turno']]['nombre']))

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
            self.log(self.t("win", n=self.players[i]['nombre'], p=self.points(i)))

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
            out.append(self.t("row_player", mark=mark, n=p['nombre'], t=i18n.seat(self.lang, p['tipo']), p=self.points(i),
                              c=sum(p['mano'].values()), a=al, ci=ci, r=self.count('camino', i), L=self.road_length(i))
                       + (" 🛣️+2" if s["camino_largo"] == i else ""))
        if s["fase"] == "colocacion":
            out.append(self.t("phase_setup", n=self.players[self.current()]['nombre']))
        elif s["fase"] == "juego":
            out.append(self.t("trade_line", w=self.t("trade_wild") if self.house_2to1() else ""))
            out.append(self.t("round", r=s['ronda'], n=self.players[s['turno']]['nombre'],
                              d=self.t("dice", d=s['dados']) if s["tirado"] else self.t("not_rolled")))
            if s["pendiente"]:
                pd = s['pendiente']
                out.append(self.t("pending", d={self.players[int(j)]['nombre']: n for j, n in pd['descartes'].items()},
                                  n=self.players[pd['mover_ladron']]['nombre']))
        else:
            out.append(self.t("over", n=self.players[s['ganador']]['nombre']))
        out.append(self.t("recent") + " | ".join(s["log"][-4:]))
        return "\n".join(out)

    def hand(self, name):
        p = self.players[self.idx(name)]
        return self.t("hand", n=p['nombre']) + ", ".join(f"{EMOJI[r]} {i18n.res(self.lang, r)} {c}" for r, c in p["mano"].items())

    def vertex_info(self, v):
        hs = ", ".join(f"{l}({i18n.res(self.lang, self.s['hexes'][l]['terreno'])} {self.s['hexes'][l]['numero'] or '-'})" for l in VHEX[v])
        return self.t("vertex", v=v, h=hs, p=self.vertex_pips(v))

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
            m["comodin"] = [r for r in RES if h[r] >= 2] if self.house_2to1() else []
        return m
