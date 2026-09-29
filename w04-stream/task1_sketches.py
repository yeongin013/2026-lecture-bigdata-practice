#!/usr/bin/env python3
"""Week 4 · Task 1 — Answer questions about a stream you cannot store.

Textbook §4.3 (sampling), §4.4 (Bloom filter), §4.5 (Flajolet-Martin).

The premise of the whole chapter: the stream is longer than your memory, it
goes past once, and you still have to answer. Every method here trades an exact
answer for a bounded amount of space, and the job is to know exactly what you
traded.

You build three, and the harness checks each against the truth it is
approximating.

    python3 task1_sketches.py --verify
"""
import argparse, hashlib, math, random, statistics

# Flajolet-Martin's 2^R runs high - E[2^R] ~ n/PHI - so rules that keep the
# scale of 2^R get multiplied by PHI. _FM_RULE names the rule actually used;
# out/observation.md reports what every other rule gave on the same pass.
_FM_BIAS = 0.77351
_FM_RULE = "2^(mean R) x PHI"


class BloomFilter:
    """Membership, with one-sided error.

    A Bloom filter never says "no" about something you inserted. It sometimes
    says "yes" about something you did not. That asymmetry is the entire design
    and it is why it is useful for "have I seen this before" and useless for
    "is this definitely in the set".

    `m` bits, `k` hash functions.
    """

    def __init__(self, m, k, seed=246):
        if m <= 0 or k <= 0:
            raise ValueError("m and k must both be positive")
        self.m = m
        self.k = k
        self.seed = seed
        self._key = str(seed).encode()
        # m BITS, packed 8 to a byte. A bytearray(m) would be a bytearray of m
        # BYTES - eight times the memory for the same filter - and claiming m
        # bits while holding 8m is the thing Task 3 R3 forbids.
        self.bits = bytearray((m + 7) // 8)
        self.n_inserted = 0

    def _positions(self, item):
        """The k bit positions this item owns.

        One digest per 16 positions, sliced into 4-byte words. The positions
        depend only on the item, never on what is already in the filter - that
        is what makes R1 structural rather than probabilistic.
        """
        raw = str(item).encode()
        out, block = [], 0
        while len(out) < self.k:
            d = hashlib.blake2b(raw + b"#" + str(block).encode(),
                                digest_size=64, key=self._key).digest()
            for i in range(0, 64, 4):
                out.append(int.from_bytes(d[i:i + 4], "big") % self.m)
                if len(out) == self.k:
                    break
            block += 1
        return out

    def add(self, item):
        for i in self._positions(item):
            self.bits[i >> 3] |= 1 << (i & 7)
        self.n_inserted += 1

    def __contains__(self, item):
        # R1: `add` only ever turns bits ON, and nothing ever turns one off, so
        # every bit an inserted item set is still set. A "no" therefore cannot
        # happen for something inserted - not rarely, never.
        return all(self.bits[i >> 3] >> (i & 7) & 1
                   for i in self._positions(item))

    def expected_fp_rate(self, n_inserted):
        """The textbook's predicted false-positive rate after n insertions.

        §4.4.2 derives it. Return the number, do not measure it - the harness
        measures separately and compares the two.

        kn/m darts are thrown at m bits, so a given bit is still 0 with
        probability (1 - 1/m)^(kn) ~ e^(-kn/m). A false positive needs all k of
        an absent item's bits to be 1:

            (1 - e^(-kn/m))^k
        """
        return (1.0 - math.exp(-self.k * n_inserted / self.m)) ** self.k


def _tails(stream, n_hashes, seed):
    """One pass. Returns the longest run of trailing zeros seen by each of the
    n_hashes independent estimators.

    h_j(x) = (a_j * base(x) + b_j) mod 2^64 with a_j odd. Every estimator sees
    every item, which is what §4.5 describes; the price is that per-item work is
    O(n_hashes), and that is exactly the cost HyperLogLog removes. Task 2's
    timings are what that price looks like.

    low_mask[j] isolates the lowest tails[j]+1 bits. If any is set the item
    cannot beat the record and the expensive path is skipped, so once tails[j]
    has grown almost every item costs a single multiply. The high bits of the
    product cannot affect the low bits, so this test does not need the mod 2^64.
    """
    if n_hashes <= 0:
        raise ValueError("n_hashes must be positive")
    MASK = (1 << 64) - 1
    rng = random.Random(seed)
    a = [rng.randrange(1, 1 << 64) | 1 for _ in range(n_hashes)]
    b = [rng.randrange(1 << 64) for _ in range(n_hashes)]
    tails = [0] * n_hashes
    low_mask = [1] * n_hashes
    seen = False
    blake = hashlib.blake2b
    for item in stream:
        seen = True
        base = int.from_bytes(blake(str(item).encode(), digest_size=8).digest(),
                              "big")
        for j in range(n_hashes):
            if not (a[j] * base + b[j]) & low_mask[j]:
                v = (a[j] * base + b[j]) & MASK
                tz = 64 if v == 0 else (v & -v).bit_length() - 1
                if tz > tails[j]:
                    tails[j] = tz
                    low_mask[j] = (1 << (tz + 1)) - 1
    return tails if seen else None


def _rules(tails):
    """Every combining rule, from one pass's trailing-zero records.

    The estimate 2^R is biased high: E[2^R] ~ n/PHI, so a rule that keeps the
    scale of 2^R has to be multiplied by PHI to land on n. Rules that are
    already medians of powers of two do not, and the numbers in
    out/observation.md say which is which.
    """
    powers = [float(1 << r) for r in tails]
    n_hashes = len(powers)
    g = max(1, math.isqrt(n_hashes))          # 64 hashes -> 8 groups of 8
    groups = [powers[i:i + g] for i in range(0, n_hashes, g)]
    tail_groups = [tails[i:i + g] for i in range(0, n_hashes, g)]
    return {
        "mean of 2^R": sum(powers) / n_hashes,
        "median of 2^R": statistics.median(powers),
        "median of group means": statistics.median(
            [sum(x) / len(x) for x in groups]),
        "mean of group medians": statistics.mean(
            [statistics.median(x) for x in groups]),
        "2^(mean R)": float(2.0 ** statistics.mean(tails)),
        "2^(mean R) x PHI": float(2.0 ** statistics.mean(tails)) * _FM_BIAS,
        "median of group means x PHI": statistics.median(
            [sum(x) / len(x) for x in groups]) * _FM_BIAS,
        "harmonic mean of 2^R": n_hashes / sum(1.0 / x for x in powers),
    }


def flajolet_martin(stream, n_hashes=64, seed=246):
    """Estimate how many DISTINCT items went past, in almost no memory.

    §4.5. Hash each item, count trailing zeros in the hash, keep the maximum.
    A maximum of R suggests about 2^R distinct items, because seeing R trailing
    zeros is a 1-in-2^R event.

    One hash gives an estimate with enormous variance, so you use many and
    combine them. How you combine them matters a great deal:

      * averaging 2^R directly is dominated by whichever hash got lucky - the
        values are exponential, so one outlier swamps the rest
      * the median is robust but can only ever be a power of two
      * §4.5.3 suggests grouping, and combining twice

    The harness accepts anything **within a factor of two** of the truth. That is
    not a generous tolerance, it is an honest one: this method really is that
    crude, and HyperLogLog exists because of it. Getting inside a factor of two
    reliably is the requirement; getting closer than that is not expected here.

    Return your estimate as a float.
    """
    tails = _tails(stream, n_hashes, seed)
    if tails is None:
        return 0.0
    return _rules(tails)[_FM_RULE]


def fm_all_rules(stream, n_hashes=64, seed=246):
    """Every combining rule from one shared pass, so the numbers in
    observation.md are strictly comparable. Returns {rule: estimate}."""
    tails = _tails(stream, n_hashes, seed)
    return {} if tails is None else _rules(tails)


def reservoir_sample(stream, k, seed=246):
    """Keep k items uniformly at random from a stream of unknown length.

    §4.3. Every item that went past must end up with the same probability k/n
    of being in your sample, and you only ever hold k of them.

    Return a list of k items (or fewer if the stream was shorter).
    """
    if k <= 0:
        return []
    rng = random.Random(seed)
    keep = []
    for i, item in enumerate(stream):
        if i < k:
            keep.append(item)            # the first k just fill the reservoir
        else:
            # The only place a length appears is `i + 1`, the number of items
            # seen SO FAR. The total length n is never needed and never known:
            # item i is kept with probability k/(i+1), and each later item has
            # probability k/(i+1) of evicting a uniformly chosen incumbent, so
            # after the stream ends every item stands at exactly k/n. The
            # sample is valid if the stream stops at any point.
            j = rng.randrange(i + 1)
            if j < k:
                keep[j] = item
    return keep


# ------------------------------------------------------------------- harness
def verify():
    fails = 0
    rng = random.Random(246)

    def check(label, ok, detail=""):
        nonlocal fails
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<46} {detail}")
        fails += not ok

    # --- Bloom: no false negatives, ever
    try:
        bf = BloomFilter(m=8192, k=5)
    except NotImplementedError:
        print("  BloomFilter is still a stub"); return 1
    inserted = [f"item-{i}" for i in range(800)]
    for x in inserted:
        bf.add(x)
    check("no false negatives", all(x in bf for x in inserted))

    absent = [f"other-{i}" for i in range(20_000)]
    fp = sum(1 for x in absent if x in bf) / len(absent)
    predicted = bf.expected_fp_rate(len(inserted))
    close = abs(fp - predicted) < max(0.02, predicted * 0.5)
    check("measured false-positive rate matches theory", close,
          f"measured {fp:.3%}, predicted {predicted:.3%}")

    # --- Flajolet-Martin: a factor of two is what this method gives you
    try:
        distinct = 20_000
        stream = [f"k{rng.randrange(distinct)}" for _ in range(120_000)]
        est = flajolet_martin(stream)
    except NotImplementedError:
        print("  flajolet_martin is still a stub"); return 1
    true_distinct = len(set(stream))
    ratio = est / true_distinct
    check("distinct estimate within a factor of 2", 0.5 <= ratio <= 2.0,
          f"estimated {est:,.0f}, true {true_distinct:,} ({ratio:.2f}x)")

    # --- Reservoir: uniform over many trials
    try:
        counts = [0] * 20
        trials = 4000
        for t in range(trials):
            s = reservoir_sample(range(20), 5, seed=t)
            for i in s:
                counts[i] += 1
    except NotImplementedError:
        print("  reservoir_sample is still a stub"); return 1
    expected = trials * 5 / 20
    spread = (max(counts) - min(counts)) / expected
    check("reservoir is uniform across items", spread < 0.15,
          f"spread {spread:.1%} around {expected:.0f}")

    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())
