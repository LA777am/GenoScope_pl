def parse_fasta_sequences(content: str):
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    # Handle UTF-8 BOM
    content = content.lstrip('\ufeff')

    sequences = []
    current = []
    header_count = 0
    
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            header_count += 1
            if current:
                sequences.append("".join(current))
                current = []
        else:
            current.append(line)

    if current:
        sequences.append("".join(current))

    if header_count != len(sequences):
        print(
            f"WARNING: FASTA mismatch — headers={header_count}, sequences={len(sequences)}"
        )

    return sequences