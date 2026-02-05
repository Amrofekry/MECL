import serial
import time
import pandas as pd
import sys

# --- CONFIGURATION ---
PORT = 'COM3'  # CHECK THIS!
DURATION_SEC = 60  # EXACTLY 60 Seconds
FILENAME = "gain.csv"  # CHANGE THIS for each run: healthy, gain, conn, power


# ---------------------

def record():
    print(f"--- SETUP: RECORDING TO '{FILENAME}' ---")

    # 1. LOAD DATA (Big Buffer for 60s)
    try:
        df = pd.read_csv('ecg_data.csv')
        # Load 15,000 samples to be safe for 60 seconds
        data = (df['dac'].tolist() * 100)[:15000]
        print(f"[OK] Loaded signal data.")
    except:
        print("[ERROR] ecg_data.csv is missing!")
        return

    # 2. CONNECT TO ARDUINO
    try:
        ser = serial.Serial(PORT, 115200, timeout=1)
        time.sleep(2)  # Wait for Arduino to wake up
        print(f"[OK] Connected to {PORT}.")
    except:
        print(f"[ERROR] Cannot connect to {PORT}. Is it open in another app?")
        return

    # 3. USER TRIGGER (CRITICAL FOR ACCURACY)
    print("\n" + "=" * 40)
    print(f"PREPARE YOUR CIRCUIT FOR: {FILENAME}")
    print(" -> If 'conn.csv', get ready to tap the button.")
    print(" -> If 'gain.csv', set the knob and let go.")
    print("=" * 40)
    input(">>> PRESS ENTER TO START RECORDING <<<")

    log = []
    start_time = time.time()
    print(" >> RECORDING STARTED... (Do your task!)")

    # 4. STREAM LOOP
    for i, val in enumerate(data):
        # STOP LOOP AT 60 SECONDS
        elapsed = time.time() - start_time
        if elapsed > DURATION_SEC:
            break

        # Progress Countdown
        if i % 1000 == 0:
            sys.stdout.write(f"\r   Time Remaining: {int(DURATION_SEC - elapsed)}s   ")
            sys.stdout.flush()

        # Send/Receive
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


    # 5. SAVE
    print(f"\n\n[DONE] Capture finished.")
    if len(log) > 100:
        pd.DataFrame(log, columns=['Sent', 'Recv']).to_csv(FILENAME, index=False)
        print(f"[SUCCESS] Saved {len(log)} samples to {FILENAME}.")
    else:
        print("[FAIL] Not enough data recorded. Check wires.")


if __name__ == "__main__":
    record()