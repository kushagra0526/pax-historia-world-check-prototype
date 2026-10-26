import json
from collections import Counter

from . import gen, world


def sentence_level(world_before, sentences):
    """Baseline: judge each sentence alone (year-aware tech check and negative troops only), with no world state."""
    out = []
    for s in sentences:
        kind, g = world.parse(s)
        if kind == "tech" and world_before.year < world.TECH_YEAR.get(g["t"].strip(), 0):
            out.append((s, "ANACHRONISM"))
        if kind == "troops" and int(g["n"]) < 0:
            out.append((s, "NEGATIVE_TROOPS"))
    return out


def score(seeds, held, patterns=None):
    t, per = Counter(), {}
    pat = patterns or world.PATTERNS
    for s in seeds:
        for before, sents, planted in gen.make_game(s, held):
            bad, unparsed, _ = world.check_turn(before, sents, pat)
            base = sentence_level(before, sents)
            gold, got, bl = set(planted), set(bad), set(base)
            t["planted"] += len(gold)
            t["found_exact"] += len(gold & got)
            t["found_any_code"] += len({x for x, _ in gold} & {x for x, _ in got})
            t["false_flags"] += len(got - gold)
            t["baseline_found"] += len(gold & bl)
            t["baseline_false"] += len(bl - gold)
            t["unparsed_sentences"] += len(unparsed)
            t["unparsed_planted"] += len({x for x, _ in gold} & set(unparsed))
            t["valid_sentences"] += len(sents) - len(planted)
            for sen, code in gold:
                p = per.setdefault(code, Counter())
                p["n"] += 1
                p["found"] += (sen, code) in got
    return {"totals": dict(t), "by_code": {k: dict(v) for k, v in sorted(per.items())}}


def main():
    res = {"dev": score(range(0, 200), False), "held_out": score(range(10000, 10200), True)}
    json.dump(res, open("out/result.json", "w"), indent=1)
    for k, v in res.items():
        print(k, v["totals"])
        for c, d in v["by_code"].items():
            print("   ", c, d)


if __name__ == "__main__":
    main()
