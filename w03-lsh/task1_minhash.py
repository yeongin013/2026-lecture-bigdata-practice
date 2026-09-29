#!/usr/bin/env python3
"""Week 3 · Task 1 — Minhash and LSH, built from the matrix up.

Textbook §3.2 - §3.4.

Comparing every pair is quadratic, so it stops being possible somewhere around
a hundred thousand documents. The way out is two ideas stacked:

    minhash   replace a set with a short signature, such that the chance two
              signatures agree in a position equals their Jaccard similarity
    LSH       hash bands of those signatures so that similar pairs collide and
              you only ever compare the ones that did

You build both. The textbook's §3.3.5 example is small enough to check by hand,
and the harness checks you against it.

    python3 task1_minhash.py --verify
"""
import argparse

# §3.3.5. Rows are elements 0..4, columns are the sets S1..S4.
BOOK = [[1, 0, 0, 1],
        [0, 0, 1, 0],
        [0, 1, 0, 1],
        [1, 0, 1, 1],
        [0, 0, 1, 0]]
# The two hash functions the textbook uses on the row numbers.
BOOK_HASHES = [lambda r: (r + 1) % 5, lambda r: (3 * r + 1) % 5]


def jaccard(a, b):
    """|a and b| / |a or b|. Empty union is 0, not an error."""
    a, b = set(a), set(b)
    union = len(a | b)
    if not union:          # two empty sets have no similarity to speak of,
        return 0.0         # and 0/0 is not a number. R1 says 0, not an error.
    return len(a & b) / union


def minhash_signatures(columns, hashes, n_rows):
    """Build the signature matrix, one pass over the rows.

    `columns` is [set_of_row_numbers, ...], one entry per document.
    Return [[sig for each hash] for each column].

    The algorithm in §3.3.5 walks each row **once** and updates the signature
    of every column that has a 1 in it:

        sig[h][c] = min(sig[h][c], h(r))

    Doing it that way is the point. If you sort or re-scan per column you have
    written something correct that does not survive a dataset that does not fit
    in memory, and not fitting in memory is what this course is about.

    A column with no 1 in it keeps `inf`, the way the book leaves it.
    """
    inf = float("inf")
    n_cols, n_hashes = len(columns), len(hashes)
    sig = [[inf] * n_hashes for _ in range(n_cols)]

    # The row-wise view of the matrix: which columns hold a 1 in row r.
    # Building it is one sweep of the input, not one sweep per column, and it
    # is the order the data actually arrives in when the matrix is too big to
    # hold - a row can be read, used, and thrown away before the next one.
    rows = [[] for _ in range(n_rows)]
    for c, col in enumerate(columns):
        for r in col:
            if not 0 <= r < n_rows:
                raise ValueError(f"row {r} is outside 0..{n_rows - 1}")
            rows[r].append(c)

    for r in range(n_rows):                 # each row exactly once
        hv = [h(r) for h in hashes]         # hash the row number once per row,
        for c in rows[r]:                   # not once per column that holds it
            s = sig[c]
            for i in range(n_hashes):
                if hv[i] < s[i]:
                    s[i] = hv[i]
    return sig


def lsh_candidates(signatures, bands):
    """Split each signature into `bands` bands and hash each band.

    Two columns are candidates if they land in the same bucket for **at least
    one** band. Return {(i, j), ...} with i < j.

    R5 - what happens when `bands` does not divide the signature length:
    the rows are split **as evenly as possible** instead. With n rows and b
    bands, the first `n % b` bands get one extra row and the rest get `n // b`.

    The two alternatives are worse. Dropping the leftover rows throws away
    signature you already paid to compute, for nothing. Piling every leftover
    onto one band makes that band much taller than the others, and a taller
    band collides far less often, so it quietly contributes almost no recall
    while still costing a full pass. Splitting evenly keeps every band within
    one row of every other, which is also what keeps the S-curve of §3.4.2 -
    written for a single r - a fair description of what the code does.

    `bands` larger than the signature length is clamped: a band with no rows
    would put every column in the same bucket and make every pair a candidate.
    """
    if not signatures or bands <= 0:
        return set()
    n_rows = len(signatures[0])
    if n_rows == 0:
        return set()
    bands = min(bands, n_rows)

    base, extra = divmod(n_rows, bands)     # R5: spread the remainder
    spans, start = [], 0
    for b in range(bands):
        width = base + (1 if b < extra else 0)
        spans.append((start, start + width))
        start += width

    candidates = set()
    for lo, hi in spans:
        buckets = {}
        for c, sig in enumerate(signatures):
            buckets.setdefault(tuple(sig[lo:hi]), []).append(c)
        for members in buckets.values():
            if len(members) < 2:
                continue                    # a bucket of one collides with nobody
            for x in range(len(members)):
                for y in range(x + 1, len(members)):
                    i, j = members[x], members[y]
                    candidates.add((i, j) if i < j else (j, i))
    return candidates


# ------------------------------------------------------------------- harness
def columns_from_matrix(matrix):
    n_rows, n_cols = len(matrix), len(matrix[0])
    return [{r for r in range(n_rows) if matrix[r][c]} for c in range(n_cols)]


def verify():
    fails = 0

    def check(label, got, want):
        nonlocal fails
        ok = got == want
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<44} {got}"
              + ("" if ok else f"\n{'':>54}want {want}"))
        fails += not ok

    cols = columns_from_matrix(BOOK)
    try:
        # S1 = {0,3}, S4 = {0,2,3}: intersection 2, union 3
        check("jaccard(S1, S4)", round(jaccard(cols[0], cols[3]), 4), round(2 / 3, 4))
        check("jaccard(S1, S2)", jaccard(cols[0], cols[1]), 0.0)
        check("jaccard on empty sets", jaccard(set(), set()), 0)
    except NotImplementedError:
        print("  jaccard is still a stub"); return 1

    try:
        sig = minhash_signatures(cols, BOOK_HASHES, len(BOOK))
    except NotImplementedError:
        print("  minhash_signatures is still a stub"); return 1

    # Figure 3.4 in the textbook.
    check("signature of S1", sig[0], [1, 0])
    check("signature of S2", sig[1], [3, 2])
    check("signature of S3", sig[2], [0, 0])
    check("signature of S4", sig[3], [1, 0])

    try:
        cands = lsh_candidates([[1, 0], [3, 2], [0, 0], [1, 0]], bands=2)
    except NotImplementedError:
        print("  lsh_candidates is still a stub"); return 1
    # With one row per band, S1 and S4 are identical, so they must collide.
    check("S1 and S4 are candidates", (0, 3) in cands, True)
    check("S1 and S2 are not", (0, 1) in cands, False)

    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    if not fails:
        print("  Note that S1 and S4 agree in both signature positions, which "
              "estimates\n  their similarity as 1.0 when it is actually 2/3. "
              "Two hashes is not many.")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())
