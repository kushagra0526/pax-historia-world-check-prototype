"""A tiny alternate-history world and a validator for AI-narrated turns.

State: year, nations (alive, leader, allies, wars, provinces), province owners, leaders (alive flag). A turn's narration is a list of
sentences; each makes a claim about the world. The checker parses the claims and tests each against the state *before* the turn, applies
the valid ones, and returns violations with the sentence and the reason.
"""
import re

TECH_YEAR = {"railway": 1830, "railways": 1830, "telegraph": 1844, "machine guns": 1884, "machine gun": 1884, "airplanes": 1903, "airplane": 1903, "tanks": 1916, "radar": 1935}

PATTERNS = [  # (kind, regex) one family of surface forms per kind
    ("capture", re.compile(r"^(?P<a>[A-Z][\w ]+?) (?:captures|seizes|annexes|wrests) (?P<p>[A-Z][\w ]+?) from (?P<b>[A-Z][\w ]+?)\.?$")),
    ("capture", re.compile(r"^(?P<p>[A-Z][\w ]+?) falls to (?P<a>[A-Z][\w ]+?), taken from (?P<b>[A-Z][\w ]+?)\.?$")),
    ("war", re.compile(r"^(?P<a>[A-Z][\w ]+?) (?:declares war on|goes to war with) (?P<b>[A-Z][\w ]+?)\.?$")),
    ("alliance", re.compile(r"^(?P<a>[A-Z][\w ]+?) signs an alliance with (?P<b>[A-Z][\w ]+?)\.?$")),
    ("alliance", re.compile(r"^(?P<a>[A-Z][\w ]+?) and (?P<b>[A-Z][\w ]+?) sign an alliance\.?$")),
    ("break", re.compile(r"^(?P<a>[A-Z][\w ]+?) (?:breaks|ends) its alliance with (?P<b>[A-Z][\w ]+?)\.?$")),
    ("leader_dies", re.compile(r"^(?P<l>[A-Z][\w ]+?), (?:ruler|leader) of (?P<a>[A-Z][\w ]+?), (?:dies|is assassinated)\.?$")),
    ("leader_acts", re.compile(r"^(?P<l>[A-Z][\w ]+?) of (?P<a>[A-Z][\w ]+?) (?:addresses|reviews|orders) (?:the )?(?P<what>[\w ]+?)\.?$")),
    ("tech", re.compile(r"^(?P<a>[A-Z][\w ]+?) deploys (?P<t>[a-z ]+?)\.?$")),
    ("troops", re.compile(r"^(?P<a>[A-Z][\w ]+?) fields (?P<n>-?\d+) troops\.?$")),
]


class World:
    def __init__(self, year, nations, owners, leaders):
        self.year, self.nations, self.owners, self.leaders = year, nations, owners, leaders   # leaders: name -> (nation, alive)

    def copy(self):
        return World(self.year, {k: {**v, "allies": set(v["allies"]), "wars": set(v["wars"])} for k, v in self.nations.items()}, dict(self.owners), dict(self.leaders))


def parse(sentence, patterns=PATTERNS):
    for kind, rx in patterns:
        m = rx.match(sentence.strip())
        if m:
            return kind, m.groupdict()
    return None, {}


def check_turn(world, sentences, patterns=PATTERNS):
    """-> (violations [(sentence, code)], unparsed sentences, new world)"""
    w = world.copy()
    bad, unparsed = [], []
    for s in sentences:
        kind, g = parse(s, patterns)
        if kind is None:
            unparsed.append(s)
            continue
        a, b = g.get("a"), g.get("b")
        for n in (a, b):
            if n and n not in w.nations:
                bad.append((s, "UNKNOWN_NATION"))
                break
        else:
            if a and not w.nations[a]["alive"]:
                bad.append((s, "ELIMINATED_NATION_ACTS"))
            elif kind == "capture":
                p = g["p"]
                if b not in w.nations[a]["wars"]:
                    bad.append((s, "NOT_AT_WAR"))
                elif w.owners.get(p) != b:
                    bad.append((s, "WRONG_OWNER"))
                else:
                    w.owners[p] = a
                    if not any(o == b for o in w.owners.values()):
                        w.nations[b]["alive"] = False
            elif kind == "war":
                if b in w.nations[a]["allies"]:
                    bad.append((s, "ATTACKS_ALLY"))
                else:
                    w.nations[a]["wars"].add(b)
                    w.nations[b]["wars"].add(a)
            elif kind == "alliance":
                if b in w.nations[a]["wars"]:
                    bad.append((s, "ALLIANCE_WHILE_AT_WAR"))
                else:
                    w.nations[a]["allies"].add(b)
                    w.nations[b]["allies"].add(a)
            elif kind == "break":
                if b not in w.nations[a]["allies"]:
                    bad.append((s, "NO_SUCH_ALLIANCE"))
                else:
                    w.nations[a]["allies"].discard(b)
                    w.nations[b]["allies"].discard(a)
            elif kind in ("leader_dies", "leader_acts"):
                l = g["l"]
                if l not in w.leaders or w.leaders[l][0] != a:
                    bad.append((s, "WRONG_LEADER"))
                elif kind == "leader_acts" and not w.leaders[l][1]:
                    bad.append((s, "DEAD_LEADER_ACTS"))
                elif kind == "leader_dies":
                    if not w.leaders[l][1]:
                        bad.append((s, "DEAD_LEADER_ACTS"))
                    else:
                        w.leaders[l] = (a, False)
            elif kind == "tech":
                if w.year < TECH_YEAR.get(g["t"].strip(), 0):
                    bad.append((s, "ANACHRONISM"))
            elif kind == "troops":
                if int(g["n"]) < 0:
                    bad.append((s, "NEGATIVE_TROOPS"))
    return bad, unparsed, w
