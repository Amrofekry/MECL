import serial
import time
import pandas as pd
import numpy as np
import sys

# --- CONFIGURATION ---
PORT = 'COM3'
LIVE_FILE = "live_test.csv"
DURATION_SEC = 60


# ---------------------

# ==========================================
# PART 1: RECORDING ENGINE (Standard)
# ==========================================
def record_live_signal():
    print(f"\n--- 2. RECORDING LIVE SIGNAL ({DURATION_SEC}s) ---")
    try:
        df = pd.read_csv('ecg_data.csv')
        data = (df['dac'].tolist() * 100)[:15000]
    except:
        print("[ERR] ecg_data.csv missing.")
        return False

    try:
        ser = serial.Serial(PORT, 115200, timeout=1)
        time.sleep(2)
    except:
        print(f"[ERR] Check {PORT}.")
        return False

    log = []
    print(" >> Recording... (Don't touch the circuit!)")

    start_time = time.time()
    for i, val in enumerate(data):
        elapsed = time.time() - start_time
        if elapsed > DURATION_SEC: break

        if i % 1000 == 0:
            sys.stdout.write(f"\r   Scanning... {int(DURATION_SEC - elapsed)}s left   ")
            sys.stdout.flush()

        ser.write(f"{val}\n".encode())
        try:
            line = ser.readline().decode().strip()
            if ',' in line:
                s, r = line.split(',')
                log.append([int(s), int(r)])
        except:
            pass
        time.sleep(0.005)

    ser.close()
    if len(log) > 100:
        pd.DataFrame(log, columns=['Sent', 'Recv']).to_csv(LIVE_FILE, index=False)
        print("\n >> Scan Complete.")
        return True
    return False


# ==========================================
# PART 2: FEATURE EXTRACTION
# ==========================================
def get_features(filename):
    try:
        df = pd.read_csv(filename)
        sent = df['Sent'];
        recv = df['Recv']

        # 1. Similarity (Shape)
        sim = sent.corr(recv)

        # 2. Strength (Amplitude Ratio)
        if sent.std() == 0:
            ratio = 0
        else:
            ratio = recv.std() / sent.std()

        # 3. Dropouts
        drops = (recv < 5).sum()

        return sim, ratio, drops
    except:
        return None


def train_ai():
    print("\n--- 1. TRAINING AI (LEARNING PHASE) ---")
    files = ["healthy.csv", "gain.csv", "conn.csv", "power.csv"]
    brain = {}

    for f in files:
        feats = get_features(f)
        if feats:
            name = f.replace(".csv", "").upper()
            brain[name] = feats
            print(f" [LEARNED] {name:7} -> Shape={feats[0]:.2f} | Strength={feats[1]:.2f} | Drops={feats[2]}")

    return brain


# ==========================================
# PART 3: THE "EXPLAINABLE" COMPARISON ENGINE
# ==========================================
def diagnose(target_file, brain):
    # 1. Get Live Stats
    feats = get_features(target_file)
    if not feats: return "File Error"

    t_sim, t_str, t_drops = feats

    print("\n--- 3. DETAILED ANALYSIS ---")
    print(f" [INPUT] Shape={t_sim:.2f} | Strength={t_str:.2f} | Drops={t_drops}")
    print("-" * 65)
    print(f" {'PROFILE':<10} | {'d_SHAPE':<10} | {'d_STR':<10} | {'d_DROPS':<10} | {'SCORE (Low=Best)'}")
    print("-" * 65)

    best_match_name = "UNKNOWN"
    lowest_score = 99999999

    # 2. Compare against every profile
    for name, learned_feats in brain.items():
        l_sim, l_str, l_drops = learned_feats

        # --- CALCULATE DELTAS (The Math you asked for) ---
        d_shape = abs(t_sim - l_sim)
        d_str = abs(t_str - l_str)
        d_drops = abs(t_drops - l_drops)

        # --- NORMALIZED SCORING (The "Weights") ---
        # We multiply small decimals (Shape) to make them matter.
        # We divide huge integers (Drops) so they don't dominate.

        score_shape = d_shape * 100  # Weight: High (Shape is important)
        score_str = d_str * 50  # Weight: Medium
        score_drops = d_drops / 50  # Weight: Low (Because 2000 is huge)

        total_score = score_shape + score_str + score_drops

        # Print the exact row
        print(f" {name:<10} | {d_shape:<10.2f} | {d_str:<10.2f} | {d_drops:<10.0f} | {total_score:.1f}")

        # Pick the Winner
        if total_score < lowest_score:
            lowest_score = total_score
            best_match_name = name

    # 3. Final Result
    print("-" * 65)

    # Translate the short name to the full diagnosis
    diagnosis_map = {
        "HEALTHY": "System Healthy",
        "GAIN": "Gain Stage Failure (Potentiometer)",
        "CONN": "Loose Ribbon Cable (Intermittent Fault)",
        "POWER": "Power Rail Failure (Diode Clipping)"
    }

    full_diagnosis = diagnosis_map.get(best_match_name, "Unknown Fault")

    return f">> RESULT: {full_diagnosis}"


# ==========================================
# PART 4: RUN
# ==========================================
if __name__ == "__main__":
    knowledge = train_ai()

    if len(knowledge) == 4:
        if record_live_signal():
            result = diagnose(LIVE_FILE, knowledge)
            print(result)
            print("=" * 65)
    else:
        print("\n[STOP] You are missing training files.")