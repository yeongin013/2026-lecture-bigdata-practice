#!/usr/bin/env python3
"""Week 3 · Task 2, extended past the 2,120-document ceiling.

`task2_crossover.py` takes its documents as `bench.build()[:n]`, and
`bench.build()` always returns 2,120 of them, so every n above 2,120 re-measures
the same corpus. That script is left exactly as provided. This one reaches A2 -
"keep going until it is unpleasant, record that size" - without editing it or
`bench.py`:

  * documents: `bench.build()` first, so n <= 2,120 is bench's own corpus,
    then `bench.build(1)`, `bench.build(2)`, ... appended. Each seed is built
    with bench's own recipe; nothing about how a document looks changes.
  * measurement: the provided `task2_crossover.timed()`, the same
    `bench.Counter`, the same `BruteForce` and `YourFinder`.

Brute force's cost depends only on n and on set sizes, so a concatenated corpus
is a fair corpus for timing. Recall against planted pairs is not measured here.

    python3 task2_extend.py --sizes 4000,6500,8000

Writes out/crossover_ext.json (overwritten, not appended), so out/crossover.json
stays the unmodified script's pure output.
"""
import argparse, json, os

import bench
from task2_crossover import machine, timed
from task3_scale import BruteForce, YourFinder

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def corpus(n):
    """n documents: bench's own 2,120 first, then further seeds of the same recipe."""
    docs, seed = list(bench.build()), 1
    while len(docs) < n:
        docs.extend(bench.build(seed))
        seed += 1
    return docs[:n], seed - 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", default="4000,6500,8000")
    p.add_argument("--threshold", type=float, default=0.6)
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)

    rows = []
    for n in [int(x) for x in a.sizes.split(",")]:
        docs, extra_seeds = corpus(n)
        sim = bench.Counter()
        _, t_brute, m_brute = timed(BruteForce(a.threshold).find, docs, sim)
        sim2 = bench.Counter()
        _, t_lsh, m_lsh = timed(YourFinder(a.threshold).find, docs, sim2)
        row = {"n": n, "extra_seeds": extra_seeds,
               "brute_s": t_brute, "brute_calls": sim.calls,
               "brute_peak_bytes": m_brute,
               "lsh_s": t_lsh, "lsh_calls": sim2.calls, "lsh_peak_bytes": m_lsh}
        rows.append(row)
        print(f"  n={n:>6}  brute {t_brute:>8.2f}s  {sim.calls:>12,} cmp  "
              f"{m_brute / 1e3:>7.1f} KB   |  lsh {t_lsh:>6.2f}s  "
              f"{sim2.calls:>7,} cmp  {m_lsh / 1e6:>5.2f} MB", flush=True)

    path = os.path.join(OUT, "crossover_ext.json")
    json.dump({"machine": machine(),
               "corpus": "bench.build() + bench.build(1) + bench.build(2) + ..., "
                         "first n documents",
               "runs": rows}, open(path, "w"), indent=2)
    print(f"\n  -> out/crossover_ext.json  ({len(rows)} measurement(s))")


if __name__ == "__main__":
    main()
