#!/usr/bin/env python3
"""Week 5 · Task 2 - why so few iterations? The convergence rate, measured.

The textbook bound says the error shrinks like beta^k, which would need about
2,300 iterations at beta = 0.99 to reach 1e-10. task2_convergence.py stopped
after 24. This script checks whether that was real convergence or just a small
step, and measures the actual per-iteration contraction.

For each beta it records:
  * the L1 change per iteration, and the ratio of successive changes - the
    observed contraction rate (the second eigenvalue's size, in effect)
  * the L1 distance between the tol=1e-10 answer and a reference run for
    5,000 iterations with no early stop - how far "converged" really was
  * the rank held by the 2-node spider trap in each

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


def main():
    os.makedirs(OUT, exist_ok=True)
    graph = bench.build()
    trap = [v for v, o in graph.items() if len(o) == 1 and graph[o[0]] == [v]]
    rows = []
    for beta in BETAS:
        stopped = pagerank(graph, beta=beta, iterations=500, tol=1e-10)
        used = pagerank.iterations
        ref = pagerank(graph, beta=beta, iterations=5000, tol=0.0)
        err = sum(abs(stopped[v] - ref[v]) for v in ref)
        ds = deltas(graph, beta, 12)
        ratios = [b / a for a, b in zip(ds, ds[1:]) if a > 0]
        rate = statistics.median(ratios[3:])
        rows.append({"beta": beta, "iterations": used, "l1_error_vs_5000": err,
                     "observed_rate": rate, "beta_to_the_k_would_need":
                     __import__("math").log(1e-10) / __import__("math").log(beta),
                     "trap_rank_stopped": sum(stopped[v] for v in trap),
                     "trap_rank_reference": sum(ref[v] for v in trap)})
        print(f"  beta {beta:<5} {used:>3} it   observed rate {rate:.3f}"
              f"  (beta^k needs {rows[-1]['beta_to_the_k_would_need']:>6.0f} it)"
              f"   error vs 5000-it run {err:.1e}"
              f"   trap rank {rows[-1]['trap_rank_stopped']:.5f}")
    json.dump({"trap_nodes": trap, "runs": rows},
              open(os.path.join(OUT, "convergence_why.json"), "w"), indent=2)
    print("\n  -> out/convergence_why.json")


if __name__ == "__main__":
    main()
