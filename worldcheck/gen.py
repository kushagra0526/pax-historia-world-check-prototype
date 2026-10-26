"""A random valid alternate-history game, narrated sentence by sentence, with planted narration errors that have known codes."""
import random

from .world import World

NATIONS = ["France", "Spain", "Austria", "Prussia", "Russia", "Britain", "Ottoman Empire", "Sweden"]
LEADERS = ["Louis", "Carlos", "Franz", "Wilhelm", "Nikolai", "Edward", "Selim", "Gustav"]
PROVS = ["Lorraine", "Catalonia", "Bohemia", "Silesia", "Crimea", "Wales", "Thrace", "Scania", "Alsace", "Galicia", "Savoy", "Pomerania", "Kent", "Epirus", "Livonia", "Aragon"]
NARR_ALT = {"capture": ["{a} captures {p} from {b}.", "{a} seizes {p} from {b}.", "{a} annexes {p} from {b}."],
            "war": ["{a} declares war on {b}."], "alliance": ["{a} signs an alliance with {b}."], "break": ["{a} breaks its alliance with {b}."]}
HELD_ALT = {"capture": ["{a} wrests {p} from {b}.", "{p} falls to {a}, taken from {b}."], "war": ["{a} goes to war with {b}."],
            "alliance": ["{a} and {b} sign an alliance."], "break": ["{a} ends its alliance with {b}."]}


def start(rng, year):
    names = rng.sample(NATIONS, 5)
    provs = rng.sample(PROVS, 12)
    owners = {p: names[i % 5] for i, p in enumerate(provs)}
    nations = {n: {"alive": True, "allies": set(), "wars": set()} for n in names}
    leaders = {LEADERS[NATIONS.index(n)]: (n, True) for n in names}
    return World(year, nations, owners, leaders), names


def valid_sentence(rng, w, names, alt):
    alive = [n for n in names if w.nations[n]["alive"]]
    a = rng.choice(alive)
    kind = rng.choices(["war", "capture", "alliance", "break", "leader_acts", "tech", "troops"], [2, 4, 2, 1, 2, 1, 1])[0]
    st = w.nations[a]
    if kind == "war":
        c = [n for n in alive if n != a and n not in st["allies"] and n not in st["wars"]]
        return ("war", {"a": a, "b": rng.choice(c)}) if c else None
    if kind == "capture":
        c = [(p, o) for p, o in w.owners.items() if o in st["wars"] and w.nations[o]["alive"]]
        if not c:
            return None
        p, b = rng.choice(c)
        return "capture", {"a": a, "p": p, "b": b}
    if kind == "alliance":
        c = [n for n in alive if n != a and n not in st["allies"] and n not in st["wars"]]
        return ("alliance", {"a": a, "b": rng.choice(c)}) if c else None
    if kind == "break":
        return ("break", {"a": a, "b": rng.choice(sorted(st["allies"]))}) if st["allies"] else None
    if kind == "leader_acts":
        l = [l for l, (n, ok) in w.leaders.items() if n == a and ok]
        return ("leader_acts", {"l": l[0], "a": a, "what": rng.choice(["the council", "the fleet", "the army"])}) if l else None
    if kind == "tech":
        t = rng.choice(["railways", "telegraph", "machine guns", "airplanes"])
        from .world import TECH_YEAR
        return ("tech", {"a": a, "t": t}) if w.year >= TECH_YEAR[t] else None
    return "troops", {"a": a, "n": str(rng.randint(10, 90) * 1000)}


def render(kind, g, alt, rng):
    if kind == "leader_acts":
        return f"{g['l']} of {g['a']} {rng.choice(['addresses', 'reviews', 'orders'])} the {g['what'].replace('the ', '')}."
    if kind == "tech":
        return f"{g['a']} deploys {g['t']}."
    if kind == "troops":
        return f"{g['a']} fields {g['n']} troops."
    return rng.choice(alt[kind]).format(**{**g, "p": g.get("p", "")})


def plant(rng, w, names, kind_pool):
    """Returns (kind, fields, code) for a sentence the world does not support."""
    alive = [n for n in names if w.nations[n]["alive"]]
    a = rng.choice(alive)
    code = rng.choice(kind_pool)
    others = [n for n in alive if n != a]
    if code == "NOT_AT_WAR":
        c = [(p, o) for p, o in w.owners.items() if o != a and o not in w.nations[a]["wars"]]
        p, b = rng.choice(c)
        return "capture", {"a": a, "p": p, "b": b}, code
    if code == "WRONG_OWNER":
        wars = [o for o in w.nations[a]["wars"] if w.nations[o]["alive"]]
        c = [(p, o) for p, o in w.owners.items() if o != a]
        if wars:
            b = rng.choice(wars)
            ps = [p for p, o in w.owners.items() if o != b and o != a]
            return "capture", {"a": a, "p": rng.choice(ps), "b": b}, code
        return None
    if code == "ATTACKS_ALLY":
        al = sorted(w.nations[a]["allies"])
        return ("war", {"a": a, "b": rng.choice(al)}, code) if al else None
    if code == "DEAD_LEADER_ACTS":
        dead = [l for l, (n, ok) in w.leaders.items() if not ok and w.nations[n]["alive"]]
        if not dead:
            return None
        l = rng.choice(dead)
        return "leader_acts", {"l": l, "a": w.leaders[l][0], "what": "the council"}, code
    if code == "ANACHRONISM":
        from .world import TECH_YEAR
        t = [t for t in ("airplanes", "machine guns", "telegraph") if w.year < TECH_YEAR[t]]
        return ("tech", {"a": a, "t": rng.choice(t)}, code) if t else None
    if code == "ELIMINATED_NATION_ACTS":
        dead = [n for n in names if not w.nations[n]["alive"]]
        return ("troops", {"a": rng.choice(dead), "n": "40000"}, code) if dead else None
    if code == "NO_SUCH_ALLIANCE":
        c = [n for n in others if n not in w.nations[a]["allies"]]
        return "break", {"a": a, "b": rng.choice(c)}, code
    if code == "ALLIANCE_WHILE_AT_WAR":
        wars = sorted(w.nations[a]["wars"])
        return ("alliance", {"a": a, "b": rng.choice(wars)}, code) if wars else None
    return None


DEV_CODES = ["NOT_AT_WAR", "WRONG_OWNER", "ATTACKS_ALLY", "DEAD_LEADER_ACTS", "ANACHRONISM", "ELIMINATED_NATION_ACTS"]
HELD_CODES = DEV_CODES + ["NO_SUCH_ALLIANCE", "ALLIANCE_WHILE_AT_WAR"]


def make_game(seed, held_out=False, turns=14):
    """-> list of turns: (world_before, sentences, planted [(sentence, code)])"""
    from .world import check_turn
    rng = random.Random(seed)
    year = rng.choice([1790, 1815, 1850, 1900]) if not held_out else rng.choice([1620, 1745, 1830, 1880])
    w, names = start(rng, year)
    alt = {k: NARR_ALT[k] + (HELD_ALT[k] if held_out else []) for k in NARR_ALT}
    pool = HELD_CODES if held_out else DEV_CODES
    out = []
    for t in range(turns):
        sents, planted, applied = [], [], []
        for _ in range(rng.randint(3, 6)):
            tries = 0
            while tries < 10:
                tries += 1
                r = valid_sentence(rng, w, names, alt)
                if r:
                    s = render(r[0], r[1], alt, rng)
                    bad, _, _ = check_turn(w, applied + [s])      # keep the narration valid in sequence
                    if not bad:
                        applied.append(s)
                        sents.append(s)
                        break
            if rng.random() < 0.25:
                try:
                    pl = plant(rng, w, names, pool)
                except (IndexError, KeyError):
                    pl = None   # nothing to plant of that kind right now
                if pl:
                    kind, g, code = pl
                    s = render(kind, g, alt, rng)
                    sents.insert(0, s)   # planted at the start of the turn, where the state is the one the plant was derived from
                    planted.append((s, code))
        valid = [s for s in sents if s not in {p for p, _ in planted}]
        before = w
        _, _, w = check_turn(w, valid)                           # world advances along the valid sentences only
        if rng.random() < 0.2:                                   # a leader dies in the true world; narration is silent
            alive = [l for l, (n, ok) in w.leaders.items() if ok and w.nations[n]["alive"]]
            if alive:
                l = rng.choice(alive)
                w.leaders[l] = (w.leaders[l][0], False)
        w.year += rng.randint(1, 4)
        out.append((before, sents, planted))
    return out
