import serial
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
PORT = 'COM3'  # Check your Port
DURATION = 10  # How many seconds to test


# ---------------------

def run_test():
    print(f"--- STARTING TEST ({DURATION}s) ---")

    # 1. LOAD DATA
    try:
        df = pd.read_csv('ecg_data.csv')
        data = (df['dac'].tolist() * 50)[:(DURATION * 150)]
    except:
        print("[ERROR] ecg_data.csv is missing!")
        return

    # 2. CONNECT
    try:
        ser = serial.Serial(PORT, 115200, timeout=1)
        time.sleep(2)
        print(f"[OK] Connected to {PORT}. Running...")
    except:
        print(f"[ERROR] Check {PORT}.")
        return

    sent_data = []
    recv_data = []

    # 3. RUN LOOP
    start_time = time.time()
    for val in data:
        if time.time() - start_time > DURATION: break

        ser.write(f"{val}\n".encode())
        try:
            line = ser.readline().decode().strip()
            if ',' in line:
                s, r = line.split(',')
                sent_data.append(int(s))
                recv_data.append(int(r))
        except:
            pass
        time.sleep(0.005)

    ser.close()

    # 4. CALCULATE MATH
    if len(recv_data) < 10: return print("[FAIL] No data.")

    arr_sent = np.array(sent_data)
    arr_recv = np.array(recv_data)

    # A. Shape (Correlation)
    shape = np.corrcoef(arr_sent, arr_recv)[0, 1]

    # B. Accuracy (Percentage)
    acc = shape * 100

    # C. Strength (Ratio)
    if np.std(arr_sent) == 0:
        strength = 0
    else:
        strength = np.std(arr_recv) / np.std(arr_sent)

    # D. Drops (Zeros)
    drops = np.sum(arr_recv < 5)

    print(f"\nRESULTS: Acc={acc:.1f}% | Shape={shape:.2f} | Str={strength:.2f} | Drops={drops}")

    # 5. DRAW GRAPH
    plt.figure(figsize=(10, 6))
    plt.plot(sent_data, label='Original (PC)', color='blue', alpha=0.5)
    plt.plot(recv_data, label='Output (Circuit)', color='red', alpha=0.8)

    # Add Stats Box
    stats = f"Accuracy: {acc:.1f}%\nShape: {shape:.2f}\nStrength: {strength:.2f}\nDrops: {drops}"
    plt.text(0.02, 0.95, stats, transform=plt.gca().transAxes,
             fontsize=12, bbox=dict(facecolor='white', alpha=0.9))

    plt.title("ECG Signal Analysis")
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    run_test()