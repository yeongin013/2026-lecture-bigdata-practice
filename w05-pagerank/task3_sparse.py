#!/usr/bin/env python3
"""Week 5 · Task 3 — PageRank on a graph that will not fit as a matrix.

Textbook §5.2 (efficient PageRank), §5.2.1 - §5.2.3.

`DenseMatrix` is PageRank written the way the equations are written: build the
transition matrix M, multiply. It is correct, it is easy to read, and it stores
n^2 numbers for a graph with almost no edges.

The web's matrix is about 99.9999% zeros. Storing them is the problem, and
§5.2 is the chapter about not doing that.

    python3 bench.py
    python3 bench.py --yours

Correctness first: the harness compares your ranks against the dense version
element by element. A fast PageRank that ranks pages differently is a different
algorithm, not a faster one.
"""


class DenseMatrix:
    """PageRank as written in the equations. Stores n^2 floats."""

    def __init__(self, beta=0.85, tol=1e-10, max_iter=100):
        self.beta, self.tol, self.max_iter = beta, tol, max_iter

    def run(self, graph):
        nodes = list(graph)
        n = len(nodes)
        index = {v: i for i, v in enumerate(nodes)}

        # the full transition matrix, zeros and all
        M = [[0.0] * n for _ in range(n)]
        for v, outs in graph.items():
            if outs:
                share = 1.0 / len(outs)
                for w in outs:
                    M[index[w]][index[v]] = share
            else:
                for i in range(n):           # dead end: spread it everywhere
                    M[i][index[v]] = 1.0 / n

        r = [1.0 / n] * n
        for self.iterations in range(1, self.max_iter + 1):
            nr = [0.0] * n
            for i in range(n):
                row = M[i]
                s = 0.0
                for j in range(n):
                    if row[j]:
                        s += row[j] * r[j]
                nr[i] = self.beta * s + (1 - self.beta) / n
            delta = sum(abs(a - b) for a, b in zip(nr, r))
            r = nr
            if delta < self.tol:
                break
        return {v: r[index[v]] for v in nodes}

    def memory_floats(self):
        return getattr(self, "_n", 0) ** 2


class YourPageRank:
    """Your PageRank.

        __init__(beta=0.85, tol=1e-10, max_iter=100)
        run(graph) -> {node: rank}
        memory_floats() -> the largest number of floats you held at once

    Same ranks, to within 1e-9 per node. Far less memory.

    `graph` is {node: [out-neighbours]}. Note what that already is: an adjacency
    list, which is the sparse representation. The dense version throws that
    structure away and then pays to get it back.

    Two things to be careful about, and they are the same two as Task 1:

      * dead ends, whose rank has to go somewhere
      * the teleport term, which touches every node and is therefore the one
        part that looks like it needs a dense operation - it does not, and
        working out why is the point of §5.2.3

    `memory_floats()` is on your honour and the harness reads it. Count the
    numbers you actually hold at once.
    """

    # ---------------------------------------------------------------- what is
    # stored instead of M
    #
    #   r, nr     the old and new rank vectors          2n floats
    #   outs      the adjacency list, as node indices   e ints (no floats)
    #
    # plus three scalars per iteration (dead-end mass, the shared base value,
    # the L1 change). M's n^2 entries are never built: an edge v -> w already
    # says "w gets r[v] / outdeg(v)", so each iteration walks the e edges once.
    #
    # The two all-node terms are not dense operations. Every node gets the same
    # (1 - beta)/n from teleporting and the same beta * dead / n from dead ends,
    # so they collapse into ONE number, `base`, computed once per iteration and
    # used as each node's starting value. What would be an n x n block of equal
    # entries in M is a single scalar here.

    def __init__(self, beta=0.85, tol=1e-10, max_iter=100):
        self.beta, self.tol, self.max_iter = beta, tol, max_iter
        self._held = 0

    def run(self, graph):
        nodes = list(graph)
        n = len(nodes)
        if n == 0:
            return {}
        index = {v: i for i, v in enumerate(nodes)}
        outs = [[index[w] for w in graph[v]] for v in nodes]
        dead_ends = [i for i, o in enumerate(outs) if not o]
        beta, teleport = self.beta, (1 - self.beta) / n

        r = [1.0 / n] * n
        for self.iterations in range(1, self.max_iter + 1):
            dead = sum(r[i] for i in dead_ends)
            base = beta * dead / n + teleport
            nr = [base] * n
            for j, o in enumerate(outs):
                if o:
                    share = beta * r[j] / len(o)
                    for i in o:
                        nr[i] += share
            delta = sum(abs(a - b) for a, b in zip(nr, r))
            r = nr
            if delta < self.tol:
                break
        self._held = 2 * n + 3          # r, nr, and dead / base / delta
        return {v: r[index[v]] for v in nodes}

    def memory_floats(self):
        return self._held
