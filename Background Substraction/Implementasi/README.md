# 🚦 ATCS — Adaptive Traffic Control System
### Prototype Sistem Lampu Lalu Lintas Adaptif Berbasis Computer Vision & IoT

> Sistem lampu lalu lintas adaptif yang mendeteksi kepadatan kendaraan via webcam, memutuskan durasi hijau secara dinamis, dan mengendalikan lampu fisik melalui ESP32 via Firebase Realtime Database.

---

## 📁 Struktur Repository

```
atcs/
├── laptop/
│   ├── main.py              # Otak sistem: deteksi kendaraan + logika fase + push Firebase
│   └── StreetPicker.py      # Tool kalibrasi ROI slot per arah
├── esp32/
│   └── main.cpp             # Firmware ESP32: baca Firebase → eksekusi lampu
├── simulation/
│   └── Simulasi_All_Siklus.html   # Simulasi browser (referensi logika)
├── assets/
│   └── street_image.jpg     # Foto maket dari atas (untuk kalibrasi)
├── requirements.txt
└── README.md
```

---

## 🧠 Arsitektur Sistem

```
┌─────────────────────────────────────────┐
│              LAPTOP (main.py)           │
│                                         │
│  Webcam USB → OpenCV (preprocess)       │
│      ↓                                  │
│  countNonZero per slot ROI              │
│      ↓                                  │
│  Logika Fase (identik simulasi HTML)    │
│  pickNextDir (4-tier priority)          │
│      ↓                                  │
│  Push /atcs/phase & /atcs/counts        │
└──────────────────┬──────────────────────┘
                   │ Firebase RTDB (WiFi)
┌──────────────────▼──────────────────────┐
│            ESP32 DevKit V1              │
│                                         │
│  Poll /atcs/phase tiap 500ms            │
│      ↓                                  │
│  Eksekusi 4 modul lampu lalu lintas     │
│  (N / E / S / W)                        │
└─────────────────────────────────────────┘
```

---

## ⚙️ Logika Fase (Identik Simulasi)

### Tabel Durasi Hijau

| Kendaraan di ROI | Kategori    | Durasi Hijau |
|:----------------:|-------------|:------------:|
| 0                | Kosong      | Skip         |
| 1 – 2            | Sangat Cepat| 5 detik      |
| 3 – 5            | Cepat       | 10 detik     |
| 6 – 9            | Sedang      | 15 detik     |
| ≥ 10             | Padat       | 20 detik     |

### State Machine Fase

```
clearance (2.0s) → green (5/10/15/20s) → yellow (2.5s) → clearance → ...
                ↘ skip (0.6s) jika semua arah kosong ↗
```

### Prioritas Pemilihan Arah (pickNextDir)

1. **Tier 1** — ROI count terbanyak (maks 14 kendaraan)
2. **Tier 2** — Total antrian terbanyak (termasuk luar ROI)
3. **Tier 3** — Siapa pertama masuk ROI (`roiFirstEntry`)
4. **Tier 4** — Wait time terlama (anti-starvation, cap 60 detik)

---

## 🛒 Komponen Hardware

| Komponen | Qty | Keterangan |
|----------|:---:|------------|
| Laptop dengan GPU | 1 | Minimum GTX 1050 / setara |
| Webcam USB | 1 | Resolusi min 640×480 |
| ESP32 DevKit V1 | 1 | |
| Modul lampu lalu lintas (R/Y/G) | 4 | Satu per arah |
| Kabel jumper | secukupnya | |
| Maket jalan (simpang 4) | 1 | Lihat foto di `assets/` |
| Mobil mainan 4×3 cm | 32 | 8 per ruas |
| Power bank / kabel USB | 1 | Untuk ESP32 |

### Wiring ESP32

| Arah | Merah | Kuning | Hijau |
|------|:-----:|:------:|:-----:|
| N (Utara)  | GPIO 13 | GPIO 12 | GPIO 14 |
| E (Timur)  | GPIO 27 | GPIO 26 | GPIO 25 |
| S (Selatan)| GPIO 33 | GPIO 32 | GPIO 15 |
| W (Barat)  | GPIO  2 | GPIO  4 | GPIO  5 |

> Semua GND modul lampu → GND ESP32

---

## 🔥 Setup Firebase

1. Buka [console.firebase.google.com](https://console.firebase.google.com)
2. **Create project** → beri nama (contoh: `atcs-prototype`)
3. Klik **Realtime Database** → Create database → pilih **Start in test mode**
4. Catat URL database: `https://atcs-prototype-default-rtdb.firebaseio.com`
5. **Project Settings** → **Service accounts** → **Generate new private key**
   - Download file JSON → rename jadi `serviceAccountKey.json`
   - Taruh di folder `laptop/`
6. **Project Settings** → **Service accounts** → scroll bawah → salin **Database secret**
   - Paste ke `FIREBASE_AUTH` di `esp32/main.cpp`

Struktur data Firebase yang akan terbentuk otomatis:
```
atcs/
├── counts/
│   ├── N: 3
│   ├── E: 0
│   ├── S: 7
│   └── W: 1
└── phase/
    ├── dir: "S"
    ├── state: "green"
    ├── timer: 12.4
    ├── timer_max: 15
    ├── green_duration: 15
    ├── cycle_count: 42
    └── skip_count: 5
```

---

## 💻 Setup Laptop

### 1. Clone repository

```bash
git clone https://github.com/USERNAME/atcs.git
cd atcs/laptop
```

### 2. Install dependencies

```bash
pip install opencv-python==4.8.1.78 numpy==1.26.4 cvzone==1.5.6 firebase-admin==6.3.0
```

### 3. Taruh `serviceAccountKey.json` di folder `laptop/`

### 4. Edit `main.py` — isi URL Firebase

```python
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://NAMA-PROJECT-default-rtdb.firebaseio.com'
})
```

### 5. Kalibrasi ROI dengan StreetPicker

```bash
# Foto maket dari atas → simpan sebagai street_image.jpg di folder laptop/
python StreetPicker.py
```

**Kontrol StreetPicker:**
- Tekan `N` / `E` / `S` / `W` → pilih arah aktif
- **Klik kiri** → tambah slot (satu slot = ruang satu mobil)
- **Klik kanan** → hapus slot
- `ESC` → simpan & keluar

Tandai slot mulai dari **dekat stop line** ke arah luar. Jumlah slot maksimal yang berguna = 14 per arah (sesuai ROI_MAX simulasi).

### 6. Jalankan sistem

```bash
python main.py
```

---

## 🔌 Setup ESP32

### 1. Install Arduino IDE

Download dari [arduino.cc/en/software](https://www.arduino.cc/en/software)

### 2. Install board ESP32

- Arduino IDE → **File** → **Preferences**
- Tambahkan URL berikut ke *Additional boards manager URLs*:
  ```
  https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
  ```
- **Tools** → **Board** → **Boards Manager** → cari `esp32` → Install

### 3. Install library Firebase

- **Sketch** → **Include Library** → **Manage Libraries**
- Cari `Firebase ESP Client` by Mobizt → Install

### 4. Edit `esp32/main.cpp`

```cpp
#define FIREBASE_HOST   "atcs-prototype-default-rtdb.firebaseio.com"
#define FIREBASE_AUTH   "DATABASE_SECRET_KEY_DARI_FIREBASE"
#define WIFI_SSID       "NAMA_WIFI_KAMU"
#define WIFI_PASSWORD   "PASSWORD_WIFI_KAMU"
```

### 5. Upload ke ESP32

- **Tools** → **Board** → pilih `ESP32 Dev Module`
- **Tools** → **Port** → pilih port COM ESP32 (cek Device Manager)
- Klik **Upload** (→)
- Buka **Serial Monitor** (115200 baud) — pastikan muncul:
  ```
  [WiFi] Terhubung: 192.168.x.x
  [Firebase] Siap.
  ```

---

## ▶️ Menjalankan Sistem Lengkap

```
1. ESP32 dinyalakan & terhubung WiFi+Firebase (Serial Monitor konfirmasi)
2. Maket diletakkan, webcam dipasang tepat di atas (top-down, ketinggian 40–60 cm)
3. Pencahayaan ruangan stabil (hindari cahaya berubah-ubah)
4. cd laptop/
5. python main.py
6. Jendela "ATCS — Laptop" terbuka → sistem berjalan
7. Letakkan mobil mainan di ruas → lampu ESP32 merespons
```

### Indikator warna di jendela laptop

| Warna kotak slot | Arti |
|:----------------:|------|
| 🟢 Hijau tebal   | Slot kosong |
| 🔴 Merah tipis   | Slot terisi (ada mobil) |

---

## 🔧 Kalibrasi & Troubleshooting

### Mobil tidak terdeteksi
- Turunkan `PIXEL_THRESHOLD` dari `600` → `300`
- Pastikan pencahayaan cukup terang dan merata
- Cek ukuran `SLOT_W` / `SLOT_H` di StreetPicker — sesuaikan dengan ukuran mobil di frame

### Terlalu banyak false positive (deteksi salah)
- Naikkan `PIXEL_THRESHOLD` → `800` atau `1000`
- Periksa apakah ada bayangan atau pantulan cahaya di maket

### ESP32 tidak update lampu
- Cek WiFi SSID/password
- Cek `FIREBASE_HOST` (tanpa `https://`, tanpa `/` di akhir)
- Cek `FIREBASE_AUTH` — gunakan Database Secret, bukan API Key

### Serial Monitor ESP32 error `PERMISSION_DENIED`
- Firebase Rules masih di lock mode → ubah rules jadi:
  ```json
  {
    "rules": {
      ".read": true,
      ".write": true
    }
  }
  ```
  *(untuk prototype/testing saja)*

---

## 📦 requirements.txt

```
opencv-python==4.8.1.78
numpy==1.26.4
cvzone==1.5.6
firebase-admin==6.3.0
```

---

## 📄 Referensi

- Ompusunggu, R. C., et al. (2025). *Prototype of GPS-Based Adaptive Traffic Light System for Emergency Vehicle Priority*. Sebatik Vol. 29 No. 1.
- Lim, W. L., et al. (2020). *Vision-based Smart Traffic System*. Evolution in Electrical and Electronic Engineering Vol. 1 No. 1.
- Undang-Undang No. 22 Tahun 2009 tentang Lalu Lintas dan Angkutan Jalan.

---

## 👤 Author

**Regita Cahyani Ompusunggu**  
Sistem Informasi — STMIK Widya Cipta Dharma  
NIM: 2041056
