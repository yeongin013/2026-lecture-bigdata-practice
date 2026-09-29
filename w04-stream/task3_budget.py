#!/usr/bin/env python3
"""Week 4 · Task 3 — Same memory, fewer mistakes.

Textbook §4.4 (Bloom filters), §4.5 (counting distinct).

`NaiveFilter` is a membership filter in a fixed number of bits. It works. It
also makes far more mistakes than it has to with the memory it was given, and
it does so for a reason you can find by reading §4.4.2 and doing one derivative.

You get **exactly the same number of bits**. Make fewer mistakes.

    python3 bench.py
    python3 bench.py --yours

The rule that makes this interesting: a false negative is not allowed. Ever.
The whole point of this structure is that "no" means no. A filter that gets a
better score by occasionally forgetting something it was given has not improved
anything, it has broken the contract.
"""
import hashlib
import math

from task1_sketches import BloomFilter

# The harness states the item count as a module constant, and task3.md points at
# it: "the harness tells you n before you start, so you have no excuse for
# guessing." Reading it is not editing it - bench.py is untouched. The fallback
# is only so this file still imports if bench.py is not on the path.
try:
    from bench import N_INSERT as _ITEMS_EXPECTED
except Exception:                                     # pragma: no cover
    _ITEMS_EXPECTED = None


class NaiveFilter:
    """One hash function, and the bits it was given."""

    def __init__(self, n_bits, seed=246):
        self.n_bits = n_bits
        self.seed = seed
        self.bits = bytearray(n_bits)

    def _index(self, item):
        d = hashlib.blake2b(str(item).encode(), digest_size=8,
                            key=str(self.seed).encode()).digest()
        return int.from_bytes(d, "big") % self.n_bits

    def add(self, item):
        self.bits[self._index(item)] = 1

    def __contains__(self, item):
        return bool(self.bits[self._index(item)])

    def memory_bits(self):
        return self.n_bits


class YourFilter:
    """Your filter.

        __init__(n_bits, seed=246)
        add(item)
        item in filter  ->  bool
        memory_bits()   ->  how many bits you are using

    `memory_bits()` must not exceed the `n_bits` you were given. The harness
    checks. Counting only some of your memory is not an optimisation.

    §4.4.2 gives the false-positive rate of a filter with m bits, k hashes and
    n items inserted. There is a k that minimises it, and it depends on m/n.
    The harness tells you n before you start, so you have no excuse for guessing.

    Then there is a second question, which is worth more: the harness inserts
    a **known** number of items, but a real stream does not tell you n in
    advance. What would you do then? You do not have to implement it - but
    observation.md asks.
    """

    # ------------------------------------------------------------- the choice
    #
    # The parameter is k, the number of hash functions. §4.4.2: with m bits, n
    # items and k hashes, a given bit is still 0 with probability ~e^(-kn/m),
    # so a false positive - all k bits set - has probability
    #
    #     p(k) = (1 - e^(-kn/m))^k
    #
    # Taking d/dk of ln p and setting it to zero gives the minimum at
    #
    #     k* = (m/n) ln 2
    #
    # Here m/n = 80,000/8,000 = 10, so k* = 10 ln 2 = 6.93. k must be an
    # integer, and 7 is the better of the two neighbours:
    #
    #     k = 6  ->  0.844%      k = 7  ->  0.819%      k = 8  ->  0.845%
    #
    # So k = 7 and the predicted rate is 0.819%. That is the floor task3.md
    # refers to, and it is a floor, not a target to beat: p(k*) = 2^-k* =
    # 0.6185^(m/n), which no choice of k can go below at ten bits per item.
    # The baseline's mistake is not a bad hash, it is k = 1: p(1) = 9.52%,
    # eleven times worse with identical memory.

    def __init__(self, n_bits, seed=246):
        # Whole bytes only, so memory_bits() reports the bits that actually
        # exist rather than a rounded-up claim. At 80,000 this loses nothing.
        m = (n_bits // 8) * 8
        if m <= 0:
            raise ValueError("need at least one byte of budget")
        n = _ITEMS_EXPECTED or max(1, m // 10)
        self.budget_bits = n_bits
        self.n_expected = n
        # Same Bloom filter as Task 1. The only difference from the baseline is
        # that k is derived instead of assumed - hence composition, not a rewrite.
        self._bloom = BloomFilter(m, max(1, round((m / n) * math.log(2))), seed)

    @property
    def k(self):
        return self._bloom.k

    def add(self, item):
        self._bloom.add(item)

    def __contains__(self, item):
        return item in self._bloom

    def memory_bits(self):
        # R3: every bit this filter holds. The bit array is packed 8 to a byte,
        # so this is the true figure - len(bytearray) * 8, not a promise.
        # (NaiveFilter reports n_bits while holding bytearray(n_bits), which is
        # n_bits BYTES: it uses eight times the memory it declares.)
        return len(self._bloom.bits) * 8

    def expected_fp_rate(self):
        """§4.4.2's prediction for the k this filter chose. Computed, not measured."""
        return self._bloom.expected_fp_rate(self.n_expected)
