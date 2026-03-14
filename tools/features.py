

import numpy as np
from collections import Counter
from tools.dna_tools import clean_sequence, find_orfs
import re
# ALL possible codons
CODONS = [a+b+c for a in "ATGC" for b in "ATGC" for c in "ATGC"]


import math
from collections import Counter

def shannon_entropy(seq):
    """Return Shannon entropy of the DNA sequence."""
    seq = seq.upper()
    counts = Counter(seq)
    n = len(seq)
    if n == 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        p = count / n
        entropy -= p * math.log2(p)
    return entropy


def codon_freq_vector(seq):
    """Return normalized frequency of all 64 codons."""
    s = clean_sequence(seq)
    codons = [s[i:i+3] for i in range(0, len(s)-2, 3)]
    counts = Counter(codons)
    total = sum(counts.values()) or 1
    return np.array([counts.get(c, 0) / total for c in CODONS])



def orf_features(seq):
    """Longest ORF length + number of ORFs."""
    orfs = find_orfs(seq, min_len=0)
    lengths = [o['aa_length'] * 3 for o in orfs]
    longest = max(lengths) if lengths else 0
    count = len(lengths)
    return longest, count


def basic_features(seq):
    """Return length, GC fraction, AT fraction."""
    s = clean_sequence(seq)
    length = len(s)
    gc = (s.count("G") + s.count("C")) / length if length > 0 else 0
    at = (s.count("A") + s.count("T")) / length if length > 0 else 0
    return length, gc, at



def extract_features(seq):
    """
    Convert DNA sequence into a numeric vector suitable for ML.
    Order (new):
    [length, gc, at, entropy, longest_orf, orf_count, 64 codon frequencies]

    NOTE: entropy is the Shannon entropy (added to improve detection of
    low-complexity repetitive sequences).
    """
    # basic features (length, gc, at) - assumes basic_features returns those
    length, gc, at = basic_features(seq)

    # entropy feature (new)
    entropy = shannon_entropy(seq)

    # ORF related features
    longest_orf, orf_count = orf_features(seq)

    # codon frequency vector (64-d)
    codon_vec = codon_freq_vector(seq)

    # assemble final feature vector (as numpy array of floats)
    return np.array(
        [length, gc, at, entropy, longest_orf, orf_count] +
        codon_vec.tolist(),
        dtype=float
    )


MOTIF_10 = "TATAAT"
MOTIF_35 = "TTGACA"

def hamming_distance(a, b):
    return sum(ch1 != ch2 for ch1, ch2 in zip(a, b))

def motif_min_hamming_and_pos(seq, motif):
    """Return (best_hamming, best_position)."""
    Ls, Lm = len(seq), len(motif)
    if Ls < Lm:
        return Lm, -1
    best = Lm + 1
    best_pos = -1
    for i in range(Ls - Lm + 1):
        window = seq[i:i+Lm]
        hd = hamming_distance(window, motif)
        if hd < best:
            best = hd
            best_pos = i
    return best, best_pos

def motif_present_in_window(seq, motif, start, end, max_hd=1):
    """Check for an approximate motif match in a specific region."""
    if start < 0: start = 0
    if end > len(seq): end = len(seq)
    window = seq[start:end]
    L = len(motif)
    if len(window) < L:
        return 0
    for i in range(len(window) - L + 1):
        if hamming_distance(window[i:i+L], motif) <= max_hd:
            return 1
    return 0

def extract_promoter_features(seq):
    """Return 27 features for promoter classification."""
    seq = seq.upper()
    L = len(seq)

    # --- basic sequence statistics ---
    gc = (seq.count("G") + seq.count("C")) / L
    at = (seq.count("A") + seq.count("T")) / L

    # entropy
    from math import log2
    freqs = [seq.count(n)/L for n in "ATGC"]
    entropy = -sum(f * log2(f) for f in freqs if f > 0)

    # --- motif counts ---
    cnt10 = seq.count(MOTIF_10)
    cnt35 = seq.count(MOTIF_35)

    # --- best approximate match + positions ---
    best10_hd, best10_pos = motif_min_hamming_and_pos(seq, MOTIF_10)
    best35_hd, best35_pos = motif_min_hamming_and_pos(seq, MOTIF_35)

    # --- spacing feature ---
    if best10_pos >= 0 and best35_pos >= 0:
        spacing = abs(best10_pos - best35_pos)
    else:
        spacing = L  # penalize missing motifs

    # --- expected windows for UCI 57bp promoters ---
    win35_start, win35_end = 8, 22
    win10_start, win10_end = 22, 38

    present10 = motif_present_in_window(seq, MOTIF_10, win10_start, win10_end)
    present35 = motif_present_in_window(seq, MOTIF_35, win35_start, win35_end)

    # --- k-mer (2-mer) frequencies: 16 features ---
    kmers = [a+b for a in "ATGC" for b in "ATGC"]
    kfreqs = []
    for km in kmers:
        if L > 1:
            kfreqs.append(seq.count(km) / (L - 1))
        else:
            kfreqs.append(0.0)

    # Final vector = 27 features
    features = [
        gc,           # 0
        at,           # 1
        entropy,      # 2
        cnt10,        # 3
        cnt35,        # 4
        best10_hd,    # 5
        best35_hd,    # 6
        best10_pos,   # 7
        best35_pos,   # 8
        spacing,      # 9
        present10,    # 10
        present35     # 11
    ] + kfreqs        # +16 = total 27

    return np.array(features, dtype=float)