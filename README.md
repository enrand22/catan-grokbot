# 🎲 Catan for Grok Bot

🇲🇽 **[Leer en español → README.es.md](README.es.md)**

Play Catan in chat with your Grok Bot: 2 to 4 players, mixing **humans**, **your bot**, and **AI players**
the bot runs. For example: you + your bot + 2 AIs, or 1 human against 3 AIs.
No dependencies, just standard Python 3.9+. Fully bilingual (English / Spanish).
*Catan* is a trademark of its owners; this is a fan project.

## Install
1. Ask your Grok Bot to clone this repo onto its computer and save `SKILL.md` as a skill.
2. Say: "let's play Catan: me, you and 2 AIs".

## Language
`--lang en|es` when creating a game; it's stored in the save file. Without it, the game uses
`$CATAN_LANG`, then the system locale (`$LANG`…), and falls back to English. Switch mid-game with
`lang es` / `idioma en`. Commands and resource names work in **both** languages
(`roll`/`tirar`, `wood`/`madera`, `wheat`/`trigo`, `sheep`/`oveja`, `brick`/`ladrillo`, `ore`/`mineral`).

## Manual use
```bash
python3 -m catan.cli --lang en new Ann:human Bot:bot AI1:ai AI2:ai   # types: human | bot | ai
python3 -m catan.cli board               # public view
python3 -m catan.cli options Ann         # legal moves (vertex/edge ids)
python3 -m catan.cli vertex 12 20        # what a vertex touches
python3 -m catan.cli place Ann 12 17     # initial placement: settlement + road
python3 -m catan.cli roll Ann
python3 -m catan.cli build Ann settlement 20     # road | settlement | city
python3 -m catan.cli trade Ann sheep wheat       # bank 4:1
python3 -m catan.cli wild Ann wheat wood         # house rule 2:1
python3 -m catan.cli discard Ann '{"wood":2}'    # after a 7, if you hold more than 7 cards
python3 -m catan.cli robber Ann K Bot            # move the robber, steal from a player
python3 -m catan.cli end Ann
python3 -m catan.cli ai                  # play the AI turns
```
Rules: random board (no 6/8 next to each other), snake-order setup, robber with discards, roads,
settlements, cities, longest road (+2), and 10 points to win (`--target`). Not included:
development cards and harbors. Player-to-player trades are left out **on purpose** (see below).

### House rule: 2:1 wild trade (on by default)
On your own turn, after rolling, trade **2 of any one resource for 1 of any other** with the bank,
as many times as you like, no harbor needed. It exists because there is **no player-to-player
trading**: a human can never pressure the bot or the AIs into a trade they don't want, and trading
is still always possible. Bank 4:1 still works. To play without it: `new ... --no-wild`.

## Tests
```bash
python3 -m unittest discover -s tests
python3 simulate.py 200 4 en    # 200 AI-only games, 4 players, English
```

License: MIT.
