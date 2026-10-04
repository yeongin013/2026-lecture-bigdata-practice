#!/usr/bin/env python3
"""Week 5 · Task 2 - why so few iterations? The convergence rate, measured.

The textbook bound says the error shrinks like beta^k, which would need about
2,300 iterations at beta = 0.99 to reach 1e-10. task2_convergence.py stopped
after 24. This script checks whether that was real convergence or just a small
step, and measures the actual per-iteration contraction.

For each beta it records:
  * the L1 change per iteration, and the ratio of successive changes over
    iterations 5-12 - the early contraction rate
  * the ratio of successive L1 errors against the reference from iteration 17
    on, while the error is still above 1e-12 (float noise below that) - the
    late contraction rate, which is the one that lasts; null when the error
    reaches the noise floor before iteration 17
  * the L1 distance between the tol=1e-10 answer and a reference run for
    5,000 iterations with no early stop - how far "converged" really was
  * the rank held by the 2-node spider trap in each
  * how many of the top-100 positions differ from the beta = 0.85 order (A6)

    python3 task2_why.py
Writes out/convergence_why.json. Uses task1_pagerank.pagerank unchanged.
"""
import json, os, statistics

import bench
from task1_pagerank import pagerank

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
BETAS = [0.5, 0.7, 0.85, 0.95, 0.99]


def deltas(graph, beta, steps):
    """L1 change at each of `steps` iterations, by stepping pagerank one at a time."""
    out, r = [], None
    for k in range(1, steps + 1):
        nr = pagerank(graph, beta=beta, iterations=k, tol=0.0)
        if r is not None:
            out.append(sum(abs(nr[v] - r[v]) for v in nr))
        r = nr
    return out


def late_rate(graph, beta, ref):
    """Median ratio of successive L1 errors vs `ref`, iteration 17 on, error >= 1e-12."""
    errs = []
    for k in range(16, 41):
        r = pagerank(graph, beta=beta, iterations=k, tol=0.0)
        errs.append(sum(abs(r[v] - ref[v]) for v in ref))
    ratios = [b / a for a, b in zip(errs, errs[1:]) if b >= 1e-12]
    return statistics.median(ratios) if ratios else None


def top(ranks, n=100):
    return sorted(ranks, key=lambda v: (-ranks[v], v))[:n]


def main():
    os.makedirs(OUT, exist_ok=True)
    graph = bench.build()
    trap = [v for v, o in graph.items() if len(o) == 1 and graph[o[0]] == [v]]
    base = top(pagerank(graph, beta=0.85, iterations=5000, tol=0.0))
    rows = []
    for beta in BETAS:
        stopped = pagerank(graph, beta=beta, iterations=500, tol=1e-10)
        used = pagerank.iterations
        ref = pagerank(graph, beta=beta, iterations=5000, tol=0.0)
        err = sum(abs(stopped[v] - ref[v]) for v in ref)
        ds = deltas(graph, beta, 12)
        ratios = [b / a for a, b in zip(ds, ds[1:]) if a > 0]
        rate = statistics.median(ratios[3:])
        late = late_rate(graph, beta, ref)
        top100 = top(ref)
        rows.append({"beta": beta, "iterations": used, "l1_error_vs_5000": err,
                     "observed_rate": rate, "late_rate": late,
                     "top100_same_set_as_085": set(top100) == set(base),
                     "top100_positions_changed_vs_085":
                     sum(a != b for a, b in zip(top100, base)),
                     "beta_to_the_k_would_need":
                     __import__("math").log(1e-10) / __import__("math").log(beta),
                     "trap_rank_stopped": sum(stopped[v] for v in trap),
                     "trap_rank_reference": sum(ref[v] for v in trap)})
        print(f"  beta {beta:<5} {used:>3} it   rate early {rate:.3f} (/beta {rate / beta:.3f})"
              + (f" late {late:.3f} (/beta {late / beta:.3f})" if late
                 else " late   -   (noise floor first)")
              + f"   top-100 moved {rows[-1]['top100_positions_changed_vs_085']:>3}"
              f"  (beta^k needs {rows[-1]['beta_to_the_k_would_need']:>6.0f} it)"
              f"   error vs 5000-it run {err:.1e}"
              f"   trap rank {rows[-1]['trap_rank_stopped']:.5f}")
    json.dump({"trap_nodes": trap, "runs": rows},
              open(os.path.join(OUT, "convergence_why.json"), "w"), indent=2)
    print("\n  -> out/convergence_why.json")


if __name__ == "__main__":
    main()
