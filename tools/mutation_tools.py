from Bio import pairwise2
from Bio.Seq import Seq
from references import GENE_LIBRARY


def clean_sequence(seq: str) -> str:

    lines = seq.splitlines()
    cleaned = ""

    for line in lines:
        if not line.startswith(">"):
            cleaned += line.strip()

    cleaned = cleaned.upper()
    cleaned = "".join([n for n in cleaned if n in "ATGC"])

    return cleaned


def detect_mutation(disease_key: str, user_sequence: str):
    """ - Silent
        - Missense
        - Nonsense
        - Frameshift"""


    # 1. Validate Disease Key

    if disease_key not in GENE_LIBRARY:
        return {"error": "Unknown disease reference selected"}

    ref_data = GENE_LIBRARY[disease_key]
    ref_dna = ref_data["reference_dna"]


    # 2. Clean & Validate Input

    user_sequence = clean_sequence(user_sequence)

    if not user_sequence:
        return {"error": "Empty or invalid DNA sequence provided"}

    if any(n not in "ATGC" for n in user_sequence):
        return {"error": "Invalid DNA sequence. Only A/T/G/C allowed."}


    # 3. Frameshift Check (Pre-Alignment)

    length_difference = len(user_sequence) - len(ref_dna)

    if length_difference % 3 != 0:
        return {
            "gene": ref_data["gene_name"],
            "disease": disease_key,
            "mutation_detected": True,
            "mutation_type": "Frameshift Mutation",
            "total_mutations": 0,
            "mutations": [],
            "pdb_id": ref_data["pdb_id"],
            "reference_dna": ref_dna,
            "user_dna": user_sequence,
        }


    # 4. Global Alignment

    alignments = pairwise2.align.globalms(
        ref_dna,
        user_sequence,
        2,     # match score
        -1,    # mismatch penalty
        -2,    # gap open penalty
        -0.5   # gap extend penalty
    )

    if not alignments:
        return {"error": "Alignment failed"}

    aligned_ref, aligned_user, score, start, end = alignments[0]


    # 5. Remove Alignment Gaps

    clean_ref = aligned_ref.replace("-", "")
    clean_user = aligned_user.replace("-", "")

    # Ensure codon integrity
    clean_ref = clean_ref[:len(clean_ref) - (len(clean_ref) % 3)]
    clean_user = clean_user[:len(clean_user) - (len(clean_user) % 3)]


    # 6. Translate to Protein

    ref_protein = str(Seq(clean_ref).translate(to_stop=False))
    user_protein = str(Seq(clean_user).translate(to_stop=False))

    mutations = []
    min_len = min(len(ref_protein), len(user_protein))


    # 7. Codon-by-Codon Comparison

    for i in range(min_len):

        codon_start = i * 3

        ref_codon = clean_ref[codon_start:codon_start+3]
        user_codon = clean_user[codon_start:codon_start+3]

        if ref_codon != user_codon:

            ref_aa = ref_protein[i]
            user_aa = user_protein[i]

            if user_aa == "*":
                mutation_type = "Nonsense Mutation"

            elif ref_aa == user_aa:
                mutation_type = "Silent Mutation"

            else:
                mutation_type = "Missense Mutation"

            mutations.append({
                "position": i + 1,
                "mutation_type": mutation_type,
                "reference_aa": ref_aa,
                "mutated_aa": user_aa,
                "reference_codon": ref_codon,
                "mutated_codon": user_codon
            })


    # 8. Final Result

    return {
        "gene": ref_data["gene_name"],
        "description": ref_data.get("description", ""),
        "disease": disease_key,
        "mutation_detected": len(mutations) > 0,
        "mutation_type": (
            "Multiple Mutations" if len(mutations) > 1
            else mutations[0]["mutation_type"] if mutations
            else "No Mutation"
        ),
        "total_mutations": len(mutations),
        "mutations": mutations,
        "pdb_id": ref_data["pdb_id"],
        "reference_dna": clean_ref,
        "user_dna": clean_user,
    }