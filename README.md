# 🚦 Adaptive Traffic Control System (ATCS)
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
