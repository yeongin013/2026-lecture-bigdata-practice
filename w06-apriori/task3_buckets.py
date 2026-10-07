#!/usr/bin/env python3
"""Week 6 · Task 3 — Measure PCY bucket saturation and total memory.

    python3 task3_buckets.py --buckets 1000003,10007,1009 --scales 0.25,1,4
    python3 task3_buckets.py --scales ""
"""
import argparse, json, os, time, tracemalloc

import bench
from task2_explosion import machine
from task3_pcy import PlainApriori, YourAlgorithm

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def measure(algo, baskets):
    tracemalloc.start()
    t0 = time.perf_counter()
    pairs = algo.run(baskets)
    elapsed = time.perf_counter() - t0
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return set(pairs), elapsed, peak_bytes


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--buckets", default="1000003,500009,250007,100003,50021,10007,1009")
    p.add_argument("--scales", default="0.125,0.25,0.5,0.75,1,2,4,8")
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "pcy_buckets.json")
    data = {"machine": machine(), "runs": []}

    for kind, values in [("buckets", a.buckets), ("scale", a.scales)]:
        if not values.strip():
            continue
        if kind == "buckets":
            bench.ITEMS, bench.BASKETS = 2000, 20000
            baskets = bench.build()
            base = PlainApriori(bench.SUPPORT)
            reference, base_seconds, base_bytes = measure(base, baskets)
        for value in [float(x) if kind == "scale" else int(x) for x in values.split(",")]:
            if kind == "scale":
                bench.ITEMS, bench.BASKETS = int(2000 * value), int(20000 * value)
                baskets = bench.build()
                base = PlainApriori(bench.SUPPORT)
                reference, base_seconds, base_bytes = measure(base, baskets)
                algo = YourAlgorithm(bench.SUPPORT)
            else:
                algo = YourAlgorithm(bench.SUPPORT, n_buckets=value)
            pairs, elapsed, peak_bytes = measure(algo, baskets)
            assert pairs == reference, "PCY and baseline frequent pair keys differ"
            row = {"kind": kind, "n_buckets": algo.n_buckets,
                   "frequent_buckets": algo.frequent_buckets,
                   "peak_counters": algo.peak_counters,
                   "baseline_peak_counters": base.peak_counters,
                   "seconds": elapsed, "peak_bytes": peak_bytes,
                   "baseline_peak_bytes": base_bytes}
            if kind == "scale":
                row.update(scale=value, items=bench.ITEMS, baskets=bench.BASKETS,
                           baseline_seconds=base_seconds)
            else:
                row["frequent_bucket_fraction"] = algo.frequent_buckets / algo.n_buckets
            data["runs"].append(row)
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"  {kind} {value:>7}   buckets {algo.frequent_buckets:,}/{algo.n_buckets:,}   "
                  f"counters {algo.peak_counters:,}/{base.peak_counters:,}   "
                  f"{elapsed:.2f}s   {peak_bytes / 1e6:.1f}/{base_bytes / 1e6:.1f} MB",
                  flush=True)


if __name__ == "__main__":
    main()
