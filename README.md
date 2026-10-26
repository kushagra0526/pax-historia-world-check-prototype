# worldcheck: do an AI game master's turn summaries agree with the world state?

Pax Historia is an AI-powered alternate-history sandbox where players publish their own worlds (https://www.paxhistoria.co/); its YC page reports 35k daily users and 100B+ tokens a week, and it is hiring for LLM infrastructure and "harness optimization". When a model narrates what happens after a player's move, the story can quietly contradict the world it is supposed to describe: a province changes hands that its owner never held, a dead ruler gives an order, an ally is attacked with no treaty broken, airplanes appear in 1790. This prototype is a validator that reads a turn's narration against the world state before the turn.

## What it does
`worldcheck/world.py`: a tiny world (nations, provinces and owners, leaders alive or dead, alliances, wars, the year) and a checker. It parses each sentence into a claim (capture, declare war, sign or break an alliance, leader dies or acts, deploys a technology, fields troops), tests it against the state *before* the turn, applies the valid ones in order, and returns violations with a code: `NOT_AT_WAR`, `WRONG_OWNER`, `ATTACKS_ALLY`, `DEAD_LEADER_ACTS`, `ELIMINATED_NATION_ACTS`, `ANACHRONISM`, `NO_SUCH_ALLIANCE`, `ALLIANCE_WHILE_AT_WAR`. Sentences it cannot parse are returned as `unparsed`, never silently accepted.

## Results (simulated games of 14 turns; planted errors at the start of the turn so their label comes from the state, not the checker)
Dev: 200 games, 2,147 planted errors, 12,470 valid sentences. Held-out: 200 games with 8 error codes (two new) and paraphrases the parser had not seen (`wrests ... from`, `falls to ..., taken from`, `goes to war with`, `A and B sign an alliance`, `ends its alliance with`), earlier years (1620-1880); fixed in git before the first run.

| | sentence-by-sentence checks (year and troops only) | worldcheck dev | worldcheck held-out run 1 | held-out run 2 (parser extended) |
|---|---|---|---|---|
| planted errors found with the right code | 400 / 2,147 (dev), 338 / 2,159 (held-out) | **2,147 / 2,147** | 1,481 / 2,159 | **2,253 / 2,253** |
| valid sentences flagged | 0 | 0 | 0 | 0 |
| sentences it could not read | - | 0 | **4,693** (678 of them planted errors) | 0 |

- A sentence-level check, which has no world state, finds only the anachronisms (about 1 in 5).
- Run 1 on unseen phrasings: 69% of planted errors found with no false flags, but 4,693 sentences were unread (about 32% of all sentences); because unread sentences also do not update the state, later turns drift (missed ownership changes, wars and alliances), which is how 678 planted errors in unread sentences plus others were missed. The right behaviour for a validator is to report "unread", not "fine"; the 4,693 are in the output.
- I extended the parser with the five new phrasings and re-ran (run 1 output in `out/first_run.txt`).

## Read this before believing the table
The narration is generated from templates and parsed with regular expressions, so run 2 is close to circular: I wrote both sides, and the held-out games of run 2 differ from run 1 because my game generator also uses the parser to keep its valid sentences valid. Real LLM narration is free text, so the claims would have to come from structured output or an extraction model, and real worlds have far more state (treaties, vassals, resources, borders). Nothing here uses Pax Historia data, prompts or systems.

## Run it (3 commands)
```
pip install pytest
python -m pytest -q tests
python -m worldcheck.run
```
Standard library only. 4 tests.

Unofficial prototype by Kushagra Pratap Singh. Not affiliated with Pax Historia.
