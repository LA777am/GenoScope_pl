from collections import Counter
import string
CODON_TABLE = {
    'TTT':'F','TTC':'F','TTA':'L','TTG':'L',
    'CTT':'L','CTC':'L','CTA':'L','CTG':'L',
    'ATT':'I','ATC':'I','ATA':'I','ATG':'M',
    'GTT':'V','GTC':'V','GTA':'V','GTG':'V',
    'TCT':'S','TCC':'S','TCA':'S','TCG':'S',
    'CCT':'P','CCC':'P','CCA':'P','CCG':'P', 
    'ACT':'T','ACC':'T','ACA':'T','ACG':'T',
    'GCT':'A','GCC':'A','GCA':'A','GCG':'A',
    'TAT':'Y','TAC':'Y','TAA':'*','TAG':'*',
    'CAT':'H','CAC':'H','CAA':'Q','CAG':'Q',
    'AAT':'N','AAC':'N','AAA':'K','AAG':'K',
    'GAT':'D','GAC':'D','GAA':'E','GAG':'E',
    'TGT':'C','TGC':'C','TGA':'*','TGG':'W',
    'CGT':'R','CGC':'R','CGA':'R','CGG':'R',
    'AGT':'S','AGC':'S','AGA':'R','AGG':'R',
    'GGT':'G','GGC':'G','GGA':'G','GGG':'G'
}

def clean_sequence(seq):
    """Remove invalid chars & uppercase."""
    newSeq= ""
    for i in seq:
        if i.isspace() or i.isdigit() or i in string.punctuation:
            continue
        newSeq+=i
    return ''.join([c for c in newSeq.upper() if c in ('A','T','G','C')])

def analyze_sequence(seq):
    """Compute GC%, AT%, codon freq, motifs."""
    s = clean_sequence(seq)
    n = len(s)
    counts = Counter(s)

    gc = (counts.get('G',0) + counts.get('C',0)) / n * 100 if n > 0 else 0
    at = (counts.get('A',0) + counts.get('T',0)) / n * 100 if n > 0 else 0

    codons = {}
    for i in range(0, n - (n % 3), 3):
        c = s[i:i+3]
        if len(c) == 3:
            codons[c] = codons.get(c, 0) + 1

    motifs = {
        'TATA': s.count('TATA'),
        'CpG_count': s.count('CG')
    }

    return {
        'length': n,
        'counts': dict(counts),
        'gc_percent': round(gc, 2),
        'at_percent': round(at, 2),
        'codon_frequency': codons,
        'motifs': motifs
    }

def translate_sequence(seq, frame=1):
    """Translate DNA → Protein in given reading frame."""
    s = clean_sequence(seq)
    start = max(0, frame - 1)
    prot = []

    for i in range(start, len(s) - 2, 3):
        codon = s[i:i+3]
        aa = CODON_TABLE.get(codon, 'X')
        if aa == '*':   # stop codon
            break
        prot.append(aa)
    return ''.join(prot)

# --- NEW: improved reverse complement ---
def reverse_complement(seq):
    """Return the reverse complement of a DNA sequence."""
    comp_table = str.maketrans("ATGCatgcNn", "TACGtacgNn")
    cleaned = clean_sequence(seq)
    return cleaned.translate(comp_table)[::-1]


# --- NEW: translate a sequence starting from an offset ---
def translate_from_frame(seq, offset):
    """Translate DNA starting from offset (0,1,2)."""
    s = clean_sequence(seq)
    prot = []
    for i in range(offset, len(s) - 2, 3):
        codon = s[i:i+3]
        aa = CODON_TABLE.get(codon, 'X')
        prot.append(aa)
    return ''.join(prot)


# --- NEW: full 6-frame translation ---
def translate_6_frames(seq):
    """
    Return translation of all 6 reading frames.
    Frames:
        frame_1, frame_2, frame_3,
        rc_frame_1, rc_frame_2, rc_frame_3
    """
    s = clean_sequence(seq)
    rc = reverse_complement(s)

    frames = {
        "frame_1": translate_from_frame(s, 0),
        "frame_2": translate_from_frame(s, 1),
        "frame_3": translate_from_frame(s, 2),
        "rc_frame_1": translate_from_frame(rc, 0),
        "rc_frame_2": translate_from_frame(rc, 1),
        "rc_frame_3": translate_from_frame(rc, 2)
    }

    return frames


def find_orfs(seq, min_len=90):
    """Find ORFs in all 6 reading frames."""
    s = clean_sequence(seq)
    results = []

    # Forward frames
    frames = []
    for f in range(3):
        aa_seq = []
        for i in range(f, len(s) - 2, 3):
            codon = s[i:i+3]
            aa = CODON_TABLE.get(codon,'X')
            aa_seq.append(aa)
        frames.append(''.join(aa_seq))

    for f_idx, aa_seq in enumerate(frames):
        i = 0
        while i < len(aa_seq):
            if aa_seq[i] == 'M':
                j = i + 1
                while j < len(aa_seq) and aa_seq[j] != '*':
                    j += 1

                aa_len = j - i
                if aa_len * 3 >= min_len:
                    start_nt = f_idx + i * 3 + 1
                    end_nt = f_idx + j * 3 + 3
                    results.append({
                        'frame': f_idx + 1,
                        'start_nt': start_nt,
                        'end_nt': end_nt,
                        'aa_length': aa_len,
                        'protein_seq': aa_seq[i:j]
                    })
                i = j + 1
            else:
                i += 1

    # Reverse strand
    rc = reverse_complement(s)
    frames_rc = []

    for f in range(3):
        aa_seq = []
        for i in range(f, len(rc) - 2, 3):
            codon = rc[i:i+3]
            aa = CODON_TABLE.get(codon,'X')
            aa_seq.append(aa)
        frames_rc.append(''.join(aa_seq))

    for f_idx, aa_seq in enumerate(frames_rc):
        i = 0
        while i < len(aa_seq):
            if aa_seq[i] == 'M':
                j = i + 1
                while j < len(aa_seq) and aa_seq[j] != '*':
                    j += 1

                aa_len = j - i
                if aa_len * 3 >= min_len:
                    start_nt = -(f_idx + j * 3)
                    end_nt = -(f_idx + i * 3)
                    results.append({
                        'frame': f'rc_{f_idx+1}',
                        'start_nt': start_nt,
                        'end_nt': end_nt,
                        'aa_length': aa_len,
                        'protein_seq': aa_seq[i:j]
                    })
                i = j + 1
            else:
                i += 1

    return results


def top_codons(seq, n=10, frame=1):
    """Return top n codons in given frame (1-based frame: 1,2,3)."""
    s = clean_sequence(seq)
    start = max(0, frame-1)
    codon_counts = {}
    for i in range(start, len(s)-2, 3):
        codon = s[i:i+3]
        if len(codon)==3:
            codon_counts[codon] = codon_counts.get(codon, 0) + 1
    # sort by count desc
    items = sorted(codon_counts.items(), key=lambda x: x[1], reverse=True)
    return [{'codon': c, 'count': cnt} for c, cnt in items[:n]]

def sliding_gc_windows(seq, window=50, step=1):
    """Return list of dicts: [{'start':1,'end':50,'gc':xx}, ...]"""
    s = clean_sequence(seq)
    out = []
    n = len(s)
    if window <= 0 or step <= 0:
        return out
    for i in range(0, n - window + 1, step):
        fragment = s[i:i+window]
        stats = analyze_sequence(fragment)
        out.append({'start': i+1, 'end': i+window, 'gc_percent': stats['gc_percent']})
    return out

def edit_distance(a, b):
    """Levenshtein distance using DP."""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost
            )
    return dp[n][m]


def longest_common_subsequence(a, b):
    """Returns length of LCS."""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n):
        for j in range(m):
            if a[i] == b[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])

    return dp[n][m]


def kmer_similarity(a, b, k=5):
    """Jaccard similarity of k-mers."""
    if len(a) < k or len(b) < k:
        return 0.0

    kmers_a = set(a[i:i+k] for i in range(len(a) - k + 1))
    kmers_b = set(b[i:i+k] for i in range(len(b) - k + 1))

    intersection = kmers_a & kmers_b
    union = kmers_a | kmers_b

    return len(intersection) / len(union)


