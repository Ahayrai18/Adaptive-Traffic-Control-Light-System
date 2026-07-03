import cv2, json

def calibrate():
    cap = cv2.VideoCapture(0)  
    if not cap.isOpened():
        print("ERROR: Webcam tidak terdeteksi. Coba ganti angka 0 ke 1.")
        return

    print("=" * 50)
    print("LANGKAH 1: Pastikan maket KOSONG (tanpa mobil)")
    print("Tekan SPASI untuk ambil foto background")
    print("=" * 50)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        cv2.imshow("Kalibrasi — Tekan SPASI saat maket kosong", frame)
        if cv2.waitKey(1) & 0xFF == 32:  
            cv2.imwrite("bg.jpg", frame)
            print("Background tersimpan: bg.jpg")
            break

    cv2.destroyAllWindows()

    print("\n" + "=" * 50)
    print("LANGKAH 2: Tarik kotak ROI untuk setiap arah")
    print("Klik-drag → Enter untuk konfirmasi → ulangi 4x")
    print("=" * 50)

    rois = {}
    directions = {
        'N': "ROI UTARA  — Ruas kendaraan dari atas",
        'E': "ROI TIMUR  — Ruas kendaraan dari kanan",
        'S': "ROI SELATAN — Ruas kendaraan dari bawah",
        'W': "ROI BARAT  — Ruas kendaraan dari kiri",
    }

    for code, label in directions.items():
        print(f"\n→ {label}")
        print("  Tarik kotak pada ruas tersebut, lalu tekan ENTER")
        roi = cv2.selectROI(label, frame, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow(label)
        if roi[2] == 0 or roi[3] == 0:
            print(f"  PERINGATAN: ROI {code} kosong, ulangi kalibrasi!")
            cap.release()
            return
        rois[code] = list(roi)  # [x, y, w, h]
        print(f"  Tersimpan: x={roi[0]} y={roi[1]} w={roi[2]} h={roi[3]}")

    with open("roi_config.json", "w") as f:
        json.dump(rois, f, indent=2)
    print("\nKalibrasi selesai! roi_config.json tersimpan.")
    print("Siap menjalankan traffic_main.py")
    cap.release()

if __name__ == "__main__":
    calibrate()