# 🎲 Catan para Grok Bot

Juega Colonos de Catán en el chat con tu Grok Bot: de 2 a 4 jugadores, mezclando **humanos**,
**tu bot** y **IAs** que el bot controla. Por ejemplo: tú + tu bot + 2 IAs, o 1 humano contra 3 IAs.
Sin dependencias: solo Python 3.9+ estándar. *Catan* es marca de sus dueños; este es un proyecto de fans.

## Instalación
1. Pídele a tu Grok Bot que clone este repositorio en su compu y lo guarde como skill (`SKILL.md`).
2. Dile: "juguemos Catan: yo, tú y 2 IAs".

## Uso manual
```bash
python3 -m catan.cli nueva Ana:humano Bot:bot IA1:ia IA2:ia   # tipos: humano | bot | ia
python3 -m catan.cli tablero            # vista pública
python3 -m catan.cli opciones Ana       # jugadas legales (ids de vértices/aristas)
python3 -m catan.cli colocar Ana 12 17  # colocación inicial: aldea + camino
python3 -m catan.cli tirar Ana
python3 -m catan.cli construir Ana aldea 20
python3 -m catan.cli comerciar Ana oveja trigo   # banco 4:1
python3 -m catan.cli comodin Ana trigo madera  # regla de la casa 2:1
python3 -m catan.cli terminar Ana
python3 -m catan.cli ia                 # juega los turnos de las IAs
```
### Regla de la casa: comodín 2:1 (activada por defecto)
En tu turno, después de tirar, puedes cambiar **2 cartas iguales de cualquier recurso por 1 de otro**
con el banco, sin puertos y sin límite de veces. Existe porque **no hay trueque entre jugadores**: así
un humano no puede presionar al bot o a las IAs a un intercambio que no quieren, y aun así siempre hay
comercio. El banco 4:1 sigue disponible. Para jugar sin la regla: `nueva ... --sin-comodin`.

Reglas: tablero aleatorio (sin 6/8 juntos), colocación en serpiente, ladrón con descarte, caminos,
aldeas, ciudades, camino más largo y victoria a 10 puntos (`--meta`). No incluye cartas de
desarrollo ni puertos, y a propósito no hay intercambio entre jugadores.

## Pruebas
```bash
python3 -m unittest discover -s tests
python3 simulate.py 100 4    # 100 partidas solo de IAs
```

---

## English
Play Catan in chat with your Grok Bot: 2-4 seats mixing humans, your bot, and AI players the bot runs.
Standard-library Python only. Install by asking your Grok Bot to clone this repo and save `SKILL.md`
as a skill, then say "let's play Catan: me, you and 2 AIs". Commands are in Spanish (see above;
`nueva`=new, `tablero`=board, `tirar`=roll, `construir`=build, `comerciar`=bank trade, `terminar`=end turn,
`ia`=play AI turns). Hands stay private; the bot and AIs play only from public info plus their own hand.
**House rule: 2:1 wildcard trade (on by default).** On your turn, after rolling, trade 2 of any one
resource for 1 of any other with the bank, as often as you like (`comodin <player> <give> <get>`).
It exists because there are no player-to-player trades: a human can never pressure the bot or AIs
into a trade they don't want, yet trading is always possible. Bank 4:1 still works. Turn it off with
`nueva ... --sin-comodin`. Not included: development cards, harbors. License: MIT.
