import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from catan.engine import Game, RuleError, VHEX, EDGES, ADJ, HEX_NB, edge_of
from catan import ai, cli
import simulate


class GraphTests(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(VHEX), 54); self.assertEqual(len(EDGES), 72)

    def test_no_adjacent_red_numbers(self):
        for seed in range(30):
            h = Game.new([("A", "ia"), ("B", "ia")], seed=seed).s["hexes"]
            for l, x in h.items():
                if x["numero"] in (6, 8):
                    self.assertFalse(any(h[n]["numero"] in (6, 8) for n in HEX_NB[l]))


class RuleTests(unittest.TestCase):
    def setUp(self):
        self.g = Game.new([("Ana", "humano"), ("NC", "bot"), ("IA1", "ia")], seed=1)

    def test_seats(self):
        with self.assertRaises(RuleError): Game.new([("A", "humano")])
        with self.assertRaises(RuleError): Game.new([("A", "x"), ("B", "ia")])
        with self.assertRaises(RuleError): Game.new([("A", "ia")] * 2)

    def test_distance_rule_and_turn_order(self):
        g = self.g; first = g.players[g.current()]["nombre"]
        v = 10; g.place(first, v, edge_of(v, ADJ[v][0]))
        nxt = g.players[g.current()]["nombre"]
        with self.assertRaises(RuleError): g.place(nxt, ADJ[v][0], edge_of(ADJ[v][0], ADJ[ADJ[v][0]][0]))
        with self.assertRaises(RuleError): g.place(first, 40, edge_of(40, ADJ[40][0]))

    def test_cannot_act_before_roll_and_seven(self):
        g = self.g
        while g.s["fase"] == "colocacion":
            v, e = ai.setup_move(g, g.players[g.current()]["nombre"]); g.place(g.players[g.current()]["nombre"], v, e)
        p = g.players[0]["nombre"]
        with self.assertRaises(RuleError): g.end_turn(p)
        g.players[1]["mano"]["madera"] = 9
        g.roll(p, dice=(3, 4))
        self.assertIn("1", g.s["pendiente"]["descartes"])
        with self.assertRaises(RuleError): g.move_robber(p, "A")
        g.discard(g.players[1]["nombre"], {"madera": g.s["pendiente"]["descartes"]["1"]})
        lab = next(l for l in g.s["hexes"] if l != g.s["ladron"])
        g.move_robber(p, lab); self.assertEqual(g.s["ladron"], lab)
        g.end_turn(p)

    def test_cost_enforced(self):
        g = self.g
        while g.s["fase"] == "colocacion":
            n = g.players[g.current()]["nombre"]; g.place(n, *ai.setup_move(g, n))
        p = g.players[0]; p["mano"] = {r: 0 for r in p["mano"]}
        g.roll(p["nombre"], dice=(1, 1)); p["mano"] = {r: 0 for r in p["mano"]}
        e = next(e for e in range(len(EDGES)) if g.can_road(e, 0))
        with self.assertRaises(RuleError): g.build(p["nombre"], "camino", e)
        p["mano"].update(madera=1, ladrillo=1); g.build(p["nombre"], "camino", e)
        self.assertEqual(p["mano"]["madera"], 0)

    def test_public_view_hides_hands(self):
        self.g.players[0]["mano"]["mineral"] = 3
        self.assertNotIn("mineral", self.g.public_view())


def _to_play(g):
    while g.s["fase"] == "colocacion":
        n = g.players[g.current()]["nombre"]; g.place(n, *ai.setup_move(g, n))
    p = g.players[0]; g.roll(p["nombre"], dice=(1, 1)); p["mano"] = {r: 0 for r in p["mano"]}
    return p


class HouseRuleTests(unittest.TestCase):
    def test_2to1_default_on(self):
        g = Game.new([("A", "humano"), ("B", "ia")], seed=2); p = _to_play(g)
        self.assertTrue(g.house_2to1())
        p["mano"]["trigo"] = 2; g.trade_bank(p["nombre"], "trigo", "madera", rate=2)
        self.assertEqual((p["mano"]["trigo"], p["mano"]["madera"]), (0, 1))
        with self.assertRaises(RuleError): g.trade_bank(p["nombre"], "madera", "trigo", rate=2)  # solo 1 carta
        with self.assertRaises(RuleError): g.trade_bank(p["nombre"], "oveja", "oveja", rate=2)

    def test_2to1_off(self):
        g = Game.new([("A", "humano"), ("B", "ia")], seed=2, house_2to1=False); p = _to_play(g)
        p["mano"]["trigo"] = 4
        with self.assertRaises(RuleError): g.trade_bank(p["nombre"], "trigo", "madera", rate=2)
        g.trade_bank(p["nombre"], "trigo", "madera")  # 4:1 sigue disponible
        self.assertEqual(g.legal_moves(p["nombre"])["comodin"], [])

    def test_2to1_only_own_turn_after_roll(self):
        g = Game.new([("A", "humano"), ("B", "humano")], seed=2); _to_play(g)
        other = g.players[1]; other["mano"]["trigo"] = 2
        with self.assertRaises(RuleError): g.trade_bank(other["nombre"], "trigo", "madera", rate=2)

    def test_ai_keeps_needed_cards(self):
        g = Game.new([("A", "ia"), ("B", "ia")], seed=2); p = _to_play(g)
        p["mano"].update(madera=1, ladrillo=1, oveja=1, trigo=0, mineral=3)
        ai._trade(g, p["nombre"], lambda m: None)
        self.assertEqual((p["mano"]["madera"], p["mano"]["ladrillo"], p["mano"]["oveja"]), (1, 1, 1))

    def test_cli_flag(self):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "p.json")
            cli.main(["--file", f, "nueva", "A:ia", "B:ia", "--sin-comodin"])
            self.assertFalse(Game.load(f).house_2to1())


class GameTests(unittest.TestCase):
    def test_full_games_end(self):
        for n in (2, 3, 4):
            for seed in range(5):
                g, _ = simulate.run(seed, n)
                self.assertIsNotNone(g.s["ganador"])
                g, _ = simulate.run(seed, n, house_2to1=False)
                self.assertIsNotNone(g.s["ganador"])
                self.assertGreaterEqual(g.points(g.s["ganador"]), 10)

    def test_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "p.json")
            self.assertEqual(cli.main(["--file", f, "nueva", "IA1:ia", "IA2:ia", "--seed", "3"]), 0)
            self.assertEqual(cli.main(["--file", f, "ia"]), 0)
            self.assertIsNotNone(Game.load(f).s["ganador"])


if __name__ == "__main__":
    unittest.main()
