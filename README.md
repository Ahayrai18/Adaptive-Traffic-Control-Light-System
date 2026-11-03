# 🚦 Adaptive Traffic Control System (ATCS)

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-Deep_Learning-EE4C2C?logo=pytorch)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Object_Detection-purple)
![Ultralytics](https://img.shields.io/badge/Ultralytics-YOLO-black)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-blue?logo=opencv)
![NumPy](https://img.shields.io/badge/NumPy-Scientific_Computing-013243?logo=numpy)
![Flask](https://img.shields.io/badge/Flask-Web_Dashboard-black?logo=flask)
![PySerial](https://img.shields.io/badge/PySerial-Communication-blue)
![ESP32](https://img.shields.io/badge/ESP32-IoT-red)
![Arduino](https://img.shields.io/badge/Arduino-C%2B%2B-00979D?logo=arduino)
![CUDA](https://img.shields.io/badge/NVIDIA-CUDA-76B900?logo=nvidia)
![Firebase](https://img.shields.io/badge/Firebase-Realtime_Database-FFCA28?logo=firebase)
![Roboflow](https://img.shields.io/badge/Roboflow-Dataset-purple)
![SolidWorks](https://img.shields.io/badge/SolidWorks-3D_Design-red)

### Car Color Detection with YOLOv8 + ESP32 Traffic Light Controller

A capstone project that combines real-time vehicle color detection using YOLOv8 on CUDA-accelerated hardware with an ESP32-based physical traffic light controller. Four webcams monitor each intersection direction (North, East, South, West), the model detects and counts vehicles per lane, and the result is sent over serial to an ESP32 that drives 12 real LEDs.

---

## 📋 Table of Contents

- [Demo](#-demo)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Hardware Requirements](#-hardware-requirements)
- [Project Structure](#-project-structure)
- [Setup — Step by Step](#-setup--step-by-step)
  - [1. Python 3.11.9](#1-python-3119)
  - [2. Virtual Environment](#2-virtual-environment)
  - [3. NVIDIA Driver & CUDA Check](#3-nvidia-driver--cuda-check)
  - [4. PyTorch (GPU)](#4-pytorch-gpu)
  - [5. Python Dependencies](#5-python-dependencies)
  - [6. Dataset](#6-dataset)
  - [7. Train the Model](#7-train-the-model)
  - [8. Arduino IDE & ESP32 Board](#8-arduino-ide--esp32-board)
  - [9. ESP32 Wiring](#9-esp32-wiring)
  - [10. Upload Firmware](#10-upload-firmware)
  - [11. Run Inference + Serial Control](#11-run-inference--serial-control)
- [Dataset Classes](#-dataset-classes)
- [ESP32 Pin Map](#-esp32-pin-map)
- [Script Reference](#-script-reference)
- [Fine-Tuning](#-fine-tuning)
- [Troubleshooting](#-troubleshooting)

---

## 🎥 Demo

> Four cameras feed into a 2×2 grid. YOLOv8 detects vehicles and their colors in real time. The ESP32 receives the direction command and switches the physical LEDs accordingly.

```
[Camera N]  [Camera E]        ESP32
[Camera S]  [Camera W]   →   N: 🟢 GREEN
     ↓                       E: 🔴 RED
  YOLOv8                     S: 🔴 RED
  Count                      W: 🔴 RED
     ↓
  Serial → COM5
```

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────┐
│              PC / Laptop                │
│                                         │
│  ┌──────────┐    ┌───────────────────┐  │
│  │ 4 Webcam │───▶│  YOLOv8n (CUDA)  │  │
│  │ Capture  │    │  Car Color Detect │  │
│  └──────────┘    └────────┬──────────┘  │
│                           │             │
│                  ┌────────▼──────────┐  │
│                  │  Traffic Logic    │  │
│                  │  (count per dir)  │  │
│                  └────────┬──────────┘  │
│                           │  PySerial   │
└───────────────────────────┼─────────────┘
                            │ USB
                   ┌────────▼──────────┐
                   │      ESP32        │
                   │  12 LED outputs   │
                   │  N / E / S / W    │
                   └───────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.11.9 |
| Deep Learning | PyTorch | ≥ 2.1 (CUDA) |
| Object Detection | Ultralytics YOLOv8 | Latest |
| Computer Vision | OpenCV | Latest |
| Serial Bridge | PySerial | Latest |
| Microcontroller | Arduino IDE | 2.3.9 |
| Board Package | ESP32 by Espressif | 3.0.7 |
| Hardware | ESP32 DevKit | — |

---

## 🔧 Hardware Requirements

- PC/Laptop with **NVIDIA GPU** (GTX / RTX series)
- **ESP32 DevKit** board (ESP32-WROOM-32 or equivalent)
- USB cable with **data lines** (not a charge-only cable)
- 4× USB Webcams (one per intersection direction)
- 12× LEDs (4 Red, 4 Yellow, 4 Green)
- 12× Resistors (220Ω – 330Ω)
- Breadboard + jumper wires

> **No GPU?** Training still works on CPU but will take much longer. Alternatively, use [Google Colab](https://colab.research.google.com/) for free GPU training.

---

## 📁 Project Structure

```
capstone-cuda/
│
├── dataset/                    # Roboflow-split dataset (80/20)
│   ├── train/
│   │   ├── images/             # 66 training images
│   │   └── labels/             # YOLO-format annotation .txt
│   └── valid/
│       ├── images/             # 18 validation images
│       └── labels/
│
├── train/                      # Raw collected images + labels (pre-split)
│   ├── images/
│   └── labels/
│
├── runs/                       # Auto-created by training; contains weights
│   └── detect/
│       └── car_color_detector*/
│           └── weights/
│               ├── best.pt     # ← use this for inference
│               └── last.pt
│
├── data.yaml                   # Dataset config (paths + 6 class names)
├── yolov8n.pt                  # YOLOv8 nano pretrained base weights
├── yolo26n.pt                  # Alternative pretrained weights
│
├── main.py                     # Training script (single dataset)
├── main newdataset.py          # Training script (new dataset)
├── main 4 cam.py               # Training script (4-cam config)
├── fine tuning data lama ke baru.py  # Fine-tune existing best.pt
├── split_dataset.py            # Split train/ → dataset/ (80/20)
│
├── webcam.py                   # Single webcam inference
├── 4_webcam.py                 # 4-camera 2×2 grid inference
├── list_webcam.py              # List all detected camera indices
├── tes kamera.py               # Basic camera availability test
└── test_4_webcam.py            # Verbose camera test with frame info
```

---

## ⚙️ Setup — Step by Step

### 1. Python 3.11.9

Download the **specific version** from the official release page (the homepage offers the latest, not 3.11.9):

👉 https://www.python.org/downloads/release/python-3119/

Pick **Windows installer (64-bit)**. During installation, **check "Add python.exe to PATH"** on the first screen before clicking Install Now — skipping this is the most common setup mistake.

Verify:
```bash
python --version
# Expected: Python 3.11.9
```

---

### 2. Virtual Environment

A virtual environment keeps this project's libraries isolated from everything else on your machine.

```bash
# Navigate to your project folder
cd capstone-cuda

# Create the virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Linux / Mac)
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal line. **Always activate this before running any command in this project.** To deactivate later: `deactivate`.

---

### 3. NVIDIA Driver & CUDA Check

Update your driver from [nvidia.com/Download](https://www.nvidia.com/Download/index.aspx), then run:

```bash
nvidia-smi
```

Note the **"CUDA Version"** shown in the top-right corner — this is the maximum CUDA version your driver supports. You'll need it in the next step.

> You do **not** need to install CUDA Toolkit separately. PyTorch wheels bundle the CUDA runtime.

---

### 4. PyTorch (GPU)

Go to the official selector to get the exact install command for your system and CUDA version:

👉 https://pytorch.org/get-started/locally/

Select: **Stable → Windows → Pip → Python → your CUDA version**

Example (for CUDA 12.1):
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Verify GPU is recognized:
```python
import torch
print(torch.cuda.is_available())    # Must be: True
print(torch.cuda.get_device_name(0))  # Must show your GPU name
```

If `False`: run `pip uninstall torch torchvision -y` then re-install with the correct CUDA version.

---

### 5. Python Dependencies

```bash
pip install ultralytics opencv-python pyserial
```

| Package | Purpose |
|---|---|
| `ultralytics` | YOLOv8 training & inference |
| `opencv-python` | Camera capture, frame display |
| `pyserial` | Serial communication with ESP32 |

---

### 6. Dataset

The dataset (already in this repo under `dataset/`) was collected and annotated via [Roboflow](https://roboflow.com/) and split 80/20 using `split_dataset.py`.

If you need to re-split from raw collected images:
```bash
python split_dataset.py
```

Check `data.yaml` — the `path` must match the actual location of the `dataset/` folder on your machine. Edit it if needed:
```yaml
path: /absolute/path/to/capstone-cuda/dataset

train: train/images
val:   valid/images

nc: 6
names:
  0: Mobil biru
  1: Mobil hijau
  2: Mobil kuning
  3: Mobil merah
  4: Mobil orange
  5: Mobil ungu
```

---

### 7. Train the Model

```bash
python main.py
```

This runs `yolov8n.pt` training for 100 epochs at 416×416 on GPU 0. Trained weights are saved to:
```
runs/detect/car_color_detector/weights/best.pt
```

Training parameters (editable in `main.py`):

| Parameter | Value | Notes |
|---|---|---|
| `epochs` | 100 | Increase for better accuracy |
| `imgsz` | 416 | Reduce to 320 if GPU runs out of memory |
| `batch` | 2 | Increase if VRAM allows (e.g. 8 or 16) |
| `device` | 0 | GPU index; use `"cpu"` for CPU-only |
| `workers` | 0 | Keep at 0 on Windows to avoid multiprocessing errors |

Validate after training:
```bash
yolo val model=runs/detect/car_color_detector/weights/best.pt data=data.yaml
```

Test on webcam (single camera):
```bash
python webcam.py
```

Test on 4 cameras simultaneously:
```bash
python 4_webcam.py
```

---

### 8. Arduino IDE & ESP32 Board

**Install Arduino IDE 2.3.9** — get this specific version from the GitHub releases page (the main arduino.cc page defaults to the latest):

👉 https://github.com/arduino/arduino-ide/releases/tag/2.3.9

**Add ESP32 board support:**

1. Open **File → Preferences**
2. In "Additional boards manager URLs", click the icon and add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Open **Tools → Board → Boards Manager**
4. Search `esp32`, find **"esp32 by Espressif Systems"**
5. From the **version dropdown**, select exactly **3.0.7** before clicking Install

**Select your board and port:**

- Tools → Board → esp32 → **ESP32 Dev Module**
- Plug in the ESP32 with a data-capable USB cable
- If no COM port appears: install the USB-serial driver
  - Chip says **CP2102/CP2104** → [Silicon Labs driver](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)
  - Chip says **CH340/CH9102** → search "CH340 driver download"
- Tools → Port → select the COM port that appeared

---

### 9. ESP32 Wiring

Each LED: `GPIO → 220Ω resistor → LED anode (+) → LED cathode (−) → GND`

All GND pins on the ESP32 share the same ground — connect all LED cathodes to any GND pin.

| Direction | Red LED | Yellow LED | Green LED |
|---|---|---|---|
| **North (N)** | GPIO 4 | GPIO 2 | GPIO 15 |
| **East (E)** | GPIO 27 | GPIO 14 | GPIO 12 |
| **South (S)** | GPIO 33 | GPIO 32 | GPIO 25 |
| **West (W)** | GPIO 19 | GPIO 18 | GPIO 5 |

> ⚠️ **Strapping pin note:** GPIO 2, 5, 12, and 15 are read by the ESP32 at boot. They are safe to use as LED outputs after boot completes, but avoid adding external pull-up resistors to these pins — especially GPIO 12. If the board sometimes fails to boot after uploading, move that LED to an unused pin such as GPIO 13, 16, 17, 21, 22, or 26.

---

### 10. Upload Firmware

Open the firmware sketch (`.ino` file) in Arduino IDE. Click **Verify** first, then **Upload**.

If you see `"Failed to connect to ESP32"`: hold the **BOOT** button on the ESP32 while clicking Upload, release it once the progress bar starts moving.

After upload, open **Tools → Serial Monitor** at baud **115200**. You should see:
```
ATCS_READY
```

Manual test — type this in Serial Monitor and press Enter:
```
N:GREEN,E:RED,S:RED,W:RED
```
Expected reply: `OK:N:GREEN,E:RED,S:RED,W:RED`
The green LED on the North direction should light up physically.

---

### 11. Run Inference + Serial Control

> **Important:** Close the Arduino IDE Serial Monitor before running any Python script — only one program can use a COM port at a time.

Edit `atcs_controller.py` and set your COM port:
```python
SERIAL_PORT = "COM5"   # change to your actual COM port
```

Then run:
```python
import serial, time

ser = serial.Serial("COM5", 115200, timeout=1)
time.sleep(2)

ser.write(b"N:GREEN,E:RED,S:RED,W:RED\n")
print(ser.readline().decode().strip())   # should print OK:...
```

The full loop (detection → count → send to ESP32) is handled by `atcs_controller.py` from the previous message.

---

## 🎨 Dataset Classes

The model detects vehicles by **color**, mapped to 6 classes:

| ID | Class Name | Color |
|---|---|---|
| 0 | Mobil biru | Blue car |
| 1 | Mobil hijau | Green car |
| 2 | Mobil kuning | Yellow car |
| 3 | Mobil merah | Red car |
| 4 | Mobil orange | Orange car |
| 5 | Mobil ungu | Purple car |

---

## 📌 ESP32 Pin Map

```
ESP32 DevKit
                          ┌──────────┐
              GND ────────┤          ├──── GPIO 23
              3V3 ────────┤          ├──── GPIO 22
                          │          ├──── GPIO 1  (TX0)
              GPIO 36 ────┤          ├──── GPIO 3  (RX0)
              GPIO 39 ────┤          ├──── GPIO 21
              GPIO 34 ────┤          ├──── GPIO 19 ← W RED
              GPIO 35 ────┤          ├──── GPIO 18 ← W YELLOW
              GPIO 32 ←── ┤ S YELLOW ├──── GPIO 5  ← W GREEN *
              GPIO 33 ←── ┤  S RED   ├──── GPIO 17
              GPIO 25 ←── ┤ S GREEN  ├──── GPIO 16
              GPIO 26 ────┤          ├──── GPIO 4  ← N RED
              GPIO 27 ←── ┤  E RED   ├──── GPIO 2  ← N YELLOW *
              GPIO 14 ←── ┤ E YELLOW ├──── GPIO 15 ← N GREEN *
              GPIO 12 ←── ┤  E GREEN ├──── GPIO 0  (BOOT)
              GND ────────┤    *     ├──── GND
              5V  ────────┤          ├──── 5V
                          └──────────┘
* = strapping pin (safe for LED use, avoid external pull-ups)
```

---

## 📜 Script Reference

| File | Purpose | When to Use |
|---|---|---|
| `main.py` | Train YOLOv8 on the dataset | First-time training |
| `main newdataset.py` | Same training with new dataset path | After updating dataset |
| `split_dataset.py` | Split raw `train/` into `dataset/` 80/20 | After collecting new images |
| `fine tuning data lama ke baru.py` | Fine-tune existing `best.pt` on new data | Improving an already-trained model |
| `webcam.py` | Run inference on 1 camera | Quick single-camera test |
| `4_webcam.py` | Run inference on 4 cameras in 2×2 grid | Full 4-direction live test |
| `list_webcam.py` | Print indices of all detected cameras | Check which cameras are available |
| `tes kamera.py` | Basic open/read test per camera | Debug camera connection |
| `test_4_webcam.py` | Verbose test with frame shape info | Debug frame issues |

---

## 🔁 Fine-Tuning

If you collect new images and want to improve the existing model without starting from scratch:

1. Add new images + labels to `train/images/` and `train/labels/`
2. Re-run the splitter: `python split_dataset.py`
3. Update the path inside `fine tuning data lama ke baru.py` to point to the current `best.pt`
4. Run: `python "fine tuning data lama ke baru.py"`

This resumes from the trained weights and adapts to the new data in 50 epochs instead of 100.

---

## 🐛 Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| `python` not found | PATH not set during install | Re-install Python, check "Add to PATH" |
| `torch.cuda.is_available()` returns `False` | Wrong CUDA wheel or CPU-only PyTorch installed | `pip uninstall torch torchvision -y` then reinstall with correct CUDA version |
| COM port not visible | Driver not installed or charge-only cable | Install CP2102 or CH340 driver; use a data cable |
| `Failed to connect to ESP32` | Board not in download mode | Hold BOOT button during upload |
| Port busy / access denied | Serial Monitor still open | Close Arduino IDE Serial Monitor before running Python |
| ESP32 fails to boot after wiring | Pull-up on GPIO 12 or 2 | Remove external pull-ups or move LED to GPIO 13/16/17 |
| Camera index not found | USB webcam enumeration varies | Run `list_webcam.py` first to find correct indices |
| `workers` multiprocessing error | Windows DataLoader limitation | Keep `workers=0` in all training scripts (already set) |
| Out of GPU memory | Batch size or image size too large | Reduce `batch` to 1 or `imgsz` to 320 in `main.py` |

---

## 📄 License

This project was created as a capstone/academic project. Feel free to use and adapt with attribution.

# 🚦 ATCS — Adaptive Traffic Control System
### Background Subtraction + ESP32 + Flask Web Dashboard

A computer vision-based adaptive traffic light system that detects vehicle density using **background subtraction** (no deep learning required) via a single overhead webcam, runs a smart phase-selection algorithm on the ESP32 itself, and exposes a real-time **Flask web dashboard** for monitoring. Includes a Firebase Realtime Database variant for wireless control, SolidWorks 3D prototype models, and a browser-based traffic cycle simulator.

---

## 📋 Table of Contents

- [System Overview](#-system-overview)
- [How It Works](#-how-it-works)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Hardware Requirements](#-hardware-requirements)
- [ESP32 Pin Map](#-esp32-pin-map)
- [Setup — Step by Step](#-setup--step-by-step)
  - [1. Python & Dependencies](#1-python--dependencies)
  - [2. Calibration — Background & ROI](#2-calibration--background--roi)
  - [3. Run the System](#3-run-the-system)
  - [4. Arduino IDE & ESP32 Board](#4-arduino-ide--esp32-board)
  - [5. Choose Your Firmware](#5-choose-your-firmware)
  - [6. Upload & Verify](#6-upload--verify)
- [Serial Protocol](#-serial-protocol)
- [Phase Logic & Green Duration](#-phase-logic--green-duration)
- [Flask Web Dashboard](#-flask-web-dashboard)
- [Firebase Variant](#-firebase-variant)
- [Firmware Reference](#-firmware-reference)
- [Simulation & 3D Models](#-simulation--3d-models)
- [Troubleshooting](#-troubleshooting)

---

## 🔭 System Overview

```
┌──────────────────────────────────────────────┐
│                  PC / Laptop                 │
│                                              │
│  Webcam (top-down)                           │
│       │                                      │
│  cv2.absdiff(frame, bg)                      │
│       │  Background Subtraction              │
│  Threshold → Morphology → Contour Count      │
│       │                                      │
│  counts: N=3  E=0  S=7  W=1                 │
│       │                                      │
│  ┌────┴────────────┐                         │
│  │ Flask Dashboard │  ← browser :5000        │
│  └────────────────┘                         │
│       │  Serial (USB)  or  WiFi (Firebase)   │
└───────┼──────────────────────────────────────┘
        │ "N3 E0 S7 W1\n"
┌───────▼──────────────────────────────────────┐
│                   ESP32                      │
│                                              │
│  Receive counts → pickNextDir() algorithm    │
│  Anti-starvation logic (60s cap)             │
│  State machine: GREEN → YELLOW → CLEARANCE  │
│       │                                      │
│  12 GPIO pins → 4 traffic light modules      │
│  N / E / S / W                               │
└──────────────────────────────────────────────┘
```

---

## 🧠 How It Works

**Step 1 — Calibration (one-time):**
Run `kalibrasi.py` to capture an empty-road background image (`bg.jpg`) and draw 4 ROI rectangles (one per direction) saved as `roi_config.json`.

**Step 2 — Detection loop:**
For each frame, `main.py` computes `cv2.absdiff(frame, background)`, thresholds and cleans the result with morphological operations, then counts external contours above `MIN_AREA=150px²` inside each ROI. This number (0–14 per direction) is the vehicle count.

**Step 3 — Send to ESP32:**
Every 250ms, a compact serial message is sent: `N3 E0 S7 W1\n`. The ESP32 receives this and makes all timing decisions autonomously.

**Step 4 — Smart phase selection:**
The ESP32 (`Firmware.ino`) uses a 4-tier priority algorithm to pick which direction gets green next, runs the state machine (GREEN → YELLOW → CLEARANCE → next), and sends status back over serial for the dashboard.

---

## 🛠 Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.x |
| Computer Vision | OpenCV (`cv2`) |
| Web Framework | Flask |
| Serial Bridge | PySerial |
| Microcontroller firmware | Arduino (C++) |
| Board | ESP32 DevKit V1 |
| IoT (optional) | Firebase Realtime Database |
| 3D Design | SolidWorks (.SLDPRT / .SLDASM) |

---

## 📁 Project Structure

```
Background Substraction/
│
├── ATCS Project/                   # ✅ Main implementation
│   ├── main.py                     # Vision loop + serial + Flask dashboard
│   ├── kalibrasi.py                # Two-step calibration tool
│   └── templates/
│       └── Dashboard.html          # Real-time web UI (polls /api/state)
│
├── Firmware/                       # ESP32 firmware variants
│   ├── Firmware.ino                # ⭐ Recommended: smart phase + anti-starvation
│   ├── ATCS_Firmware.ino           # Simple: receives color commands (N:GREEN,...)
│   ├── esp.ino                     # WiFi + Firebase variant
│   └── Prototype___.ino            # Prototype version (same as ATCS_Firmware)
│
├── 3D/
│   ├── 3D Models/                  # SolidWorks parts & assembly
│   │   ├── prototype.SLDASM        # Full assembly
│   │   ├── crossrode.SLDPRT        # Intersection base
│   │   ├── gray_car.SLDPRT         # Car models (gray/red/white/yellow)
│   │   ├── ESP32.SLDPRT            # ESP32 board model
│   │   ├── Arm.SLDPRT              # Camera mount arm
│   │   └── cameraa .SLDPRT         # Camera model
│   └── 3D Render/
│       └── 1.png                   # Rendered prototype photo
│
├── Simulasi/
│   └── Simulasi_All_Siklus.html   # ⭐ Browser traffic cycle simulator
│
├── Prototype/
│   ├── Prototype.html              # Browser simulation
│   └── Prototype.jpeg              # Hardware prototype photo
│
├── Implementasi/                   # Full production folder (git-tracked)
│   ├── ATCS Project/               # Mirror of main ATCS Project
│   ├── Firmware/
│   ├── requirements.txt
│   ├── README.md
│   └── .gitignore
│
├── main.py                         # Legacy: Firebase + cvzone (older approach)
├── main.cpp                        # Legacy: ESP32 Firebase C++ firmware
└── StreetPicker.py                 # Legacy: slot-based ROI picker
```

---

## 🔧 Hardware Requirements

| Component | Qty | Notes |
|---|---|---|
| PC / Laptop | 1 | Any; no GPU needed |
| USB Webcam | 1 | Minimum 640×480, mounted top-down |
| ESP32 DevKit V1 | 1 | ESP32-WROOM-32 or equivalent |
| USB cable (data) | 1 | Not a charge-only cable |
| Traffic light modules (R/Y/G) | 4 | One per direction |
| Jumper wires | — | |
| Intersection scale model | 1 | Flat top-down view, stable lighting |
| Toy cars (~3–4 cm) | up to 56 | 14 per lane max |

> **Lighting is critical.** Background subtraction fails with flickering or changing ambient light. Use constant indoor lighting and avoid direct sunlight through windows.

---

## 📌 ESP32 Pin Map

These are the pins used in `Firmware.ino` and `ATCS_Firmware.ino`:

| Direction | Red LED | Yellow LED | Green LED |
|---|---|---|---|
| **North (N)** | GPIO 4 | GPIO 2 | GPIO 15 |
| **East (E)** | GPIO 27 | GPIO 14 | GPIO 12 |
| **South (S)** | GPIO 33 | GPIO 32 | GPIO 25 |
| **West (W)** | GPIO 19 | GPIO 18 | GPIO 5 |

All LED cathodes (−) → any GND pin on the ESP32.
Each LED needs a **220Ω–330Ω resistor** in series.

> ⚠️ GPIO 2, 5, 12, 15 are strapping pins read at boot. They are safe to use as outputs after boot, but avoid adding pull-up resistors to these pins. If the board fails to boot after wiring, move the LED on GPIO 12 to GPIO 13, 16, 17, 21, 22, or 26.

---

## ⚙️ Setup — Step by Step

### 1. Python & Dependencies

```bash
pip install opencv-python numpy flask pyserial
```

Full pinned versions (from `requirements.txt`):
```
opencv-python==4.8.1.78
numpy==1.26.4
flask
pyserial
```

For the legacy Firebase approach (`root/main.py`), additionally:
```bash
pip install cvzone firebase-admin
```

---

### 2. Calibration — Background & ROI

This is a **required one-time step** before running `main.py`. It produces two files that the main script depends on: `bg.jpg` and `roi_config.json`.

```bash
cd "ATCS Project"
python kalibrasi.py
```

**Step 1 — Capture background:**
- Make sure the intersection model is completely **empty** (no toy cars)
- A live camera preview appears
- Press **SPACEBAR** to capture and save `bg.jpg`

**Step 2 — Draw 4 ROIs:**
A selection tool opens on the captured background. For each of the 4 directions:
- Click and drag to draw a rectangle covering the lane area where vehicles wait
- Press **ENTER** to confirm each ROI
- Repeat 4 times (North → East → South → West)
- `roi_config.json` is saved automatically when all 4 are done

```json
{
  "N": [x, y, width, height],
  "E": [x, y, width, height],
  "S": [x, y, width, height],
  "W": [x, y, width, height]
}
```

**ROI tips:**
- Draw the ROI to cover the full queue area (not just the stop line)
- Bigger ROI = more vehicles counted, but also more noise from lane edges
- If detection is wrong after setup, re-run calibration with better lighting

---

### 3. Run the System

```bash
cd "ATCS Project"
python main.py
```

What happens on launch:
1. Loads `roi_config.json` (exits with error if not found — run calibration first)
2. Loads `bg.jpg` as the reference background
3. Opens webcam index `0` (change `CAMERA_INDEX` at top of file if needed)
4. Starts Flask dashboard thread at `http://localhost:5000`
5. Tries to connect to ESP32 on `COM3` at 115200 baud (continues without it if not found, with a warning)
6. Opens a window showing live feed with colored ROI boxes and vehicle counts

**Configuration variables at the top of `main.py`:**

| Variable | Default | Description |
|---|---|---|
| `SERIAL_PORT` | `'COM3'` | ESP32 COM port (check Device Manager) |
| `CAMERA_INDEX` | `0` | Webcam index |
| `SEND_INTERVAL` | `0.25` | Seconds between serial sends |
| `MIN_AREA` | `150` | Minimum contour area (px²) to count as a vehicle |
| `THRESH_VAL` | `30` | Pixel difference threshold for bg subtraction |
| `FLASK_PORT` | `5000` | Web dashboard port |

Press **Q** in the camera window to stop.

---

### 4. Arduino IDE & ESP32 Board

Install **Arduino IDE 2.3.9** from the GitHub releases page:
👉 https://github.com/arduino/arduino-ide/releases/tag/2.3.9

Add ESP32 board support:
1. **File → Preferences** → "Additional boards manager URLs" → add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
2. **Tools → Board → Boards Manager** → search `esp32` → install **"esp32 by Espressif Systems" version 3.0.7**
3. **Tools → Board** → select **ESP32 Dev Module**
4. Plug in ESP32, install USB-serial driver if COM port is not visible:
   - **CP2102/CP2104 chip** → [Silicon Labs VCP driver](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)
   - **CH340/CH9102 chip** → search "CH340 driver download"
5. **Tools → Port** → select the correct COM port

---

### 5. Choose Your Firmware

There are three firmware options depending on your setup:

**`Firmware.ino` ← Recommended for wired serial**
The ESP32 receives vehicle counts (`N3 E0 S7 W1\n`) and handles all traffic logic itself: picks the busiest direction, runs GREEN→YELLOW→CLEARANCE state machine, implements anti-starvation, sends STATE updates back to Python. This is the most capable version.

**`ATCS_Firmware.ino` — Simple command-receiver**
Receives pre-computed color commands from Python (`N:GREEN,E:RED,S:RED,W:RED\n`) and just sets the LEDs accordingly. Use this if you want Python to control all traffic logic.

**`esp.ino` — WiFi + Firebase hybrid**
Connects to WiFi, receives color commands via serial, executes them, and also pushes status to Firebase Realtime Database. Requires WiFi credentials and a Firebase project (see [Firebase Variant](#-firebase-variant) section).

---

### 6. Upload & Verify

1. Open the chosen `.ino` file in Arduino IDE
2. Click **Verify** first to check for errors
3. Click **Upload**
4. If you see `"Failed to connect to ESP32"`: hold the **BOOT** button on the board while clicking Upload, release once the progress bar starts moving
5. Open **Tools → Serial Monitor** at **115200 baud**

Expected boot message for `Firmware.ino`:
```
ATCS READY
PHASE S GREEN dur=15000 cnt=7
```

Expected boot message for `ATCS_Firmware.ino`:
```
ATCS_READY
```

> **Close Serial Monitor before running `main.py`** — both cannot share the COM port at the same time.

---

## 📡 Serial Protocol

### Python → ESP32 (vehicle counts)

Used by `Firmware.ino` (the recommended smart firmware):
```
N3 E0 S7 W1\n
```
Direction letter followed immediately by count (0–14), space-separated, newline-terminated. Sent every 250ms.

### Python → ESP32 (color commands)

Used by `ATCS_Firmware.ino` and `esp.ino`:
```
N:GREEN,E:RED,S:RED,W:RED\n
```

### ESP32 → Python (status)

`Firmware.ino` sends two types of messages back:

```
STATE S GREEN rem=12400 cnt=7 N=3 E=0 S=7 W=1
```
Sent every 300ms — current phase direction, state, remaining milliseconds, all counts.

```
PHASE S YELLOW
PHASE ALL CLEARANCE
PHASE N GREEN dur=5000 cnt=2
```
Sent on each phase transition — picked up by the Flask dashboard log.

---

## 📊 Phase Logic & Green Duration

The smart firmware (`Firmware.ino`) implements a full state machine on the ESP32:

```
ALL RED (clearance 2.0s)
       ↓
  pickNextDir()
       ↓
  count = 0? → SKIP (0.6s) → pickNextDir()
       ↓
  GREEN (5–20s based on count)
       ↓
  YELLOW (2.5s)
       ↓
  CLEARANCE (2.0s) → pickNextDir()
```

**Green duration table:**

| Vehicle Count | Duration |
|:---:|---|
| 0 | Skip (0.6s) |
| 1–2 | 5 seconds |
| 3–5 | 10 seconds |
| 6–9 | 15 seconds |
| ≥ 10 | 20 seconds |

**Direction selection — `pickNextDir()` priority:**

1. **Highest count** — the direction with the most detected vehicles gets green
2. **Earliest ROI entry** — if tied, the direction whose vehicles appeared first wins (`firstNonZero` timestamp)
3. **Longest wait** — if still tied, the direction that has been waiting longest wins
4. **Anti-starvation cap** — wait time is capped at 60,000ms so no direction can be starved indefinitely

Max vehicles per ROI is capped at 14 (`val >= 0 && val <= 14` in parser).

---

## 🖥 Flask Web Dashboard

`main.py` starts a Flask server at `http://localhost:5000` in a background thread. It serves `templates/Dashboard.html` and a JSON API:

```
GET /          → serves Dashboard.html
GET /api/state → returns current system state as JSON
```

Example `/api/state` response:
```json
{
  "counts":    { "N": 3, "E": 0, "S": 7, "W": 1 },
  "phase":     { "dir": "S", "state": "GREEN", "rem_ms": 12400, "cnt": 7 },
  "connected": true,
  "cycle":     14,
  "log": [
    { "ts": "14:32:01", "msg": "PHASE S GREEN dur=15000 cnt=7", "level": "ok" },
    { "ts": "14:31:58", "msg": "Serial terhubung: COM3", "level": "ok" }
  ]
}
```

The dashboard HTML polls `/api/state` periodically and renders live counts, current phase, cycle count, and a scrollable activity log. Open `http://localhost:5000` in any browser while `main.py` is running.

---

## 🔥 Firebase Variant

`esp.ino` adds WiFi connectivity and Firebase Realtime Database logging. To use it:

**1. Create a Firebase project:**
- Go to [console.firebase.google.com](https://console.firebase.google.com)
- Create project → Realtime Database → Start in test mode
- Copy the database URL: `https://your-project-default-rtdb.firebaseio.com`
- Project Settings → Service accounts → scroll down → copy **Database secret**

**2. Install Arduino library:**
- Arduino IDE → **Sketch → Include Library → Manage Libraries**
- Search `Firebase ESP Client` by Mobizt → Install

**3. Edit `esp.ino` credentials:**
```cpp
#define WIFI_SSID      "your_wifi_name"
#define WIFI_PASSWORD  "your_wifi_password"
#define FIREBASE_HOST  "your-project-default-rtdb.firebaseio.com"
#define FIREBASE_AUTH  "your_database_secret"
```

**Firebase data structure written by ESP32:**
```
/atcs/
├── raw_state        "N:GREEN,E:RED,S:RED,W:RED"
├── timestamp        1234567
├── north/color      "GREEN"
├── east/color       "RED"
├── south/color      "RED"
└── west/color       "RED"
```

If you get `PERMISSION_DENIED` in Serial Monitor, update Firebase Rules:
```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```
*(for prototype/testing only — restrict before deploying)*

---

## 📜 Firmware Reference

| File | Input format | Who decides timing | Firebase |
|---|---|---|---|
| `Firmware.ino` | `N3 E0 S7 W1\n` | ✅ ESP32 itself | ❌ |
| `ATCS_Firmware.ino` | `N:GREEN,E:RED,...\n` | Python / external | ❌ |
| `esp.ino` | `N:GREEN,E:RED,...\n` | Python / external | ✅ |
| `Prototype___.ino` | `N:GREEN,E:RED,...\n` | Python / external | ❌ |

**Which to use:**
- `Firmware.ino` → best for production; all logic on the microcontroller, minimal Python involvement
- `ATCS_Firmware.ino` → best when Python handles all logic (e.g. combined with the YOLOv8 project)
- `esp.ino` → best for remote monitoring or when ESP32 cannot be physically connected by USB

---

## 🎮 Simulation & 3D Models

**Browser Simulator:**
Open `Simulasi/Simulasi_All_Siklus.html` directly in any browser (no server needed). Simulates the complete traffic cycle including the pickNextDir algorithm, anti-starvation, and all phase transitions. Useful for verifying logic before deploying on hardware.

**3D Models (SolidWorks):**
`3D/3D Models/` contains the full SolidWorks prototype design:

| File | Description |
|---|---|
| `prototype.SLDASM` | Full assembly of the scale model |
| `crossrode.SLDPRT` | 4-way intersection base plate |
| `gray_car.SLDPRT` | Gray toy car |
| `red_car.SLDPRT` | Red toy car |
| `white_car.SLDPRT` | White toy car |
| `yellow_car.SLDPRT` | Yellow toy car |
| `rick2022.SLDPRT` | Truck model |
| `ESP32.SLDPRT` | ESP32 board model |
| `Arm.SLDPRT` | Camera mounting arm |
| `cameraa .SLDPRT` | USB webcam model |
| `street.SLDPRT` | Road section |
| `car_surface.stp` | STEP format (importable in other CAD tools) |

Requires **SolidWorks 2022+** to open `.SLDPRT` and `.SLDASM`. The `.stp` file can be opened in FreeCAD, Fusion 360, or any STEP-compatible CAD tool.

---

## 🐛 Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| `roi_config.json not found` | Calibration not run | Run `python kalibrasi.py` first |
| `bg.jpg not readable` | Background not captured or file missing | Re-run `kalibrasi.py` from ATCS Project/ folder |
| Vehicles not detected | `MIN_AREA` too high or lighting changed | Lower `MIN_AREA` to 50–100, or recalibrate with `kalibrasi.py` |
| Too many false positives | Shadows / glare / `THRESH_VAL` too low | Raise `THRESH_VAL` from 30 to 50–80; stabilize lighting |
| COM port busy / access denied | Serial Monitor still open | Close Arduino IDE Serial Monitor |
| `Failed to connect to ESP32` | Board not in download mode | Hold BOOT button during Upload |
| ESP32 fails to boot after wiring | Pull-up on strapping pin (GPIO 12) | Remove pull-ups or move that LED to GPIO 13, 16, or 17 |
| Firebase `PERMISSION_DENIED` | Database rules in locked mode | Set `.read` and `.write` to `true` in Firebase Rules |
| Flask page not loading | Port 5000 in use by another process | Change `FLASK_PORT` in `main.py` |
| Camera index wrong | Webcam not on index 0 | Change `CAMERA_INDEX = 1` (or 2) in `main.py` |
| Counts jump wildly | Camera shaking or lighting change | Fix camera mount; avoid variable light sources |

---

## 🔗 Related Project

This project uses the same ESP32 pin map and `ATCS_Firmware.ino` as the companion **YOLOv8 car color detection** project (`capstone-cuda`), which replaces background subtraction with a trained deep learning model for more robust vehicle detection under varying conditions. Both projects share the same ESP32 firmware and serial protocol, so the two Python systems can be swapped interchangeably on the same hardware.

---

## 📄 License

Academic capstone project. Feel free to use and adapt with attribution.
