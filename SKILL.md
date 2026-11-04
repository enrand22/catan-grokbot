---
name: catan
description: Run a game of Catan (2-4 players) in chat with any mix of humans, the user's Grok Bot, and AI seats the bot plays itself, in English or Spanish. Use when the user wants to play Catan / Colonos de Catán, or to start, continue, or show a game.
---

# Catan for Grok Bot

The rules engine is in this skill's folder (`catan/`, standard library only). The game state is one
JSON file. Never edit it by hand; always go through the CLI so the rules are enforced.

## Language
Play in the user's language: talk to them in it and create the game with `--lang en` or `--lang es`
to match. The choice is saved, so every board, message and error comes out in that language. In a
mixed group, use the language most players are writing in. Switch with `lang en|es` if they ask.
Commands and resource names are accepted in both languages (`roll`=`tirar`, `wood`=`madera`, ...).

## Setup
1. Copy the skill folder to the box (e.g. `/workspace/catan-grokbot`) and `cd` there.
2. Ask who's playing (2-4 seats) and each seat's type:
   - `human`: a person in the chat. They tell you their moves; you run the commands for them.
   - `bot`: you (the user's Grok Bot) playing as yourself, with your own judgment.
   - `ai`: an extra AI opponent played by the built-in `catan/ai.py` strategy.
3. `python3 -m catan.cli --lang en --file game.json new Ann:human NC:bot AI1:ai AI2:ai`
   (optional `--seed N`, `--target 10`, `--no-wild`). The seat order is shuffled; the board shows who starts.

## Each step (always pass the same `--file`)
- Show the board after every turn with `board` (public info only).
- The ▶ line shows whose turn it is. For an `ai` seat, run `ai`: it plays every AI turn in a row and
  stops when a human or the bot has to act. Paste the events into the chat.
- Human turn: `roll <player>`, then `build <player> road|settlement|city <id>`,
  `trade <player> <give> <get>` (bank 4:1), `wild <player> <give> <get>` (house 2:1),
  and `end <player>`. Initial placement: `place <player> <vertex> <road>`.
- On a 7: players holding more than 7 cards run `discard <player> '{"wood":2,...}'`, then the roller runs
  `robber <player> <HEX> [victim]`. If an AI was mid-turn, run `ai` again.
- To help people choose: `options <player>` lists legal vertex/edge ids, `vertex <id...>` shows
  which hexes and numbers a vertex touches, and `edge <id>` shows an edge's two vertices.
- Errors start with ❌ and change nothing. Explain the rule and ask again.

## House rule: 2:1 wild trade (on by default)
On their own turn, after rolling, any player may trade 2 of one resource for 1 of any other with the
bank, any number of times, no harbor needed. Why it exists: there is NO player-to-player trading, so
a human can't pressure the bot or an AI seat into a trade it doesn't want, and trading is always
still possible. You (the bot) never trade player-to-player, never accept or broker a trade between
players, and never move cards between hands. If someone proposes a trade, point them to `wild`.
Only turn it off if the players ask (`--no-wild`). The bank 4:1 trade works either way.

## Fair play (important)
- Hands are secret. Only `board` (card counts, never contents) goes to the group chat.
- Show `hand <player>` only to that player. Never reveal another player's hand.
- When you play your own `bot` seat, decide using only the public board, the log, and YOUR hand.
  Don't read other players' hands or the JSON to decide. Dice and steals come from the engine's
  RNG: never pass fixed dice or edit the state.
- `ai` seats are played only by `catan/ai.py`, which uses public info and its own hand.

## Saving
The JSON file is the save. To resume later, run `board` with the same `--file`.
Not included: development cards and harbors. Player-to-player trades are left out on purpose (see above).
