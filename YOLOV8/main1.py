import cv2
import serial
import time
import threading
import firebase_admin
from firebase_admin import credentials, db
from ultralytics import YOLO

MODEL_PATH  = r"C:\Users\asud\Downloads\capstone-cuda\runs\detect\runs\car_color_detector_v4"
SERIAL_PORT = "COM4"          
BAUD_RATE   = 115200
FIREBASE_URL = "https://atcs-project-default-rtdb.firebaseio.com/"
SERVICE_ACCOUNT = "serviceAccountKey.json"

CAMERA_MAP = {
    "N": 0,   
    "E": 2,   
    "S": 3,   
    "W": 4,  
}

cred = credentials.Certificate(SERVICE_ACCOUNT)
firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_URL})
fb_ref = db.reference("/atcs")

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Tunggu ESP32 reset
    print("Serial connected:", SERIAL_PORT)
except Exception as e:
    print(f"Serial error: {e}")
    ser = None

cams = {}
for direction, idx in CAMERA_MAP.items():
    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cams[direction] = cap

car_counts = {"N": 0, "E": 0, "S": 0, "W": 0}
light_states = {"N": "RED", "E": "RED", "S": "RED", "W": "RED"}
lock = threading.Lock()

def count_vehicles(frame, direction):
    """Jalankan YOLO dan hitung kendaraan per frame."""
    results = model(frame, conf=0.5, verbose=False)
    count = len(results[0].boxes)
    with lock:
        car_counts[direction] = count
    return results[0].plot(), count

def decide_traffic_light():
    """
    Logika sederhana: arah dengan kendaraan terbanyak dapat HIJAU,
    sisanya MERAH. Tambahkan KUNING sebagai transisi 3 detik.
    """
    with lock:
        counts = car_counts.copy()

    max_dir = max(counts, key=counts.get)

    states = {}
    for d in ["N", "E", "S", "W"]:
        states[d] = "GREEN" if d == max_dir else "RED"

    return states

def send_to_esp32(states):
    """Kirim string 'N:GREEN,E:RED,S:RED,W:RED' ke ESP32 via Serial."""
    msg = ",".join([f"{d}:{states[d]}" for d in ["N", "E", "S", "W"]])
    if ser and ser.is_open:
        ser.write((msg + "\n").encode())
        print(f"[SERIAL] Sent: {msg}")
    return msg

def upload_to_firebase(states, counts):
    """Upload status lampu dan jumlah kendaraan ke Firebase."""
    dir_names = {"N": "north", "E": "east", "S": "south", "W": "west"}
    data = {}
    for d, name in dir_names.items():
        data[name] = {
            "color":     states[d],
            "car_count": counts[d],
        }
    data["timestamp"] = int(time.time())
    data["raw_state"] = ",".join([f"{d}:{states[d]}" for d in ["N","E","S","W"]])

    try:
        fb_ref.update(data)
        print("[FIREBASE] Updated")
    except Exception as e:
        print(f"[FIREBASE] Error: {e}")

last_decision_time = 0
DECISION_INTERVAL  = 5   # Detik antar pergantian lampu

print("System running. Press Q to quit.")

while True:
    processed = {}

    for direction, cam in cams.items():
        ret, frame = cam.read()
        if not ret:
            frame = 255 * cv2.UMat(480, 640, cv2.CV_8UC3).get()
            cv2.putText(frame, f"Cam {direction} Offline",
                        (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
            processed[direction] = frame
        else:
            annotated, count = count_vehicles(frame, direction)
            cv2.putText(annotated, f"{direction} | Cars: {count}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
            # Tampilkan warna lampu saat ini
            color = light_states.get(direction, "RED")
            color_bgr = {"RED":(0,0,255),"YELLOW":(0,255,255),"GREEN":(0,255,0)}
            cv2.circle(annotated, (610, 30), 15, color_bgr.get(color,(255,255,255)), -1)
            processed[direction] = annotated

    order = ["N", "E", "S", "W"]
    resized = [cv2.resize(processed[d], (640, 480)) for d in order]
    top    = cv2.hconcat([resized[0], resized[1]])
    bottom = cv2.hconcat([resized[2], resized[3]])
    grid   = cv2.vconcat([top, bottom])
    cv2.imshow("ATCS - 4 Camera Detection", grid)

    now = time.time()
    if now - last_decision_time >= DECISION_INTERVAL:
        last_decision_time = now
        new_states = decide_traffic_light()

        with lock:
            light_states.update(new_states)
            current_counts = car_counts.copy()

        send_to_esp32(new_states)

        # Firebase di thread terpisah agar tidak block
        t = threading.Thread(
            target=upload_to_firebase,
            args=(new_states, current_counts),
            daemon=True
        )
        t.start()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

for cam in cams.values():
    cam.release()
cv2.destroyAllWindows()
if ser:
    ser.close()
print("System stopped.")