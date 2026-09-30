#!/usr/bin/env python3
"""Week 4 · Task 1 - how often each Flajolet-Martin combining rule lands within 2x.

One run of `flajolet_martin` says little about a rule, so this measures every
rule over 40 trials: three stream sizes, several hash seeds each. Each trial is
a single pass (`fm_all_rules`), so all rules see exactly the same trailing-zero
records and are strictly comparable.

    python3 task1_fm_rules.py

Writes out/fm_rules.json and prints the summary table used in observation.md.
"""
import json, os, random, statistics

from task1_sketches import fm_all_rules

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# (distinct values, hash seeds). The stream is 3x the distinct count.
CASES = [(1_000, range(16)), (20_000, range(16)), (100_000, range(8))]


def main():
    os.makedirs(OUT, exist_ok=True)
    ratios, trials = {}, []
    for distinct, seeds in CASES:
        rng = random.Random(distinct)
        stream = [f"k{rng.randrange(distinct)}" for _ in range(distinct * 3)]
        true = len(set(stream))
        for s in seeds:
            est = fm_all_rules(stream, seed=s)
            trials.append({"distinct": distinct, "true": true, "seed": s,
                           "estimates": est})
            for rule, e in est.items():
                ratios.setdefault(rule, []).append(e / true)

    summary = {}
    for rule, rs in ratios.items():
        summary[rule] = {"trials": len(rs), "min": min(rs),
                         "median": statistics.median(rs), "max": max(rs),
                         "within_2x": sum(0.5 <= r <= 2.0 for r in rs) / len(rs)}

    print(f"  {'rule':<30} {'min':>6} {'median':>7} {'max':>7}  {'within 2x':>9}")
    for rule, v in sorted(summary.items(), key=lambda kv: (-kv[1]["within_2x"],
                                                            abs(kv[1]["median"] - 1))):
        print(f"  {rule:<30} {v['min']:>6.2f} {v['median']:>7.2f} {v['max']:>7.2f}"
              f"  {v['within_2x']:>8.0%}")

    json.dump({"cases": [[d, list(s)] for d, s in CASES], "summary": summary,
               "trials": trials}, open(os.path.join(OUT, "fm_rules.json"), "w"),
              indent=1)
    print("\n  -> out/fm_rules.json")


if __name__ == "__main__":
    main()
