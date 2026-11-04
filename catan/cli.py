"""CLI bilingüe / bilingual CLI:  python3 -m catan.cli [--lang es|en] [--file partida.json] <comando|command> ...

Los comandos en español y en inglés son equivalentes (nueva=new, tirar=roll, ...).
"""
import argparse, json, os, sys
from .engine import Game, RuleError, EDGES
from . import ai, i18n

# (canonical, english alias, help es, help en)
CMDS = [
    ("nueva", "new", "nueva partida: Nombre:tipo (humano|bot|ia)", "new game: Name:type (human|bot|ai)"),
    ("tablero", "board", "vista pública", "public view"),
    ("mano", "hand", "mano privada de un jugador", "a player's private hand"),
    ("opciones", "options", "jugadas legales", "legal moves"),
    ("vertice", "vertex", "info de vértice(s)", "vertex info"),
    ("arista", "edge", "vértices de una arista", "an edge's vertices"),
    ("colocar", "place", "colocación inicial: aldea + camino", "initial placement: settlement + road"),
    ("tirar", "roll", "tirar los dados", "roll the dice"),
    ("construir", "build", "construir camino|aldea|ciudad", "build road|settlement|city"),
    ("comerciar", "trade", "banco 4:1", "bank 4:1"),
    ("comodin", "wild", "regla de la casa: 2 iguales por 1 con el banco", "house rule: 2 of a kind for 1 with the bank"),
    ("descartar", "discard", 'descartar cartas, JSON: {"madera":2}', 'discard cards, JSON: {"wood":2}'),
    ("ladron", "robber", "mover el ladrón [y robar a víctima]", "move the robber [and steal from victim]"),
    ("terminar", "end", "terminar el turno", "end the turn"),
    ("ia", "ai", "juega los turnos IA seguidos hasta que toque a un humano/bot", "play AI turns until a human/bot must act"),
    ("idioma", "lang", "cambiar el idioma de la partida", "change the game's language"),
]
ALIAS = {en: es for es, en, *_ in CMDS}
ARG = {"jugador": "player", "vertice": "vertex", "camino": "road", "tipo": "type", "donde": "where",
       "doy": "give", "recibo": "get", "cartas": "cards", "hex": "hex", "victima": "victim", "asientos": "seats", "ids": "ids"}


def parse_seats(specs):
    out = []
    for sp in specs:
        name, _, t = sp.partition(":")
        out.append((name, t or "humano"))
    return out


def _pre_lang(argv):
    """Idioma para la ayuda/errores antes de parsear: --lang > archivo guardado > entorno."""
    lang, f = None, "partida.json"
    for k, a in enumerate(argv):
        if a == "--lang" and k + 1 < len(argv): lang = argv[k + 1]
        elif a.startswith("--lang="): lang = a.split("=", 1)[1]
        elif a == "--file" and k + 1 < len(argv): f = argv[k + 1]
        elif a.startswith("--file="): f = a.split("=", 1)[1]
    if lang in i18n.LANGS: return lang
    if os.path.exists(f):
        try:
            with open(f, encoding="utf-8") as fh: return i18n.norm_lang(json.load(fh).get("idioma", "es"))
        except (OSError, ValueError): pass
    return i18n.default_lang()


def build_parser(lang):
    en = lang == "en"
    A = (lambda n: ARG[n]) if en else (lambda n: n)
    ap = argparse.ArgumentParser(prog="catan", description=__doc__)
    ap.add_argument("--file", default="partida.json")
    ap.add_argument("--lang", choices=i18n.LANGS, help="es | en (default: save file, then $CATAN_LANG/$LANG, else en)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    P = {}
    for es, eng, hes, hen in CMDS:
        name, alias = (eng, es) if en else (es, eng)
        P[es] = sub.add_parser(name, aliases=[alias], help=hen if en else hes)
    P["nueva"].add_argument("asientos", nargs="+", metavar=A("asientos"))
    P["nueva"].add_argument("--seed", type=int); P["nueva"].add_argument("--meta", "--target", dest="meta", type=int, default=10)
    P["nueva"].add_argument("--sin-comodin", "--no-wild", dest="sin_comodin", action="store_true",
                            help="turn off the house 2:1 wild trade" if en else "desactiva el comodín 2:1 de la casa")
    for c in ("mano", "opciones", "tirar", "terminar"): P[c].add_argument("jugador", metavar=A("jugador"))
    P["vertice"].add_argument("ids", nargs="+", type=int); P["arista"].add_argument("ids", nargs="+", type=int)
    P["colocar"].add_argument("jugador", metavar=A("jugador")); P["colocar"].add_argument("vertice", type=int, metavar=A("vertice")); P["colocar"].add_argument("camino", type=int, metavar=A("camino"))
    P["construir"].add_argument("jugador", metavar=A("jugador")); P["construir"].add_argument("tipo", choices=sorted(i18n.KIND_ALIASES), metavar=A("tipo")); P["construir"].add_argument("donde", type=int, metavar=A("donde"))
    for c in ("comerciar", "comodin"):
        P[c].add_argument("jugador", metavar=A("jugador")); P[c].add_argument("doy", metavar=A("doy")); P[c].add_argument("recibo", metavar=A("recibo"))
    P["descartar"].add_argument("jugador", metavar=A("jugador")); P["descartar"].add_argument("cartas", metavar=A("cartas"))
    P["ladron"].add_argument("jugador", metavar=A("jugador")); P["ladron"].add_argument("hex"); P["ladron"].add_argument("victima", nargs="?", metavar=A("victima"))
    P["idioma"].add_argument("nuevo", choices=i18n.LANGS, metavar="es|en")
    return ap


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    lang = _pre_lang(argv)
    args = build_parser(lang).parse_args(argv)
    cmd = ALIAS.get(args.cmd, args.cmd)
    try:
        if cmd == "nueva":
            g = Game.new(parse_seats(args.asientos), seed=args.seed, target=args.meta,
                         house_2to1=not args.sin_comodin, lang=args.lang or i18n.default_lang())
            g.save(args.file); print(g.public_view()); return 0
        g = Game.load(args.file)
        if args.lang: g.set_lang(args.lang)
        lang = g.lang
        if cmd == "tablero": print(g.public_view())
        elif cmd == "mano": print(g.hand(args.jugador))
        elif cmd == "opciones": print(json.dumps(g.legal_moves(args.jugador)))
        elif cmd == "vertice":
            for i in args.ids: print(g.vertex_info(i))
        elif cmd == "arista":
            for i in args.ids: print(g.t("edge", i=i, v=EDGES[i]))
        elif cmd == "colocar": print(g.place(args.jugador, args.vertice, args.camino))
        elif cmd == "tirar": print(g.roll(args.jugador))
        elif cmd == "construir": print(g.build(args.jugador, args.tipo, args.donde))
        elif cmd == "comerciar": print(g.trade_bank(args.jugador, args.doy, args.recibo))
        elif cmd == "comodin": print(g.trade_bank(args.jugador, args.doy, args.recibo, rate=2))
        elif cmd == "descartar":
            try: cards = json.loads(args.cartas)
            except ValueError: raise RuleError("err_cards_json")
            if not isinstance(cards, dict): raise RuleError("err_cards_json")
            print(g.discard(args.jugador, cards))
        elif cmd == "ladron": print(g.move_robber(args.jugador, args.hex, args.victima))
        elif cmd == "terminar": print(g.end_turn(args.jugador))
        elif cmd == "idioma": g.set_lang(args.nuevo); print(g.t("lang_set"))
        elif cmd == "ia":
            ai.resolve_pending(g, print, ai_only=True)
            guard = 0
            while g.s["ganador"] is None and g.players[g.current()]["tipo"] == "ia" and guard < 500:
                before = len(g.s["log"])
                ai.play_turn(g, g.players[g.current()]["nombre"])
                guard += 1
                if g.s["pendiente"] or len(g.s["log"]) == before: break
            print("—"); print(g.public_view())
        g.save(args.file)
    except RuleError as e:
        print(f"❌ {e.text(lang)}", file=sys.stderr); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
