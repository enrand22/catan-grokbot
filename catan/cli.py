"""CLI: python3 -m catan.cli <comando> ...   (estado en --file, por defecto partida.json)"""
import argparse, json, sys
from .engine import Game, RuleError, VHEX, EDGES
from . import ai


def parse_seats(specs):
    seats = []
    for sp in specs:
        name, _, t = sp.partition(":")
        seats.append((name, t or "humano"))
    return seats


def main(argv=None):
    ap = argparse.ArgumentParser(prog="catan")
    ap.add_argument("--file", default="partida.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("nueva", help="nueva partida: Nombre:tipo (humano|bot|ia)")
    n.add_argument("asientos", nargs="+"); n.add_argument("--seed", type=int); n.add_argument("--meta", type=int, default=10)
    n.add_argument("--sin-comodin", action="store_true", help="desactiva el comercio comodín 2:1 de la casa")
    sub.add_parser("tablero", help="vista pública")
    h = sub.add_parser("mano", help="mano privada de un jugador"); h.add_argument("jugador")
    o = sub.add_parser("opciones", help="jugadas legales"); o.add_argument("jugador")
    v = sub.add_parser("vertice", help="info de vértice(s)"); v.add_argument("ids", nargs="+", type=int)
    a = sub.add_parser("arista", help="vértices de una arista"); a.add_argument("ids", nargs="+", type=int)
    c = sub.add_parser("colocar"); c.add_argument("jugador"); c.add_argument("vertice", type=int); c.add_argument("camino", type=int)
    t = sub.add_parser("tirar"); t.add_argument("jugador")
    b = sub.add_parser("construir"); b.add_argument("jugador"); b.add_argument("tipo", choices=["camino", "aldea", "ciudad"]); b.add_argument("donde", type=int)
    cm = sub.add_parser("comerciar"); cm.add_argument("jugador"); cm.add_argument("doy"); cm.add_argument("recibo")
    cz = sub.add_parser("comodin", help="regla de la casa: 2 de un recurso por 1 de otro con el banco"); cz.add_argument("jugador"); cz.add_argument("doy"); cz.add_argument("recibo")
    d = sub.add_parser("descartar"); d.add_argument("jugador"); d.add_argument("cartas", help='JSON, ej. {"madera":2}')
    l = sub.add_parser("ladron"); l.add_argument("jugador"); l.add_argument("hex"); l.add_argument("victima", nargs="?")
    f = sub.add_parser("terminar"); f.add_argument("jugador")
    sub.add_parser("ia", help="juega los turnos IA seguidos hasta que toque a un humano/bot")
    args = ap.parse_args(argv)

    try:
        if args.cmd == "nueva":
            g = Game.new(parse_seats(args.asientos), seed=args.seed, target=args.meta, house_2to1=not args.sin_comodin)
            g.save(args.file); print(g.public_view()); return 0
        g = Game.load(args.file)
        cmd = args.cmd
        if cmd == "tablero": print(g.public_view())
        elif cmd == "mano": print(g.hand(args.jugador))
        elif cmd == "opciones": print(json.dumps(g.legal_moves(args.jugador)))
        elif cmd == "vertice":
            for i in args.ids: print(g.vertex_info(i))
        elif cmd == "arista":
            for i in args.ids: print(f"arista {i}: vértices {EDGES[i]}")
        elif cmd == "colocar": print(g.place(args.jugador, args.vertice, args.camino))
        elif cmd == "tirar": print(g.roll(args.jugador))
        elif cmd == "construir": print(g.build(args.jugador, args.tipo, args.donde))
        elif cmd == "comerciar": print(g.trade_bank(args.jugador, args.doy, args.recibo))
        elif cmd == "comodin": print(g.trade_bank(args.jugador, args.doy, args.recibo, rate=2))
        elif cmd == "descartar": print(g.discard(args.jugador, json.loads(args.cartas)))
        elif cmd == "ladron": print(g.move_robber(args.jugador, args.hex, args.victima))
        elif cmd == "terminar": print(g.end_turn(args.jugador))
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
        print(f"❌ {e}", file=sys.stderr); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
