import cv2
import numpy as np
import time
import threading
import serial
from datetime import datetime
from ultralytics import YOLO
from flask import Flask, render_template, jsonify

try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_LIB_OK = True
except ImportError:
    FIREBASE_LIB_OK = False

YOLO_MODEL_PATH = r"C:\Users\asud\Downloads\capstone-cuda\runs\detect\runs\car_color_detector_v4"
YOLO_CONF       = 0.40    
YOLO_DEVICE     = 0     
YOLO_IMG_SIZE   = 416     
MIN_BOX_AREA    = 200     

EXCLUDE_CAMERA_INDEX = -1
FRAME_WIDTH  = 640
FRAME_HEIGHT = 480  

DIRECTION_ORDER = ["N", "E", "S", "W"]  

SERIAL_PORT = "COM8"    
BAUD_RATE   = 115200

FIREBASE_ENABLED = True
FIREBASE_CRED    = "serviceAccountKey.json"
FIREBASE_DB_URL  = "https://ATCS.firebaseio.com"

FLASK_PORT = 5000

YELLOW_DURATION_S    = 2.5
CLEARANCE_DURATION_S = 2.0
SKIP_DURATION_S      = 0.6
STARVATION_CAP_S     = 60.0

SERIAL_SEND_INTERVAL_S   = 0.25
FIREBASE_PUSH_INTERVAL_S = 0.5

from pygrabber.dshow_graph import FilterGraph

EXCLUDE_NAME_KEYWORDS = ["USB CAMERA", "NYK NEMESIS", "USB Camera", "USB Camera"]  # sesuaikan dgn hasil langkah 2

def find_cameras(max_cam=10):
    device_names = FilterGraph().get_input_devices()  # urutannya = urutan index CAP_DSHOW
    indices = []
    for i, name in enumerate(device_names):
        if i >= max_cam:
            continue
        if any(kw in name.lower() for kw in EXCLUDE_NAME_KEYWORDS):
            print(f"[SKIP] index {i} -> '{name}' (kamera internal)")
            continue
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                indices.append(i)
                print(f"[OK]   index {i} -> '{name}'")
        cap.release()
    return indices

print("[...] Mencari kamera...")
_all_indices = find_cameras()
_usb_indices = [idx for idx in _all_indices if idx != EXCLUDE_CAMERA_INDEX][:4]
print(f"[OK] Kamera yang dipakai: {_usb_indices}")

if len(_usb_indices) < 4:
    print(f"[FATAL] Hanya {len(_usb_indices)} kamera USB ditemukan, butuh 4!")
    print("        Jalankan 01_find_cameras.py untuk diagnosa lebih detail.")
    exit(1)

CAMERA_INDICES = {
    "N":3,
    "E":2,
    "S":1,
    "W":0
}
print(f"[INFO] Mapping arah -> index kamera: {CAMERA_INDICES}")

print(f"[...] Loading YOLO model...")
model = YOLO(YOLO_MODEL_PATH)
print(f"[INFO] Kelas model: {model.names}")
print(f"[INFO] Semua {len(model.names)} kelas dihitung sebagai kendaraan (tanpa filter)")

dummy = np.zeros((YOLO_IMG_SIZE, YOLO_IMG_SIZE, 3), dtype=np.uint8)
model(dummy, device=YOLO_DEVICE, verbose=False)
print(f"[OK] YOLO siap")

yolo_lock = threading.Lock()

firebase_ok = False
ref_counts = ref_phase = ref_meta = ref_log = None

if FIREBASE_ENABLED and FIREBASE_LIB_OK:
    try:
        cred = credentials.Certificate(FIREBASE_CRED)
        firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})
        ref_counts = db.reference("/atcs/counts")
        ref_phase  = db.reference("/atcs/phase")
        ref_meta   = db.reference("/atcs/meta")
        ref_log    = db.reference("/atcs/log")
        firebase_ok = True
        print(f"[OK] Firebase terhubung: {FIREBASE_DB_URL}")
    except Exception as e:
        print(f"[WARN] Firebase gagal ({e}) — lanjut tanpa cloud dashboard")
else:
    print("[INFO] Firebase dilewati (disabled atau library tidak terinstall)")

START_TIME = time.time()
lock = threading.Lock()

counts_state = {"N": 0, "E": 0, "S": 0, "W": 0}

phase_state = {
    "dir": "N", "state": "SKIP",
    "rem_s": 0.6, "dur_s": 0.6, "cnt": 0,
}

wait_time     = {"N": 0.0, "E": 0.0, "S": 0.0, "W": 0.0}
first_nonzero = {"N": 0.0, "E": 0.0, "S": 0.0, "W": 0.0}

meta_state = {
    "esp32_connected": False,
    "cycle": 0,
    "skip_count": 0,
}

LOG_BUFFER = []
def log(msg, level="info"):
    ts = datetime.now().strftime("%H:%M:%S")
    entry = {"ts": ts, "msg": msg, "level": level}
    with lock:
        LOG_BUFFER.append(entry)
        if len(LOG_BUFFER) > 80:
            LOG_BUFFER.pop(0)
    print(f"[{ts}] {msg}")

def get_green_duration(count):
    if count == 0:  return 0.0
    if count <= 2:  return 5.0
    if count <= 5:  return 10.0
    if count <= 9:  return 15.0
    return 20.0

def pick_next_direction():

    with lock:
        counts_snapshot = dict(counts_state)
        wait_snapshot    = dict(wait_time)
        fnz_snapshot     = dict(first_nonzero)

    max_val = max(counts_snapshot.values())
    candidates = [d for d in "NESW" if counts_snapshot[d] == max_val]

    if len(candidates) == 1:
        return candidates[0]

    valid_fnz = {d: fnz_snapshot[d] for d in candidates if fnz_snapshot[d] > 0}
    if valid_fnz:
        return min(valid_fnz, key=valid_fnz.get)

    return max(candidates, key=lambda d: wait_snapshot[d])

def init_phase():
    next_dir = pick_next_direction()

    with lock:
        count = counts_state[next_dir]
        wait_time[next_dir] = 0.0
        first_nonzero[next_dir] = 0.0

    duration = get_green_duration(count)

    if duration == 0:
        new_state, new_dur = "SKIP", SKIP_DURATION_S
    else:
        new_state, new_dur = "GREEN", duration

    with lock:
        phase_state["dir"]   = next_dir
        phase_state["state"] = new_state
        phase_state["rem_s"] = new_dur
        phase_state["dur_s"] = new_dur
        phase_state["cnt"]   = count
        meta_state["cycle"] += 1
        if new_state == "SKIP":
            meta_state["skip_count"] += 1

    log(f"PHASE {next_dir} {new_state} dur={new_dur:.1f}s cnt={count}", "ok")
    send_light_command()

def tick_phase(dt):
    with lock:
        active_dir = phase_state["dir"]
        current_state = phase_state["state"]

        for d in "NESW":
            is_active = (d == active_dir and current_state == "GREEN")
            if not is_active:
                wait_time[d] += dt
                if wait_time[d] > STARVATION_CAP_S:
                    wait_time[d] = STARVATION_CAP_S
            if counts_state[d] > 0:
                if first_nonzero[d] == 0:
                    first_nonzero[d] = time.time()
            else:
                first_nonzero[d] = 0.0

        phase_state["rem_s"] = max(0.0, phase_state["rem_s"] - dt)
        rem = phase_state["rem_s"]
        st  = phase_state["state"]

    if rem > 0:
        return

    if st == "SKIP":
        init_phase()
    elif st == "GREEN":
        with lock:
            phase_state["state"] = "YELLOW"
            phase_state["rem_s"] = YELLOW_DURATION_S
            phase_state["dur_s"] = YELLOW_DURATION_S
        log(f"PHASE {active_dir} YELLOW", "ok")
        send_light_command()
    elif st == "YELLOW":
        with lock:
            phase_state["state"] = "CLEARANCE"
            phase_state["rem_s"] = CLEARANCE_DURATION_S
            phase_state["dur_s"] = CLEARANCE_DURATION_S
        log("PHASE ALL CLEARANCE", "ok")
        send_light_command()
    elif st == "CLEARANCE":
        init_phase()

def phase_machine_loop():
    last_tick = time.time()
    time.sleep(2.0)
    init_phase()

    while running:
        now = time.time()
        dt = now - last_tick
        last_tick = now
        tick_phase(dt)
        time.sleep(0.1)

def detect_full_frame(frame):
    with yolo_lock:
        results = model(frame, imgsz=YOLO_IMG_SIZE, conf=YOLO_CONF,
                         device=YOLO_DEVICE, verbose=False)

    count = 0
    annotated = frame
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
        valid_count = 0
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            area = (x2 - x1) * (y2 - y1)
            if area >= MIN_BOX_AREA:
                valid_count += 1
        count = valid_count
        annotated = result.plot()

    return min(count, 14), annotated

frame_display = {"N": None, "E": None, "S": None, "W": None}
running = True

def camera_loop(direction_key, camera_index):
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        log(f"FATAL: Kamera {direction_key} index {camera_index} tidak terbuka!", "err")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    log(f"Kamera {direction_key} aktif (index {camera_index})", "ok")

    while running:
        ret, frame = cap.read()
        if not ret:
            frame = 255 * np.ones((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
            cv2.putText(frame, f"Camera {direction_key} Offline",
                        (40, FRAME_HEIGHT // 2), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 0, 255), 2)
            with lock:
                counts_state[direction_key] = 0
            frame_display[direction_key] = frame
            time.sleep(0.1)
            continue

        count, annotated = detect_full_frame(frame)

        with lock:
            counts_state[direction_key] = count

        cv2.putText(annotated, f"{direction_key}: {count} kendaraan",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        frame_display[direction_key] = annotated

    cap.release()

ser_handle = None

def derive_light_colors():
    with lock:
        active_dir = phase_state["dir"]
        st = phase_state["state"]

    colors = {"N": "RED", "E": "RED", "S": "RED", "W": "RED"}
    if st == "GREEN":
        colors[active_dir] = "GREEN"
    elif st == "YELLOW":
        colors[active_dir] = "YELLOW"
    return colors

def send_light_command():
    global ser_handle
    if not ser_handle or not ser_handle.is_open:
        return
    colors = derive_light_colors()
    msg = f"N:{colors['N']},E:{colors['E']},S:{colors['S']},W:{colors['W']}\n"
    try:
        ser_handle.write(msg.encode())
    except Exception as e:
        log(f"Serial write error: {e}", "err")

def serial_reader_loop(ser):
    log(f"Serial reader aktif: {SERIAL_PORT}", "ok")
    with lock:
        meta_state["esp32_connected"] = True

    buf = ""
    while running:
        try:
            if not ser.is_open:
                break
            data = ser.read(ser.in_waiting or 1)
            if not data:
                time.sleep(0.01)
                continue
            buf += data.decode("utf-8", errors="ignore")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                if line == "ATCS_READY":
                    log("ESP32 siap (ATCS_READY)", "ok")
                elif line.startswith("OK:"):
                    pass
        except serial.SerialException as e:
            log(f"Serial putus: {e}", "err")
            with lock:
                meta_state["esp32_connected"] = False
            break
        except Exception as e:
            log(f"Serial read error: {e}", "err")
        time.sleep(0.01)

def serial_periodic_sender_loop():
    while running:
        send_light_command()
        time.sleep(SERIAL_SEND_INTERVAL_S)

def firebase_push_loop():
    if not firebase_ok:
        return
    while running:
        try:
            with lock:
                counts_snap = dict(counts_state)
                phase_snap  = dict(phase_state)
                meta_snap   = dict(meta_state)
                log_snap    = list(LOG_BUFFER[-30:])

            now = time.time()
            ts  = int(now * 1000)
            uptime = int(now - START_TIME)

            ref_counts.set({**counts_snap, "ts": ts})
            ref_phase.set({**phase_snap, "ts": ts})
            ref_meta.set({**meta_snap, "uptime_s": uptime, "ts": ts})
            if log_snap:
                ref_log.set(log_snap)
        except Exception as e:
            log(f"Firebase push error: {e}", "warn")

        time.sleep(FIREBASE_PUSH_INTERVAL_S)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("dashboard_local.html")

@app.route("/api/state")
def api_state():
    with lock:
        return jsonify({
            "counts": dict(counts_state),
            "phase":  dict(phase_state),
            "meta":   {**meta_state, "uptime_s": int(time.time() - START_TIME)},
            "log":    list(LOG_BUFFER[-30:]),
        })

def flask_loop():
    log(f"Dashboard lokal: http://localhost:{FLASK_PORT}", "info")
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False, use_reloader=False)

def main():
    global running, ser_handle

    log("=" * 50, "info")
    log("ATCS FINAL — Python otak, ESP32 eksekutor", "info")
    log("=" * 50, "info")

    try:
        ser_handle = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2.0)
        threading.Thread(target=serial_reader_loop, args=(ser_handle,), daemon=True).start()
        threading.Thread(target=serial_periodic_sender_loop, daemon=True).start()
    except serial.SerialException as e:
        log(f"Serial gagal ({e}) — sistem jalan tanpa ESP32 (logika tetap jalan)", "warn")

    for d, idx in CAMERA_INDICES.items():
        threading.Thread(target=camera_loop, args=(d, idx), daemon=True).start()
        time.sleep(0.3)

    threading.Thread(target=phase_machine_loop, daemon=True).start()

    if firebase_ok:
        threading.Thread(target=firebase_push_loop, daemon=True).start()

    threading.Thread(target=flask_loop, daemon=True).start()

    log("Semua sistem berjalan. Tekan Q di jendela kamera untuk keluar.", "ok")

    window_positions = {"N": (0, 0), "E": (660, 0), "S": (0, 520), "W": (660, 520)}
    windows_moved = set()

    while True:
        for d in "NESW":
            f = frame_display[d]
            if f is not None:
                win = f"ATCS Cam {d}"
                cv2.imshow(win, cv2.resize(f, (640, 480)))
                if win not in windows_moved:
                    cv2.moveWindow(win, *window_positions[d])
                    windows_moved.add(win)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False
            break

    log("Shutdown...", "warn")
    time.sleep(0.5)
    if ser_handle and ser_handle.is_open:
        ser_handle.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
