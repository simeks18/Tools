# Photo Layout Utility

A simple Python tool for preparing printable photo sheets.

* **4×6 Mode** → creates 4×6 print images with the same photo duplicated side-by-side as two 2×3 prints
* **Letter Mode** → arranges multiple photos onto standard 8.5×11 printable sheets
* Supports both:

  * **GUI workflow**
  * **Fully headless CLI workflow**

---

# Features

## 4×6 Mode

For every image in the input folder:

* Produces **one 4×6 JPG**
* Places the **same image twice side-by-side**
* Creates two printable **2×3 photo areas**
* Automatically handles aspect ratio differences using:

  * scale-to-fit
  * white padding/margins

### Example Layout

```text
+---------------------------+
|     Photo     |   Photo   |
|               |           |
|    2×3 area   |  2×3 area |
+---------------------------+
          4×6 output
```

---

## Letter Mode

Collects all photos and tiles them onto:

* **8.5×11 inch sheets**
* Default grid:

  * `4 columns × 3 rows`
  * `12 photos per sheet`

Extra photos automatically continue onto additional pages.

### Example Layout

```text
+-----------------------------------+
| [] [] [] []                       |
| [] [] [] []   8.5×11 Sheet        |
| [] [] [] []                       |
+-----------------------------------+
```

---

# Installation (WSL / Linux)

## Install Pillow

```bash
pip install Pillow
```

---

# Running the Application

## Launch the GUI

```bash
python photo_layout.py
```

If required CLI arguments are missing, the GUI opens automatically.

---

# GUI Features

The GUI includes:

* Folder picker dialogs
* DPI spinner
* Columns/rows spinners
* Live progress bar
* Status line showing current file being processed

### Mode-Specific Behavior

* In **4×6 mode**:

  * columns/rows controls are disabled
  * output always contains exactly two photos per sheet

* In **Letter mode**:

  * grid dimensions are configurable

---

# Command Line Usage

## Fully Headless Requirements

For a completely headless run, all of the following are required:

* `--mode`
* `--input`
* `--output`

If any are missing:

* the GUI opens instead
* any provided values are pre-filled automatically

---

# CLI Examples

## 4×6 Mode

```bash
python photo_layout.py --mode 4x6 --input ./photos --output ./out
```

---

## Letter Mode (Default Grid)

```bash
python photo_layout.py --mode letter --input ./photos --output ./out
```

---

## Letter Mode with Custom Grid + DPI

```bash
python photo_layout.py \
  --mode letter \
  --input ./photos \
  --output ./out \
  --cols 4 \
  --rows 3 \
  --dpi 300
```

---

## Partial Arguments → GUI Opens

```bash
python photo_layout.py --input ./photos
```

This launches the GUI with the input field already populated.

---

# Command Line Flags

| Flag       | Type              | Default  | Description                                           |
| ---------- | ----------------- | -------- | ----------------------------------------------------- |
| `--mode`   | `4x6` or `letter` | *(none)* | Layout mode                                           |
| `--input`  | path              | *(none)* | Input folder (top-level scan only, no subdirectories) |
| `--output` | path              | *(none)* | Output folder (created automatically if missing)      |
| `--dpi`    | integer           | `300`    | Output resolution in DPI                              |
| `--cols`   | integer           | `4`      | Number of columns in letter mode                      |
| `--rows`   | integer           | `3`      | Number of rows in letter mode                         |

---

# Important Notes

## Input Folder Behavior

* Only scans the **top level**
* Does **not** recurse into subdirectories

---

## Output Folder Behavior

* Automatically created if it does not exist

---

## `--cols` and `--rows` in 4×6 Mode

These flags are accepted but ignored in `4x6` mode.

Reason:

* 4×6 mode always generates:

  * exactly one sheet
  * exactly two photo slots

Example:

```bash
python photo_layout.py \
  --mode 4x6 \
  --input ./photos \
  --output ./out \
  --cols 99 \
  --rows 99
```

Still produces standard 4×6 dual-photo layouts.

---

# Typical Workflow

## GUI Workflow

```text
1. Launch application
2. Select input folder
3. Select output folder
4. Choose mode
5. Adjust DPI/grid if needed
6. Click Generate
```

---

## Headless Workflow

```text
1. Prepare input folder
2. Run CLI command
3. Generated sheets appear in output directory
```

---

# Example Output Structure

```text
project/
├── photo_layout.py
├── photos/
│   ├── img1.jpg
│   ├── img2.jpg
│   └── img3.jpg
└── out/
    ├── sheet_001.jpg
    ├── sheet_002.jpg
    └── ...
```

---

# Requirements

* Python 3
* Pillow (`PIL`)

Install dependency:

```bash
pip install Pillow
```

---

# Quick Start

```bash
pip install Pillow
python photo_layout.py
```
