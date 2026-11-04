"""Textos en español e inglés. Las claves internas del estado siguen en español."""
import locale, os

LANGS = ("es", "en")
RES_NAMES = {
    "es": {"madera": "madera", "ladrillo": "ladrillo", "oveja": "oveja", "trigo": "trigo", "mineral": "mineral", "desierto": "desierto"},
    "en": {"madera": "wood", "ladrillo": "brick", "oveja": "sheep", "trigo": "wheat", "mineral": "ore", "desierto": "desert"},
}
KIND_NAMES = {"es": {"camino": "camino", "aldea": "aldea", "ciudad": "ciudad"},
              "en": {"camino": "road", "aldea": "settlement", "ciudad": "city"}}
PHASE_NAMES = {"es": {"colocacion": "colocación", "juego": "juego", "fin": "fin"},
               "en": {"colocacion": "placement", "juego": "play", "fin": "game over"}}
SEAT_NAMES = {"es": {"humano": "humano", "bot": "bot", "ia": "ia"}, "en": {"humano": "human", "bot": "bot", "ia": "ai"}}

# entrada aceptada en ambos idiomas -> clave interna
RES_ALIASES = {"madera": "madera", "wood": "madera", "lumber": "madera", "ladrillo": "ladrillo", "brick": "ladrillo",
               "oveja": "oveja", "sheep": "oveja", "wool": "oveja", "trigo": "trigo", "wheat": "trigo", "grain": "trigo",
               "mineral": "mineral", "ore": "mineral"}
KIND_ALIASES = {"camino": "camino", "road": "camino", "aldea": "aldea", "settlement": "aldea", "ciudad": "ciudad", "city": "ciudad"}
SEAT_ALIASES = {"humano": "humano", "human": "humano", "bot": "bot", "ia": "ia", "ai": "ia"}

M = {
 "err_not_connected": ("los vértices {a} y {b} no están conectados", "vertices {a} and {b} are not connected"),
 "err_players": ("se necesitan de 2 a 4 jugadores", "2 to 4 players are required"),
 "err_unique": ("los nombres deben ser únicos", "player names must be unique"),
 "err_seat": ("tipo inválido {t!r}; usa humano | bot | ia", "invalid seat type {t!r}; use human | bot | ai"),
 "err_lang": ("idioma inválido {l!r}; usa es | en", "invalid language {l!r}; use es | en"),
 "err_no_player": ("no existe el jugador {n!r}", "no player named {n!r}"),
 "err_over": ("la partida ya terminó", "the game is over"),
 "err_phase": ("no estamos en fase {p}", "not in the {p} phase"),
 "err_turn": ("no es turno de {n}", "it is not {n}'s turn"),
 "err_cost": ("faltan recursos: cuesta {c}", "not enough resources: costs {c}"),
 "err_place": ("no se puede poner aldea en {v} (ocupado o regla de distancia)", "can't place a settlement on {v} (taken or distance rule)"),
 "err_road_touch": ("el camino debe tocar la aldea nueva", "the road must touch the new settlement"),
 "err_road_taken": ("camino ocupado", "that road is taken"),
 "err_rolled": ("ya tiraste los dados este turno", "you already rolled this turn"),
 "err_pending": ("hay una acción pendiente del ladrón", "a robber action is pending"),
 "err_no_discard": ("no tienes que descartar", "you don't need to discard"),
 "err_discard_n": ("debes descartar exactamente {n}", "you must discard exactly {n}"),
 "err_not_robber": ("no te toca mover el ladrón", "it's not your job to move the robber"),
 "err_wait_discard": ("faltan descartes de: {names}", "still waiting for discards from: {names}"),
 "err_hex": ("hexágono inválido (debe ser otro)", "invalid hex (must be a different one)"),
 "err_victim": ("esa víctima no tiene edificio en el hexágono", "that player has no building on that hex"),
 "err_roll_first": ("primero tira los dados", "roll the dice first"),
 "err_robber_first": ("resuelve primero el ladrón", "resolve the robber first"),
 "err_pieces": ("ya no te quedan piezas de {k}", "you have no {k} pieces left"),
 "err_road": ("camino {w} no es legal", "road {w} is not legal"),
 "err_settle": ("aldea en {w} no es legal", "settlement on {w} is not legal"),
 "err_city": ("la ciudad debe reemplazar una aldea tuya", "a city must replace one of your settlements"),
 "err_kind": ("tipo de construcción: camino | aldea | ciudad", "build type: road | settlement | city"),
 "err_rate": ("tasa inválida", "invalid rate"),
 "err_wild_off": ("el comodín 2:1 está desactivado en esta partida", "the 2:1 wild trade is off in this game"),
 "err_res": ("recursos inválidos", "invalid resources"),
 "err_cards_json": ("cartas inválidas; usa JSON, ej. {{\"madera\":2}}", "invalid cards; use JSON, e.g. {{\"wood\":2}}"),
 "place": ("{n} coloca aldea en {v} y camino {e}", "{n} places a settlement on {v} and road {e}"),
 "place_got": (" y recibe {g}", " and receives {g}"),
 "roll": ("{n} tira {a}+{b}={t}", "{n} rolls {a}+{b}={t}"),
 "must_discard": ("; deben descartar: {lst}", "; must discard: {lst}"),
 "move_robber": ("; mueve el ladrón", "; move the robber"),
 "gets": ("{n} recibe {g}", "{n} receives {g}"),
 "nobody": ("nadie cobra", "nobody collects"),
 "discard": ("{n} descarta {k} cartas", "{n} discards {k} cards"),
 "robber": ("{n} mueve el ladrón a {h}", "{n} moves the robber to {h}"),
 "steal": (" y roba 1 carta a {v}", " and steals 1 card from {v}"),
 "build": ("{n} construye {k} en {w}", "{n} builds a {k} on {w}"),
 "trade": ("{n} cambia {r} {g} por 1 {x} con el banco", "{n} trades {r} {g} for 1 {x} with the bank"),
 "wild_tag": (" (comodín 2:1 de la casa)", " (house 2:1 wild trade)"),
 "end": ("{n} termina su turno → {m}", "{n} ends the turn → {m}"),
 "win": ("🏆 ¡{n} gana con {p} puntos!", "🏆 {n} wins with {p} points!"),
 "row_player": ("{mark} {n} ({t}): {p} pts | cartas {c} | aldeas {a} ciudades {ci} | caminos {r} (largo {L})",
                "{mark} {n} ({t}): {p} pts | cards {c} | settlements {a} cities {ci} | roads {r} (longest {L})"),
 "phase_setup": ("Fase: colocación inicial — {n} pone aldea + camino", "Phase: initial placement — {n} places a settlement + road"),
 "trade_line": ("Comercio: banco 4:1{w}; sin trueque entre jugadores", "Trading: bank 4:1{w}; no player-to-player trades"),
 "trade_wild": (" + comodín 2:1 (regla de la casa)", " + 2:1 wild trade (house rule)"),
 "round": ("Ronda {r} — turno de {n}; {d}", "Round {r} — {n}'s turn; {d}"),
 "dice": ("dados {d}", "dice {d}"),
 "not_rolled": ("aún no tira", "hasn't rolled yet"),
 "pending": ("Pendiente: descartes {d}; mueve el ladrón {n}", "Pending: discards {d}; {n} moves the robber"),
 "over": ("Fin: ganó {n}", "Game over: {n} won"),
 "recent": ("Últimos eventos: ", "Recent events: "),
 "hand": ("Mano de {n}: ", "{n}'s hand: "),
 "vertex": ("vértice {v}: {h}; pips {p}", "vertex {v}: {h}; pips {p}"),
 "edge": ("arista {i}: vértices {v}", "edge {i}: vertices {v}"),
 "ai_wait": ("⏸️ Esperando a que los humanos resuelvan descartes/ladrón; luego vuelve a ejecutar `ia`.",
             "⏸️ Waiting for humans to resolve discards/robber; then run `ai` again."),
 "lang_set": ("Idioma: español", "Language: English"),
}


def default_lang():
    for var in ("CATAN_LANG", "LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        v = os.environ.get(var, "")
        if v[:2].lower() in LANGS: return v[:2].lower()
    try:
        loc = (locale.getlocale()[0] or "")[:2].lower()
        if loc in LANGS: return loc
    except Exception:
        pass
    return "en"


def norm_lang(lang):
    return lang if lang in LANGS else "en"


def t(lang, key, **kw):
    es, en = M[key]
    return (en if norm_lang(lang) == "en" else es).format(**kw)


def res(lang, r): return RES_NAMES[norm_lang(lang)].get(r, r)
def kind(lang, k): return KIND_NAMES[norm_lang(lang)].get(k, k)
def phase(lang, p): return PHASE_NAMES[norm_lang(lang)].get(p, p)
def seat(lang, s): return SEAT_NAMES[norm_lang(lang)].get(s, s)
def fmt_res(lang, d): return "{" + ", ".join(f"{res(lang, r)}: {c}" for r, c in d.items()) + "}"
