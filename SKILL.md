---
name: catan
description: Run a game of Catan (2-4 players) in chat with any mix of humans, the user's Grok Bot, and AI seats the bot plays itself. Use when the user wants to play Catan / Colonos de Catán, start, continue, or show a game.
---

# Catan en Grok Bot

The rules engine lives in this skill's folder (`catan/`, standard library only). The game state is one
JSON file; never edit it by hand, always go through the CLI so the rules are enforced.

## Setup
1. Copy the skill folder to the box (e.g. `/workspace/catan-grokbot`) and `cd` there.
2. Ask who plays (2-4 seats) and each seat's type:
   - `humano`: a person in the chat. They tell you their moves; you run the commands for them.
   - `bot`: you (the user's Grok Bot) playing as yourself, with your own judgment.
   - `ia`: an extra AI opponent played by the built-in `catan/ai.py` strategy.
3. `python3 -m catan.cli --file partida.json nueva Henry:humano NC:bot IA1:ia IA2:ia`
   (optional `--seed N`, `--meta 10`). Seat order is shuffled; the board output shows who starts.

## Each step
- Show the board after every turn: `python3 -m catan.cli tablero` (public info only).
- Whose turn: the ▶ line. If it is an `ia` seat, run `python3 -m catan.cli ia` — it plays every
  consecutive AI turn and stops when a human/bot must act. Paste the events to the chat.
- Human turn: `tirar <jugador>`, then their choices with `construir <jugador> camino|aldea|ciudad <id>`,
  `comerciar <jugador> <doy> <recibo>` (bank 4:1), `comodin <jugador> <doy> <recibo>` (house 2:1),
  and `terminar <jugador>`.
  Initial placement: `colocar <jugador> <vertice> <camino>`.
- On a 7: players with >7 cards `descartar <jugador> '{"madera":2,...}'`; then the roller does
  `ladron <jugador> <HEX> [victima]`. Then run `ia` again if an AI was mid-turn.
- Help people choose: `opciones <jugador>` lists legal vertex/edge ids; `vertice <id...>` describes
  which hexes and numbers a vertex touches; `arista <id>` shows an edge's two vertices.
- Errors start with ❌ and nothing changes; explain the rule and ask again.

## Fair play (important)
- Hands are secret. Only `tablero` (card counts, never contents) goes to the group chat.
- Show `mano <jugador>` only to that player. In a shared chat, tell humans to keep their own count
  or send their hand privately if the channel allows; never reveal another player's hand.
- When you play your own `bot` seat, decide using only the public board, the log, and YOUR hand.
  Do not read other players' `mano` or the JSON hands to decide. Dice and steals come from the
  engine's RNG — never pass fixed dice (`dice=`) or edit the state.
- `ia` seats are played only by `catan/ai.py`, which uses public info and its own hand.

## House rule: comodín 2:1 (on by default)
On their own turn, after rolling, any player may trade 2 of one resource for 1 of any other with the
bank, any number of times, no harbor needed. Why: there is NO player-to-player trading, so a human
can't pressure the bot or an AI seat into a trade it doesn't want, and trade is still always
available. You (the bot) never trade player-to-player, never accept or broker a trade between
players, and never move cards between hands; if someone proposes one, point them to `comodin`.
Disable only if the players ask: `nueva ... --sin-comodin` (bank 4:1 remains either way).

## Saving
The JSON file is the save. To resume later, just run `tablero` with the same `--file`.
Not included: development cards and harbors. Player-to-player trades are left out on purpose (see above).
