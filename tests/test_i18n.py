import io, json, os, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from catan.engine import Game, RuleError
from catan import ai, cli, i18n
import simulate


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def to_play(g):
    while g.s["fase"] == "colocacion":
        n = g.players[g.current()]["nombre"]; g.place(n, *ai.setup_move(g, n))


class LangTests(unittest.TestCase):
    def test_default_lang_env(self):
        with mock.patch.dict(os.environ, {"CATAN_LANG": "", "LC_ALL": "", "LC_MESSAGES": "", "LANG": "es_MX.UTF-8", "LANGUAGE": ""}):
            self.assertEqual(i18n.default_lang(), "es")
        with mock.patch.dict(os.environ, {"CATAN_LANG": "fr", "LC_ALL": "", "LC_MESSAGES": "", "LANG": "C", "LANGUAGE": ""}), \
             mock.patch("locale.getlocale", return_value=(None, None)):
            self.assertEqual(i18n.default_lang(), "en")

    def test_every_message_has_both_langs(self):
        for k, v in i18n.M.items():
            self.assertEqual(len(v), 2, k); self.assertTrue(all(v), k)

    def test_english_board_and_errors(self):
        g = Game.new([("Ann", "human"), ("NC", "bot"), ("Bot2", "ai")], seed=1, lang="en")
        self.assertEqual([p["tipo"] for p in sorted(g.players, key=lambda p: p["nombre"])], ["humano", "ia", "bot"])
        v = g.public_view()
        self.assertIn("Phase: initial placement", v); self.assertNotIn("aldea", v)
        try:
            g.roll(g.players[0]["nombre"])
        except RuleError as e:
            self.assertEqual(e.text("en"), "not in the play phase")
        to_play(g)
        p = g.players[0]["nombre"]; g.roll(p, dice=(1, 1))
        g.players[0]["mano"].update(trigo=2)
        msg = g.trade_bank(p, "wheat", "wood", rate=2)
        self.assertIn("trades 2 wheat for 1 wood", msg); self.assertIn("house 2:1", msg)
        self.assertIn("wood", g.hand(p))

    def test_old_save_defaults_to_spanish(self):
        g = Game.new([("A", "ia"), ("B", "ia")], seed=1, lang="en"); del g.s["idioma"]
        self.assertEqual(g.lang, "es")


class EnglishCliTests(unittest.TestCase):
    def test_english_commands(self):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "g.json")
            code, out, _ = run("--lang", "en", "--file", f, "new", "Me:human", "A1:ai", "--seed", "5")
            self.assertEqual(code, 0); self.assertIn("Phase: initial placement", out)
            self.assertEqual(json.load(open(f))["idioma"], "en")
            g = Game.load(f); first = g.players[g.current()]["nombre"]
            if first != "Me":
                run("--file", f, "ai")
            opts = json.loads(run("--file", f, "options", "Me")[1])
            v = opts["aldeas"][0]
            from catan.engine import ADJ, edge_of
            code, out, _ = run("--file", f, "place", "Me", str(v), str(edge_of(v, ADJ[v][0])))
            self.assertEqual(code, 0); self.assertIn("places a settlement", out)
            code, _, err = run("--file", f, "roll", "Me")
            self.assertEqual(code, 2); self.assertIn("not in the play phase", err)
            code, out, _ = run("--file", f, "board")
            self.assertIn("Recent events", out)

    def test_spanish_aliases_still_work_and_lang_switch(self):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "g.json")
            run("--lang", "es", "--file", f, "nueva", "A:ia", "B:ia", "--seed", "2")
            self.assertIn("Fase: colocación", run("--file", f, "tablero")[1])
            self.assertIn("Language: English", run("--file", f, "lang", "en")[1])
            self.assertIn("Phase: initial", run("--file", f, "tablero")[1])
            code, out, _ = run("--file", f, "ai")
            self.assertEqual(code, 0); self.assertIn("wins with", out)

    def test_no_wild_flag_english(self):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "g.json")
            run("--lang", "en", "--file", f, "new", "A:ai", "B:ai", "--no-wild")
            self.assertFalse(Game.load(f).house_2to1())

    def test_english_simulation_ends(self):
        for n in (2, 3, 4):
            g, _ = simulate.run(n, n, lang="en")
            self.assertIsNotNone(g.s["ganador"]); self.assertIn("wins with", g.s["log"][-1] + " ".join(g.s["log"]))


if __name__ == "__main__":
    unittest.main()
