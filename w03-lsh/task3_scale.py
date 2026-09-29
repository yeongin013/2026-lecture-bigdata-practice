#!/usr/bin/env python3
"""Week 3 · Task 3 — Find the same pairs without comparing everything.

Textbook §3.4.

`BruteForce` compares every pair. On 3,000 documents that is 4.5 million
comparisons and it is completely correct. On 3 million documents it is 4.5
trillion and it is completely useless.

Beat it. Find the same near-duplicate pairs while making far fewer comparisons.

    python3 bench.py
    python3 bench.py --yours

The harness counts every call you make to `similarity()`. That is your score.
It also checks **recall** - which of the truly similar pairs you found. Skipping
comparisons is easy; skipping comparisons without losing the pairs is the task.
"""
import random

from task1_minhash import lsh_candidates, minhash_signatures


def _next_prime(n):
    """Smallest prime >= n. Used as the modulus of the hash family."""
    def prime(m):
        if m < 2:
            return False
        if m % 2 == 0:
            return m == 2
        f = 3
        while f * f <= m:
            if m % f == 0:
                return False
            f += 2
        return True

    while not prime(n):
        n += 1
    return n


class BruteForce:
    """Correct, and quadratic."""

    def __init__(self, threshold):
        self.threshold = threshold

    def find(self, docs, similarity):
        """docs is [set_of_shingles, ...]. Return {(i, j), ...} with i < j."""
        out = set()
        for i in range(len(docs)):
            for j in range(i + 1, len(docs)):
                if similarity(docs[i], docs[j]) >= self.threshold:
                    out.add((i, j))
        return out


class YourFinder:
    """Your near-duplicate finder.

        __init__(threshold)
        find(docs, similarity) -> {(i, j), ...}

    `similarity(a, b)` is the only way to compare two documents, and every call
    is counted. Everything else - signatures, banding, bucketing - is free, in
    the sense that the harness does not charge you for it. That is deliberate:
    it is also roughly true at scale, where the comparison is the expensive
    part and the hashing is linear.

    Two knobs decide everything:

        the number of hashes in a signature
        how many bands you split it into

    §3.4.2 gives you the relationship between those and the probability that a
    pair at similarity s becomes a candidate. It is an S-curve, and where its
    step sits is something you choose. Choose it on purpose and be able to say
    why in observation.md - a threshold of 0.8 does not mean bands should be
    anything in particular until you have done the arithmetic.

    You may reuse your Task 1 code.

    ------------------------------------------------------------------ choice

    N_HASHES = 128 split into BANDS = 32, so r = 4 rows to a band.

    §3.4.2: a pair at similarity s becomes a candidate with probability
    1 - (1 - s^r)^b, an S-curve whose step sits near (1/b)^(1/r). Here that is

        (1/32)^(1/4) = 0.420

    which is deliberately **below** the 0.6 threshold rather than on it. The
    planted pairs sit just above the line - a clone with 14 of its 60 shingles
    swapped has similarity 46/74 = 0.622 - so a step parked at 0.6 would catch
    the weakest of them only about half the time. With the step at 0.42 that
    same pair becomes a candidate with probability

        1 - (1 - 0.622^4)^32 = 0.994

    and what it costs is false candidates, which is cheap here: two unrelated
    documents share almost nothing out of a 5,000-shingle vocabulary, so at
    s = 0.006 the same formula gives 4e-8, and over two million pairs that is
    a fraction of one extra comparison.

    Moving the step the other way - fewer, taller bands - loses recall fast,
    and recall is the number that has to survive. See out/observation.md.
    """

    N_HASHES = 128
    BANDS = 32
    SEED = 20260916          # fixed, so a run is reproducible

    def __init__(self, threshold):
        self.threshold = threshold

    def _hashes(self, modulus):
        """N_HASHES permutations of 0..modulus-1: x -> (a*x + b) mod p."""
        rng = random.Random(self.SEED)
        return [(lambda x, a=rng.randrange(1, modulus), b=rng.randrange(modulus):
                 (a * x + b) % modulus)
                for _ in range(self.N_HASHES)]

    def find(self, docs, similarity):
        if not docs:
            return set()

        # Shingle ids are the rows of the characteristic matrix. A prime
        # modulus just above the largest of them makes every hash a genuine
        # permutation of the row space, which is what minhashing assumes.
        largest = max((max(d) for d in docs if d), default=0)
        modulus = _next_prime(largest + 1)

        signatures = minhash_signatures(docs, self._hashes(modulus), modulus)

        out = set()
        for i, j in lsh_candidates(signatures, self.BANDS):
            # The only charged line in this file.
            if similarity(docs[i], docs[j]) >= self.threshold:
                out.add((i, j))
        return out
