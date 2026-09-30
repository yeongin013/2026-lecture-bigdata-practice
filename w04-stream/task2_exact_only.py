#!/usr/bin/env python3
"""Week 4 · Task 2 - the exact set alone, past where running FM as well is practical.

`task2_limits.py` measures the exact set and Flajolet-Martin together. FM costs
about 63 µs per item here (64 estimators, pure Python), so at 102.4M items it
would take close to two hours - a limit of my FM, not of the exact set, which is
what A2 asks about. This calls the PROVIDED `task2_limits.exact_distinct()`
unchanged; `task2_limits.py` itself is not modified.

    python3 task2_exact_only.py --sizes 51200000,102400000

Writes out/limits_exact_only.json (overwritten), so out/limits.json stays the
provided script's pure output.
"""
import argparse, json, os

from task2_limits import exact_distinct, machine

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", default="51200000,102400000")
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)

    rows = []
    for n in [int(x) for x in a.sizes.split(",")]:
        true, elapsed, peak = exact_distinct(n)
        rows.append({"n": n, "true_distinct": true, "exact_s": elapsed,
                     "exact_peak_bytes": peak})
        print(f"  n={n:>12,}  distinct {true:>11,}   exact {elapsed:>7.2f}s "
              f"{peak / 1e6:>9.1f} MB   {peak / true:.1f} B/distinct", flush=True)

    json.dump({"machine": machine(), "runs": rows},
              open(os.path.join(OUT, "limits_exact_only.json"), "w"), indent=2)
    print(f"\n  -> out/limits_exact_only.json  ({len(rows)} measurement(s))")


if __name__ == "__main__":
    main()
