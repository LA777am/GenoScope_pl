from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import joblib
import json
from psycopg2.extras import RealDictCursor
from tools.mutation_tools import detect_mutation
from utils.fasta import parse_fasta_sequences
from db import get_db, close_db
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash
from tools.dna_tools import (

    edit_distance,
    longest_common_subsequence,
    kmer_similarity
)
from tools.features import extract_features, extract_promoter_features
from tools.dna_tools import (
    analyze_sequence,
    translate_sequence,
    find_orfs,
    top_codons,
    sliding_gc_windows,
    clean_sequence
)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "genoscope-dev-key-2026"

model = joblib.load("coding_rf_v2.pkl")

promoter_model = joblib.load("promoter_rf_v2.pkl")



@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.json or {}
    seq = data.get('sequence', '').upper().strip()
    if not seq:
        return jsonify({'error': 'No sequence provided'}), 400


    cleaned = clean_sequence(seq)
    base_analysis = analyze_sequence(cleaned)
    orfs = find_orfs(cleaned, min_len=30)

    analysis_payload = {
        "cleaned_sequence": cleaned,
        "length": base_analysis["length"],
        "counts": base_analysis["counts"],
        "gc_percent": base_analysis["gc_percent"],
        "at_percent": base_analysis["at_percent"],
        "codon_frequency": base_analysis["codon_frequency"],
        "motifs": base_analysis["motifs"],
        "orfs_ui": orfs
    }


    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get latest batch
        cur.execute("""
            SELECT batch_id FROM batches
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        batch = cur.fetchone()

        if not batch:
            cur.execute("""
                INSERT INTO batches (batch_name, status, user_id)
                VALUES (%s, %s, %s)
                RETURNING batch_id
            """, ("single_analysis", "active", user_id))
            batch_id = cur.fetchone()["batch_id"]
        else:
            batch_id = batch["batch_id"]

        # Insert sequence
        cur.execute("""
            INSERT INTO sequences (
                batch_id,
                user_id,
                raw_sequence,
                cleaned_sequence,
                length,
                gc_percent
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING sequence_id
        """, (
            batch_id,
            user_id,
            seq,
            cleaned,
            len(cleaned),
            base_analysis["gc_percent"]
        ))

        sequence_id = cur.fetchone()["sequence_id"]
        cur.execute("""
            INSERT INTO analysis_history (
                user_id,
                sequence_id,
                sequence,
                analysis_type,
                result_json
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            sequence_id,
            cleaned,
            "single_sequence",
            json.dumps({
                "length": base_analysis["length"],
                "gc_percent": base_analysis["gc_percent"]
            })
        ))
        print("HISTORY INSERTED FOR USER", user_id)
        # Insert GC analysis
        cur.execute("""
            INSERT INTO analyses (sequence_id, analysis_type, results)
            VALUES (%s, %s, %s)
        """, (
            sequence_id,
            "gc_content",
            json.dumps({
                "gc_percent": base_analysis["gc_percent"]
            })
        ))
        cur.execute("""
            INSERT INTO analyses (sequence_id, analysis_type, results)
            VALUES (%s, %s, %s)
        """, (
            sequence_id,
            "orfs",
            json.dumps(orfs)
        ))
        cur.execute("""
            INSERT INTO analyses (sequence_id, analysis_type, results)
            VALUES (%s, %s, %s)
        """, (
            sequence_id,
            "codon_frequency",
            json.dumps(base_analysis["codon_frequency"])
        ))
        cur.execute("""
            INSERT INTO analyses (sequence_id, analysis_type, results)
            VALUES (%s, %s, %s)
        """, (
            sequence_id,
            "motifs",
            json.dumps(base_analysis["motifs"])
        ))
        conn.commit()

        analysis_payload["sequence_id"] = sequence_id

    except Exception as e:
        raise 

    finally:
        try:
            cur.close()
        except:
            pass

    # ---------- PHASE 3: RESPONSE ----------
    return jsonify(analysis_payload)

@app.route('/api/sequences/<int:sequence_id>/full', methods=['GET'])
def get_full_sequence(sequence_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # ---- sequence ----
        cur.execute("""
            SELECT sequence_id, raw_sequence, cleaned_sequence, length, gc_percent
            FROM sequences
            WHERE sequence_id = %s
        """, (sequence_id,))
        seq = cur.fetchone()

        if not seq:
            return jsonify({"error": "Sequence not found"}), 404


        cur.execute("""
            SELECT analysis_type, results
            FROM analyses
            WHERE sequence_id = %s
        """, (sequence_id,))
        analyses_rows = cur.fetchall()

        analyses = {
            row["analysis_type"]: row["results"]
            for row in analyses_rows
        }


        cur.execute("""
            SELECT model_type, predicted_label, confidence, features_used
            FROM predictions
            WHERE sequence_id = %s
        """, (sequence_id,))
        pred_rows = cur.fetchall()

        predictions = {
            row["model_type"]: {
                "label": row["predicted_label"],
                "confidence": row["confidence"],
                "features": row["features_used"]
            }
            for row in pred_rows
        }

        return jsonify({
            "sequence": seq,
            "analyses": analyses,
            "predictions": predictions
        })

    finally:
        cur.close()

@app.route('/api/translate', methods=['POST'])
def api_translate():
    data = request.json or {}
    seq = data.get('sequence', '').upper().strip()
    if not seq:
        return jsonify({'error': 'No sequence provided'}), 400

    aa = translate_sequence(seq)
    return jsonify({'protein': aa})

@app.route('/api/translate6', methods=['POST'])
def api_translate6():
    data = request.json or {}
    seq = data.get('sequence', '').upper().strip()

    if not seq:
        return jsonify({'error': 'No sequence provided'}), 400

    from tools.dna_tools import translate_6_frames
    result = translate_6_frames(seq)
    return jsonify(result)

@app.route('/api/orfs', methods=['POST'])
def api_orfs():
    data = request.json or {}
    seq = data.get('sequence', '').upper().strip()
    min_len = int(data.get('min_len', 90))  # NEW: dynamic

    if not seq:
        return jsonify({'error': 'No sequence provided'}), 400

    orf_list = find_orfs(seq, min_len=min_len)
    return jsonify({'orfs': orf_list})


@app.route('/api/top_codons', methods=['POST'])
def api_top_codons():
    data = request.json or {}
    seq = data.get('sequence', '').upper().strip()
    n = int(data.get('n', 12))
    frame = int(data.get('frame', 1))

    if not seq:
        return jsonify({'error': 'No sequence provided'}), 400

    result = top_codons(seq, n=n, frame=frame)
    return jsonify({'top_codons': result})


@app.route('/api/sliding_gc', methods=['POST'])
def api_sliding_gc():
    data = request.json or {}
    seq = data.get('sequence', '').upper().strip()
    window = int(data.get('window', 50))
    step = int(data.get('step', 1))

    if not seq:
        return jsonify({'error': 'No sequence provided'}), 400

    result = sliding_gc_windows(seq, window=window, step=step)
    return jsonify({'windows': result})
@app.route('/api/predict_coding', methods=['POST'])
def api_predict_coding():
    data = request.json or {}
    raw_seq = data.get("sequence", "")
    sequence_id = data.get("sequence_id")
    if not sequence_id:
        return jsonify({"error": "sequence_id missing"}), 400
    if raw_seq is None:
            raw_seq = ""
    # keep original for record
    submitted = str(raw_seq)

    # Basic cleaning same as in dna_tools.clean_sequence
    cleaned = clean_sequence(submitted)

    if not cleaned:
        return jsonify({"error": "No valid ATGC bases found after cleaning", "submitted": submitted}), 400
    if len(cleaned) < 300:
        return jsonify({
            "error": "Sequence too short for ML classification. Minimum length required: 300 bp.",
            "length": len(cleaned)
        }), 400
    # Extract features (full vector)
    feats = extract_features(cleaned)
    feats_array = np.array(feats).reshape(1, -1)

    # model prediction
    proba = model.predict_proba(feats_array)[0][1]
    pred_label = "coding" if proba >= 0.5 else "noncoding"

    # Build a small features summary to return (length, gc, at, entropy, longest_orf, orf_count)
    # NOTE: feature order is [length, gc, at, entropy, longest_orf, orf_count, ...]
    length = int(feats[0])
    gc = float(feats[1])
    at = float(feats[2])
    entropy = float(feats[3])
    longest_orf = int(feats[4])
    orf_count = int(feats[5])
    # ---------- DB: store prediction ----------
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("""
            INSERT INTO predictions (
                sequence_id,
                model_type,
                predicted_label,
                confidence,
                features_used
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            sequence_id,
            "coding",
            pred_label,
            float(proba),
            json.dumps({
                "length": length,
                "gc": gc,
                "at": at,
                "entropy": entropy,
                "longest_orf": longest_orf,
                "orf_count": orf_count
            })
        ))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Prediction insert failed:", e)

    finally:
        cur.close()
    # Log to server console for debugging
    print("=== PREDICTION DEBUG ===")
    print("Submitted:", repr(submitted))
    print("Cleaned:", cleaned)
    print("Features summary:", {
    "length": length,
    "gc": gc,
    "at": at,
    "entropy": entropy,
    "longest_orf": longest_orf,
    "orf_count": orf_count
})
    print("Raw probability:", float(proba))
    print("=========================")

    return jsonify({
        "prediction": pred_label,
        "probability": float(proba),
        "cleaned_sequence": cleaned,
        "features_summary": {
            "length": length,
            "gc": gc,
            "at": at,
            "entropy": entropy,
            "longest_orf": longest_orf,
            "orf_count": orf_count
        },
        # "feature_vector": feats.tolist()  # optional - uncomment for deeper debug
    })
# ==========================
# PROMOTER PREDICTION ENDPOINT
# ==========================

@app.route('/api/upload_fasta', methods=['POST'])
def api_upload_fasta():
    """
    Accepts a FASTA file upload, extracts sequence,
    and returns the cleaned sequence for analysis.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    f = request.files['file']

    if f.filename == '':
        return jsonify({"error": "No file selected"}), 400

    content = f.read().decode('utf-8', errors='ignore')

    # Parse FASTA: ignore header lines starting with ">"
    seq_lines = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith(">"):
            continue
        seq_lines.append(line)

    raw_seq = "".join(seq_lines)

    from tools.dna_tools import clean_sequence
    cleaned = clean_sequence(raw_seq)

    if not cleaned:
        return jsonify({"error": "No valid ATGC bases found in FASTA"}), 400

    return jsonify({
        "original_length": len(raw_seq),
        "cleaned_length": len(cleaned),
        "cleaned_sequence": cleaned
    })

@app.route('/api/predict_promoter', methods=['POST'])
def api_predict_promoter():

    data = request.json or {}
    raw_seq = data.get("sequence", "")
    sequence_id = data.get("sequence_id")
    if not sequence_id:
        return jsonify({"error": "sequence_id missing"}), 400
    submitted = str(raw_seq)

    from tools.dna_tools import clean_sequence
    cleaned = clean_sequence(submitted)

    if len(cleaned) < 57:
        return jsonify({
            "error": "Promoter model requires minimum 57 bp sequence.",
            "length": len(cleaned)
        }), 400


    try:
        feats = extract_promoter_features(cleaned)
        print("Promoter feature length:", len(feats))
        feats_array = np.array(feats).reshape(1, -1)
        prob = promoter_model.predict_proba(feats_array)[0][1]


        def scan_motif(seq, motif, max_hd=1):
            hits = []
            L = len(motif)
            for i in range(len(seq) - L + 1):
                window = seq[i:i+L]
                hd = sum(a != b for a, b in zip(window, motif))
                if hd <= max_hd:
                    hits.append({"pos": i, "seq": window})
            return hits

        motifs = {
            "-35": scan_motif(cleaned, "TTGACA"),
            "-10": scan_motif(cleaned, "TATAAT")
        }

        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cur.execute("""
                INSERT INTO predictions (
                    sequence_id,
                    model_type,
                    predicted_label,
                    confidence,
                    features_used
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                sequence_id,
                "promoter",
                "promoter" if prob >= 0.5 else "non_promoter",
                float(prob),
                json.dumps({
                    "motifs": {
                        "-10": len(motifs["-10"]),
                        "-35": len(motifs["-35"])
                    }
                })
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            print("Promoter prediction insert failed:", e)

        finally:
            cur.close()
    except Exception as e:
        return jsonify({
        "error": "Promoter feature extraction failed",
        "details": str(e)
        }), 500

    

    return jsonify({
    "is_promoter": bool(prob >= 0.5),
    "probability": float(prob),
    "motifs": motifs,
    "cleaned_sequence": cleaned
})
@app.route('/api/compare_sequences', methods=['POST'])
def api_compare_sequences():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}

    seq1 = clean_sequence(data.get("seq1", ""))
    seq2 = clean_sequence(data.get("seq2", ""))

    if not seq1 or not seq2:
        return jsonify({"error": "Both sequences are required"}), 400

    ed = edit_distance(seq1, seq2)
    max_len = max(len(seq1), len(seq2))
    ed_similarity = 1 - (ed / max_len)

    lcs_len = longest_common_subsequence(seq1, seq2)
    lcs_ratio = lcs_len / min(len(seq1), len(seq2))

    kmer_sim = kmer_similarity(seq1, seq2, k=5)

    final_score = round(
        0.4 * ed_similarity +
        0.3 * lcs_ratio +
        0.3 * kmer_sim,
        3
    )

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO comparisons (
            user_id,
            metrics,
            final_score
        )
        VALUES (%s, %s, %s)
    """, (
        user_id,
        json.dumps({
            "edit_similarity": round(ed_similarity, 3),
            "lcs_ratio": round(lcs_ratio, 3),
            "kmer_similarity": round(kmer_sim, 3)
        }),
        final_score
    ))

    conn.commit()
    cur.close()

    return jsonify({
        "normalized_edit_similarity": round(ed_similarity, 3),
        "lcs_ratio": round(lcs_ratio, 3),
        "kmer_similarity": round(kmer_sim, 3),
        "final_similarity_score": final_score
    })
@app.teardown_appcontext
def teardown_db(exception):
    close_db(exception)

@app.route('/api/batches', methods=['POST'])
def create_batch():
    data = request.json or {}
    batch_name = data.get("batch_name", "Batch_Auto")

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            INSERT INTO batches (batch_name)
            VALUES (%s)
            RETURNING batch_id, batch_name, status
            """,
            (batch_name,)
        )
        batch = cur.fetchone()
        conn.commit()

        return jsonify(batch), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:      
        cur.close()



@app.route('/api/batches/<int:batch_id>/summary', methods=['GET'])
def batch_summary(batch_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # total sequences
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM sequences
            WHERE batch_id = %s
        """, (batch_id,))
        total_sequences = cur.fetchone()["total"]

        if total_sequences == 0:
            return jsonify({"error": "Empty batch"}), 404

        # average GC
        cur.execute("""
            SELECT AVG((results->>'gc_percent')::float) AS avg_gc
            FROM analyses
            WHERE analysis_type = 'gc_content'
            AND sequence_id IN (
                SELECT sequence_id FROM sequences WHERE batch_id = %s
            )
        """, (batch_id,))
        avg_gc = cur.fetchone()["avg_gc"]

        # coding predictions
        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM predictions
            WHERE model_type = 'coding'
            AND predicted_label = 'coding'
            AND sequence_id IN (
                SELECT sequence_id FROM sequences WHERE batch_id = %s
            )
        """, (batch_id,))
        coding_count = cur.fetchone()["cnt"]

        # promoter predictions
        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM predictions
            WHERE model_type = 'promoter'
            AND predicted_label = 'promoter'
            AND sequence_id IN (
                SELECT sequence_id FROM sequences WHERE batch_id = %s
            )
        """, (batch_id,))
        promoter_count = cur.fetchone()["cnt"]

        return jsonify({
            "batch_id": batch_id,
            "total_sequences": total_sequences,
            "avg_gc": round(avg_gc, 2) if avg_gc else None,
            "coding": {
                "count": coding_count,
                "percent": round(coding_count / total_sequences * 100, 1)
            },
            "promoter": {
                "count": promoter_count,
                "percent": round(promoter_count / total_sequences * 100, 1)
            }
        })

    finally:
        cur.close()


@app.route('/api/batches/<int:batch_id>/gc_distribution', methods=['GET'])
def batch_gc_distribution(batch_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("""
            SELECT gc_percent
            FROM sequences
            WHERE batch_id = %s
            ORDER BY gc_percent
        """, (batch_id,))

        rows = cur.fetchall()
        gc_values = [row["gc_percent"] for row in rows]

        return jsonify({
            "batch_id": batch_id,
            "count": len(gc_values),
            "gc_values": gc_values
        })

    finally:
        cur.close()



@app.route('/api/batches/<int:batch_id>/promoter_summary')
def batch_promoter_summary(batch_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT p.predicted_label, COUNT(*) 
        FROM predictions p
        JOIN sequences s ON p.sequence_id = s.sequence_id
        WHERE s.batch_id = %s
          AND p.model_type = 'promoter'
        GROUP BY p.predicted_label
    """, (batch_id,))

    rows = cur.fetchall()
    cur.close()

    summary = {"promoter": 0, "non_promoter": 0}
    for row in rows:
        summary[row["predicted_label"]] = row["count"]

    total = summary["promoter"] + summary["non_promoter"]

    return jsonify({
        "batch_id": batch_id,
        "counts": summary,
        "total": total,
        "percentages": {
            "promoter": round((summary["promoter"] / total) * 100, 2) if total else 0,
            "non_promoter": round((summary["non_promoter"] / total) * 100, 2) if total else 0
        }
    })

@app.route('/api/batches/<int:batch_id>/confidence_distribution')
def batch_confidence_distribution(batch_id):
    model = request.args.get("model", "coding")

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT p.confidence
        FROM predictions p
        JOIN sequences s ON p.sequence_id = s.sequence_id
        WHERE s.batch_id = %s
          AND p.model_type = %s
        ORDER BY p.confidence
    """, (batch_id, model))

    confidences = [row["confidence"] for row in cur.fetchall()]
    cur.close()

    return jsonify({
        "batch_id": batch_id,
        "model": model,
        "count": len(confidences),
        "confidences": confidences
    })




@app.route('/api/batch/upload_fasta', methods=['POST'])

def api_batch_upload_fasta():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    print("🔥 BATCH FASTA ENDPOINT HIT")
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f = request.files['file']
    if f.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    print("==== RAW FASTA DEBUG ====")
    print("Filename:", f.filename)
    
    print("==========================")

    content = f.read().decode('utf-8', errors='ignore')
    raw_sequences = parse_fasta_sequences(content)


    print("=== FASTA DEBUG ===")
    print("Raw content preview:")
    print(content[:500])
    print("Detected sequences:", len(raw_sequences))
    for i, s in enumerate(raw_sequences):
        print(f"Seq {i+1} length:", len(s))
    print("===================")

    if not raw_sequences:
        return jsonify({"error": "No valid FASTA sequences found"}), 400

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 1️⃣ Create batch
        cur.execute("""
            INSERT INTO batches (batch_name, user_id)
            VALUES (%s, %s)
            RETURNING batch_id
        """, (f.filename,user_id))
        batch_id = cur.fetchone()["batch_id"]

        inserted = 0

        # 2️⃣ Process each sequence
        for raw_seq in raw_sequences:
            cleaned = clean_sequence(raw_seq)
            if not cleaned:
                continue

            # ---- ANALYSIS ----
            base_analysis = analyze_sequence(cleaned)
            orfs = find_orfs(cleaned, min_len=30)

            # ---- INSERT SEQUENCE ----
            cur.execute("""
                INSERT INTO sequences (
                    batch_id,
                    user_id,
                    raw_sequence,
                    cleaned_sequence,
                    length,
                    gc_percent
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING sequence_id
            """, (
                batch_id,
                user_id,
                raw_seq,
                cleaned,
                len(cleaned),
                base_analysis["gc_percent"]
            ))
            sequence_id = cur.fetchone()["sequence_id"]

            # ---- STORE ANALYSES ----
            cur.execute("""
                INSERT INTO analyses (sequence_id, analysis_type, results)
                VALUES (%s, %s, %s)
            """, (sequence_id, "gc_content",
                  json.dumps({"gc_percent": base_analysis["gc_percent"]})))

            cur.execute("""
                INSERT INTO analyses (sequence_id, analysis_type, results)
                VALUES (%s, %s, %s)
            """, (sequence_id, "orfs", json.dumps(orfs)))

            # ---- ML: CODING ----
            if len(cleaned) >= 300:
                feats = extract_features(cleaned)
                proba = model.predict_proba(np.array(feats).reshape(1, -1))[0][1]
                label = "coding" if proba >= 0.5 else "noncoding"

                cur.execute("""
                    INSERT INTO predictions (
                        sequence_id, model_type, predicted_label, confidence, features_used
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    sequence_id,
                    "coding",
                    label,
                    float(proba),
                    json.dumps({"length": feats[0], "gc": feats[1]})
                ))

            # ---- ML: PROMOTER ----
            if len(cleaned) >= 57:
                feats = extract_promoter_features(cleaned)
                prob = promoter_model.predict_proba(
                    np.array(feats).reshape(1, -1)
                )[0][1]

                cur.execute("""
                    INSERT INTO predictions (
                        sequence_id, model_type, predicted_label, confidence, features_used
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    sequence_id,
                    "promoter",
                    "promoter" if prob >= 0.5 else "non_promoter",
                    float(prob),
                    json.dumps({})
                ))

            inserted += 1
                    # ✅ Mark batch as completed
        cur.execute("""
            UPDATE batches
            SET status = 'completed'
            WHERE batch_id = %s
        """, (batch_id,))
        conn.commit()

        return jsonify({
            "batch_id": batch_id,
            "total_sequences": inserted
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()



GOOGLE_CLIENT_ID = "242394180716-08pne04nsp1ae5hf5pjeuch26hl3q442.apps.googleusercontent.com"

@app.route("/auth/google", methods=["POST"])
def google_auth():
    data = request.json or {}
    token = data.get("credential")

    if not token:
        return jsonify({"success": False, "error": "Missing Google token payload"}), 400

    try:
        # 1. Cryptographically verify the JWT signature with Google's public keys
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )

        # 2. Extract the verified email
        email = idinfo.get('email')
        if not email:
            return jsonify({"success": False, "error": "Email not found in Google payload"}), 400

        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # 3. UPSERT: Find the user, or create them instantly
        cur.execute("SELECT user_id FROM users WHERE username = %s", (email,))
        user = cur.fetchone()

        if user:
            # Returning user -> Grab their ID
            user_id = user["user_id"]
        else:
            # First time user -> Provision account
            # We insert "OAUTH_MANAGED" as the password so it doesn't violate DB constraints
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING user_id",
                (email, "OAUTH_MANAGED")
            )
            user_id = cur.fetchone()["user_id"]
            conn.commit()

        cur.close()

        # 4. Establish the Flask Session (Log them in)
        session["user_id"] = user_id
        session["username"] = email

        return jsonify({"success": True, "message": "Authentication successful"})

    except ValueError:
        # If the token is expired, forged, or invalid
        return jsonify({"success": False, "error": "Invalid Google token signature"}), 401
    except Exception as e:
        print("Auth Exception:", e)
        return jsonify({"success": False, "error": "Internal Server Error"}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT id, analysis_type, created_at, sequence
        FROM analysis_history
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 20
    """, (user_id,))

    rows = cur.fetchall()
    cur.close()

    return jsonify(rows), 200

@app.route("/api/history/batch", methods=["GET"])
def get_batch_history():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            b.batch_id,
            b.batch_name,
            b.created_at,
            COUNT(s.sequence_id) AS total_sequences
        FROM batches b
        LEFT JOIN sequences s ON s.batch_id = b.batch_id
        WHERE b.user_id = %s
        GROUP BY b.batch_id
        ORDER BY b.created_at DESC
        LIMIT 20
    """, (user_id,))

    rows = cur.fetchall()
    cur.close()
    return jsonify(rows), 200


@app.route("/api/batches/<int:batch_id>/sequences", methods=["GET"])
def get_batch_sequences(batch_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            sequence_id,
            LENGTH(cleaned_sequence) AS length,
            gc_percent,
            created_at
        FROM sequences
        WHERE batch_id = %s AND user_id = %s
        ORDER BY created_at DESC
    """, (batch_id, user_id))

    rows = cur.fetchall()
    cur.close()
    return jsonify(rows), 200


@app.route("/api/history/comparisons", methods=["GET"])
def get_comparison_history():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            comparison_id,
            final_score,
            metrics,
            created_at
        FROM comparisons
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 20
    """, (user_id,))

    rows = cur.fetchall()
    cur.close()

    return jsonify(rows), 200

@app.route("/api/mutation_check", methods=["POST"])
def mutation_check():
    data = request.json or {}

    disease = data.get("disease")
    sequence = data.get("sequence", "").upper().strip()

    if not disease or not sequence:
        return jsonify({"error": "Disease and sequence required"}), 400

    result = detect_mutation(disease, sequence)

    return jsonify(result)


@app.route('/')
def index():
    return render_template('intro.html')

@app.route('/auth')
def auth():
    return render_template('auth.html')

@app.route('/mode-select')
def mode_select():
    return render_template('mode_select.html')

@app.route('/single')
def single_analysis():
    return render_template('index1.html')

@app.route('/batch')
def batch_analysis():
    return render_template('batch.html')

@app.route('/compare')
def compare():
    return render_template('compare.html')

@app.route('/mutation')
def mutation_mode():
    return render_template('mutation.html')

@app.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()   # removes user_id, username, everything
    return jsonify({"success": True})

#this must be last
if __name__ == '__main__':
    app.run(debug=True, port=5000)