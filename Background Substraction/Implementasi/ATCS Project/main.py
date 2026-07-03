import cv2
import numpy as np
import serial
import serial.tools.list_ports
import time
import json
import threading
from flask import Flask, render_template, jsonify
from datetime import datetime

SERIAL_PORT   = 'COM3'      
BAUD_RATE     = 115200
CAMERA_INDEX  = 0            
SEND_INTERVAL = 0.25         
MIN_AREA      = 150          
THRESH_VAL    = 30           
FLASK_PORT    = 5000         

try:
    with open("roi_config.json") as f:
        raw = json.load(f)
    rois = {k: tuple(map(int, v)) for k, v in raw.items()}
    print(f"ROI loaded: {rois}")
except FileNotFoundError:
    print("ERROR: roi_config.json tidak ditemukan!")
    print("Jalankan calibrate.py terlebih dahulu.")
    exit(1)

try:
    bg = cv2.imread("bg.jpg")
    bg_gray = cv2.GaussianBlur(cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    print("Background loaded: bg.jpg")
except Exception as e:
    print(f"ERROR: bg.jpg tidak bisa dibaca — {e}")
    exit(1)

state = {
    "counts":    {"N": 0, "E": 0, "S": 0, "W": 0},
    "phase":     {"dir": "N", "state": "SKIP", "rem_ms": 0, "cnt": 0},
    "connected": False,
    "log":       [],
    "cycle":     0,
}
state_lock = threading.Lock()

def add_log(msg, level="info"):
    ts = datetime.now().strftime("%H:%M:%S")
    with state_lock:
        state["log"].append({"ts": ts, "msg": msg, "level": level})
        if len(state["log"]) > 100:
            state["log"].pop(0)
    print(f"[{ts}] {msg}")

def count_vehicles(gray_frame, roi):
    x, y, w, h = roi
    roi_frame = gray_frame[y:y+h, x:x+w]
    roi_bg    = bg_gray[y:y+h, x:x+w]

    if roi_frame.shape != roi_bg.shape:
        return 0  

    diff = cv2.absdiff(roi_frame, roi_bg)
    _, thresh = cv2.threshold(diff, THRESH_VAL, 255, cv2.THRESH_BINARY)

    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.dilate(thresh, kernel, iterations=1)

    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    count = 0
    for c in contours:
        area = cv2.contourArea(c)
        if area > MIN_AREA:
            count += 1
    return min(count, 14)

def serial_thread(ser):
    add_log(f"Serial terhubung: {SERIAL_PORT}", "ok")
    with state_lock:
        state["connected"] = True

    while True:
        try:
            # Baca status dari ESP32
            if ser.in_waiting:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if line.startswith("STATE"):
                    parts = line.split()
                    if len(parts) >= 4:
                        with state_lock:
                            state["phase"]["dir"]    = parts[1] if len(parts) > 1 else "N"
                            state["phase"]["state"]  = parts[2] if len(parts) > 2 else "SKIP"
                            for p in parts:
                                if p.startswith("rem="):
                                    state["phase"]["rem_ms"] = int(p[4:])
                                elif p.startswith("cnt="):
                                    state["phase"]["cnt"] = int(p[4:])

                elif line.startswith("PHASE"):
                    add_log(f"ESP32: {line}", "ok")
                    with state_lock:
                        state["cycle"] += 1

                elif line == "ATCS READY":
                    add_log("ESP32 siap!", "ok")

        except Exception as e:
            add_log(f"Serial error: {e}", "err")
            with state_lock:
                state["connected"] = False
            break

        time.sleep(0.01)

def vision_loop():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        add_log(f"ERROR: Kamera {CAMERA_INDEX} tidak terdeteksi!", "err")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    add_log("Kamera aktif", "ok")

    ser = None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Tunggu ESP32 reset setelah koneksi serial
        t = threading.Thread(target=serial_thread, args=(ser,), daemon=True)
        t.start()
    except serial.SerialException as e:
        add_log(f"Serial GAGAL ({e}). Jalankan tanpa ESP32.", "warn")

    last_send = 0
    dir_colors = {
        "N": (0, 255, 0),
        "E": (255, 165, 0),
        "S": (0, 165, 255),
        "W": (255, 0, 255),
    }

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.GaussianBlur(
            cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (5, 5), 0
        )

        new_counts = {}
        for d, roi in rois.items():
            new_counts[d] = count_vehicles(gray, roi)

        with state_lock:
            state["counts"] = dict(new_counts)

        for d, roi in rois.items():
            x, y, w, h = roi
            color = dir_colors.get(d, (255, 255, 255))
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            label = f"{d}: {new_counts[d]}"
            cv2.putText(frame, label, (x+4, y+22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        with state_lock:
            ph = state["phase"].copy()
        phase_text = f"Phase: {ph['dir']} {ph['state']} ({ph['rem_ms']}ms)"
        cv2.putText(frame, phase_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        now = time.time()
        if ser and ser.is_open and now - last_send >= SEND_INTERVAL:
            msg = f"N{new_counts['N']} E{new_counts['E']} S{new_counts['S']} W{new_counts['W']}\n"
            try:
                ser.write(msg.encode())
            except Exception as e:
                add_log(f"Gagal kirim serial: {e}", "err")
            last_send = now

        cv2.imshow("ATCS — OpenCV Vision (tekan Q untuk keluar)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    if ser and ser.is_open:
        ser.close()
    cv2.destroyAllWindows()
    add_log("Vision loop berhenti.", "warn")

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/api/state")
def api_state():
    with state_lock:
        return jsonify(state)

def flask_thread():
    add_log(f"Dashboard: http://localhost:{FLASK_PORT}", "info")
    app.run(host="0.0.0.0", port=FLASK_PORT,
            debug=False, use_reloader=False)

if __name__ == "__main__":
    add_log("ATCS System starting...", "info")
    add_log(f"MIN_AREA={MIN_AREA} | THRESH={THRESH_VAL} | port={SERIAL_PORT}", "info")

    ft = threading.Thread(target=flask_thread, daemon=True)
    ft.start()

    vision_loop()