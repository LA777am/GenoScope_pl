---
title: GenoScope
emoji: 🧬
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# GenoScope // Computational Genomic Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.6-F89939?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-Proprietary-lightgrey)](./README.md)

---

# Live Deployment

GenoScope is publicly accessible at:

https://genotech-genoscope.hf.space/

The system is deployed using **Hugging Face Spaces** with a containerized backend and a cloud-hosted PostgreSQL database.

---

# Project Overview

**GenoScope** is a computational genomics platform designed to perform DNA sequence analysis, machine learning based classification, mutation detection, and structural protein visualization within a unified web interface.

The system integrates classical bioinformatics algorithms, machine learning models, and interactive molecular visualization tools to provide a comprehensive genomic analysis environment.

Primary capabilities include:

- DNA sequence analysis and nucleotide composition
- open reading frame discovery
- machine learning based coding region classification
- promoter region prediction
- GC-content profiling
- mutation detection against curated disease reference genes
- comparative genomic similarity analysis
- three-dimensional protein mutation visualization

The platform demonstrates how computational biology pipelines can be implemented within a modern web-based architecture.

---

# System Architecture

| Layer | Technology | Role |
|------|------------|------|
| Frontend | HTML, CSS, JavaScript | User interface and visualization |
| Backend | Flask | REST API and processing engine |
| Machine Learning | Scikit-Learn | Coding and promoter classification |
| Database | Neon PostgreSQL | Persistent cloud data storage |
| Authentication | Google OAuth 2.0 | Secure user identity verification |
| Visualization | 3Dmol.js | Interactive molecular structure rendering |

Architecture flow:

User Interface  
↓  
Flask REST API  
↓  
Bioinformatics Algorithms / Machine Learning Models  
↓  
Neon PostgreSQL Database  

---

# Cloud Infrastructure

| Component | Technology | Purpose |
|----------|------------|---------|
| Hosting | Hugging Face Spaces | Application deployment |
| Database | Neon PostgreSQL | Cloud relational storage |
| Authentication | Google Cloud Console OAuth | User identity verification |
| ML Models | Scikit-learn | Genomic classification |
| Visualization | 3Dmol.js | Protein structure rendering |

---

# Core Functional Modules

## DNA Sequence Analysis

The system performs fundamental sequence analysis operations including:

- nucleotide composition
- sequence length calculation
- GC and AT percentage computation
- codon frequency analysis
- motif detection
- sliding window GC profiling

GC content formula:

GC% = (G + C) / Total Length × 100

This metric provides insight into genomic stability and gene density.

---

## Open Reading Frame Detection

Open Reading Frames (ORFs) are identified by scanning translated amino acid sequences.

Detection rules:

Start codon → Methionine (M)  
Stop codon → *

The algorithm scans all three forward reading frames and identifies candidate ORFs exceeding a configurable nucleotide threshold.

Output includes:

- reading frame
- nucleotide start position
- nucleotide end position
- amino acid length
- translated protein sequence

---

## DNA Translation

The platform converts DNA sequences into amino acid sequences using the standard genetic codon table.

Supported modes:

- single-frame translation
- six-frame translation (forward + reverse complement)

Example:

DNA: ATG GAA TTT  
AA :  M   E   F

---

# Machine Learning Modules

GenoScope integrates two machine learning classifiers trained on genomic sequence features.

---

## Coding Sequence Classifier

Predicts whether a DNA sequence represents a protein-coding region.

Algorithm: Random Forest

Feature vector (~70 features) includes:

- sequence length
- GC content
- AT content
- Shannon entropy
- ORF statistics
- codon usage distribution
- nucleotide frequency
- k-mer frequency patterns

Output:

coding  
or  
noncoding

Probability scores are also returned.

---

## Promoter Region Classifier

Identifies promoter sequences responsible for transcription initiation.

Algorithm: Random Forest

Feature vector (27 features) includes:

- GC and AT ratio
- sequence entropy
- motif presence
- motif spacing
- motif Hamming distance
- dinucleotide frequencies

Key promoter motifs:

-10 box → TATAAT  
-35 box → TTGACA

Output:

promoter  
or  
non_promoter

---

# Mutation Detection Engine

The mutation detection module compares a user DNA sequence with reference gene sequences.

Example reference genes:

- HBB
- CFTR
- BRCA1
- TP53

---

## Sequence Alignment

Alignment is performed using **Biopython global alignment**.

Algorithm:

Bio.pairwise2.align.globalms()

Scoring parameters:

| Parameter | Value |
|----------|------|
| Match score | +2 |
| Mismatch penalty | -1 |
| Gap open penalty | -2 |
| Gap extend penalty | -0.5 |

Global alignment ensures the entire sequence is optimally aligned before mutation classification.

---

## Mutation Classification

Detected mutations are classified according to their protein-level effect.

| Mutation Type | Description |
|---------------|-------------|
| Silent | Codon change but amino acid remains unchanged |
| Missense | Codon change alters amino acid |
| Nonsense | Mutation introduces premature stop codon |
| Frameshift | Insertion/deletion disrupts reading frame |

Each detected mutation reports:

- amino acid position
- reference codon
- mutated codon
- reference amino acid
- mutated amino acid

---

# Structural Mutation Visualization

GenoScope integrates **3Dmol.js** for molecular visualization.

Protein structures are retrieved using **Protein Data Bank (PDB) identifiers**.

Detected mutations are mapped to protein residues and displayed on interactive 3D structures.

Capabilities include:

- residue highlighting
- mutation labeling
- molecular rotation and zoom
- structural context visualization

This allows users to observe mutations within the three-dimensional protein environment.

---

# Sequence Comparison Engine

The platform compares two DNA sequences using three algorithms.

| Algorithm | Purpose |
|----------|---------|
| Levenshtein Distance | Measures edit operations between sequences |
| Longest Common Subsequence | Measures conserved subsequences |
| k-mer Similarity | Measures shared k-mer composition |

Final similarity score:

Similarity =  
0.4 × Edit Similarity  
+ 0.3 × LCS Ratio  
+ 0.3 × k-mer Similarity

---

# Sequence Preprocessing Pipeline

Before analysis, sequences undergo cleaning:

- removal of FASTA headers
- whitespace removal
- uppercase normalization
- filtering of non-ATGC characters

This ensures reliable downstream analysis.

---

# Authentication System

Authentication is implemented using **Google OAuth 2.0** configured through **Google Cloud Console**.

Authentication workflow:

1. User selects "Sign in with Google"
2. Google returns an ID token
3. Backend verifies token using Google libraries
4. Session is created after successful verification

Token verification method:

google.oauth2.id_token.verify_oauth2_token()

Passwords are never stored for OAuth users.

---

# Database Design

The system uses **Neon PostgreSQL** for persistent storage.

| Table | Purpose |
|------|---------|
| users | registered users |
| sequences | submitted DNA sequences |
| analyses | sequence analysis results |
| predictions | machine learning predictions |
| batches | batch processing records |
| comparisons | sequence similarity results |

Results are stored in structured JSON format for flexible querying.

---

# Deployment Architecture

User Browser  
↓  
Hugging Face Spaces (Flask Application)  
↓  
Machine Learning Models / Bioinformatics Algorithms  
↓  
Neon PostgreSQL Cloud Database  

Authentication flow:

User → Google OAuth → Token Verification → Flask Session

---

# Project Structure

| Path | Purpose |
|------|---------|
| app.py | Flask application and API routes |
| db.py | Database connection configuration |
| tools/dna_tools.py | Sequence analysis algorithms |
| tools/features.py | ML feature extraction |
| tools/mutation_tools.py | Mutation detection engine |
| references.py | Gene reference library |
| templates/ | HTML interface templates |
| static/ | JavaScript and CSS assets |

---

# Limitations

GenoScope is intended for **educational and computational research purposes**.

Limitations include:

- reference genes are partial curated sequences
- machine learning models are trained on limited datasets
- mutation visualization approximates residue mapping
- results should not be used for clinical diagnostics

---

# Future Improvements

Planned extensions include:

- deep learning based genomic models
- larger genomic reference libraries
- variant impact prediction
- enhanced structural mutation analysis
- integration with public genomic databases

---

# Conclusion

GenoScope demonstrates how bioinformatics algorithms, machine learning techniques, and interactive visualization technologies can be integrated into a unified computational genomics platform.

The system provides an accessible environment for exploring genomic data and understanding computational biology workflows.

---

GenoScope  
Computational Genomic Intelligence Platform