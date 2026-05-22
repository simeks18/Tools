# photo_layout.py

A batch photo layout tool that arranges photos for printing — either as two 2×3 photos
on a single 4×6 print, or tiled as 2×3 photos across a full letter-size (8.5×11) sheet.

Runs as a GUI application or fully headless from the command line.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
  - [GUI](#gui)
  - [Command Line](#command-line)
  - [Flags](#flags)
- [Print Dimensions](#print-dimensions)
- [Layout Behavior](#layout-behavior)
- [Supported Formats](#supported-formats)
- [Output Naming](#output-naming)
- [Error Handling](#error-handling)
- [Performance Notes](#performance-notes)
- [Platform Support](#platform-support)
- [Troubleshooting](#troubleshooting)
- [How It Works](#how-it-works)
- [Known Limitations](#known-limitations)
- [License](#license)

---

## Quick Start

```bash
pip install Pillow pillow-heif
python photo_layout.py
```

---

## Installation

**Required:**
```bash
pip install Pillow
```

**Optional — needed for iPhone HEIC/HEIF photos:**
```bash
pip install pillow-heif
```

**Tkinter** (GUI only) — usually bundled with Python. If missing on Ubuntu/WSL:
```bash
sudo apt install python3-tk
```

---

## Usage

### GUI

Run with no arguments (or with only some flags) to open the graphical interface:

```bash
python photo_layout.py
```

The GUI lets you:
- Select input and output folders via file browser dialogs
- Choose between 4×6 and letter-sheet modes
- Adjust DPI, columns, and rows
- Watch a live progress bar as files are processed

### Command Line

All three of `--mode`, `--input`, and `--output` are required for a fully headless run.
If any one is missing, the GUI opens instead — with whatever you did pass already pre-filled.

```bash
# 4×6 mode — one output per input photo
python photo_layout.py --mode 4x6 --input ./photos --output ./out

# Letter sheet mode — tile photos across 8.5×11 pages
python photo_layout.py --mode letter --input ./photos --output ./out

# Custom grid and DPI
python photo_layout.py --mode letter --input ./photos --output ./out --cols 3 --rows 4 --dpi 600

# Pre-fill input folder, open GUI for the rest
python photo_layout.py --input /mnt/c/Users/You/Pictures
```

### Flags

| Flag | Type | Default | Description |
|---|---|---|---|
| `--mode` | `4x6` or `letter` | *(none)* | Layout mode — required for headless run |
| `--input` | path | *(none)* | Input folder — top-level only, no subdirectories |
| `--output` | path | *(none)* | Output folder — created automatically if it doesn't exist |
| `--dpi` | int | `300` | Output resolution in dots per inch |
| `--cols` | int | `4` | Columns per letter sheet *(letter mode only)* |
| `--rows` | int | `3` | Rows per letter sheet *(letter mode only)* |

`--cols` and `--rows` are silently ignored in `4x6` mode.

---

## Print Dimensions

### 4×6 Mode

| Property | Value |
|---|---|
| Output canvas | 4 × 6 inches |
| Photo regions | Two 2×3 inch cells side-by-side |
| Gap between photos | ⅛ inch |
| Outer margin | ⅛ inch on all sides |
| Output DPI | Configurable (default 300) |

Each input photo produces one output file containing two copies of itself.
This is the standard layout for splitting a 4×6 print into two wallet/ID-size prints.

### Letter Mode

| Property | Value |
|---|---|
| Output canvas | 8.5 × 11 inches |
| Default grid | 4 columns × 3 rows = **12 photos per sheet** |
| Cell size | Calculated from canvas minus margins, divided by grid |
| Gap between photos | ⅛ inch |
| Outer margin | ⅛ inch on all sides |
| Output DPI | Configurable (default 300) |

Photos fill sheets sequentially. If the last sheet isn't full, remaining cells are left white.

---

## Layout Behavior

- Images are **scaled proportionally** to fit their cell — aspect ratio is always preserved.
- If the image aspect ratio doesn't match the cell, **white padding** is added on the
  shorter sides (letterboxed/pillarboxed). Photos are never stretched or distorted.
- All output files are **JPEG** with quality 95.
- Output files embed the DPI value in their metadata for accurate print sizing.

---

## Supported Formats

Any format Pillow can open is accepted. Common formats include:

| Extension | Format |
|---|---|
| `.jpg` / `.jpeg` | JPEG |
| `.png` | PNG |
| `.bmp` | Bitmap |
| `.webp` | WebP |
| `.tiff` / `.tif` | TIFF |
| `.heic` / `.heif` | iPhone photos *(requires `pillow-heif`)* |

Files with unsupported extensions are silently skipped.
Corrupted or unreadable files are skipped with a warning — they do not stop the batch.

---

## Output Naming

Output files are written to the `--output` directory and **never overwrite originals**.
The input folder is never modified.

| Mode | Pattern | Example |
|---|---|---|
| 4×6 | `{original_stem}_4x6.jpg` | `IMG_0042_4x6.jpg` |
| Letter | `sheet_001.jpg`, `sheet_002.jpg`, … | `sheet_003.jpg` |

If a file with the same output name already exists in the output folder, it is overwritten
(re-running the tool on the same folder regenerates all outputs cleanly).

---

## Error Handling

| Situation | Behavior |
|---|---|
| Output folder doesn't exist | Created automatically (including parent directories) |
| Input folder doesn't exist | Error shown; processing does not start |
| Input folder is empty | Processing completes immediately with 0 files |
| Unreadable or corrupted image | File is skipped; processing continues |
| Permission error on output | Error shown in GUI dialog or printed to stderr in CLI |
| `pillow-heif` not installed | HEIC/HEIF files are skipped; all other formats still work |

The tool is designed to process as much of a batch as possible and report problems
rather than abort on first failure.

---

## Performance Notes

| Factor | Impact |
|---|---|
| Higher DPI | Larger canvas in pixels → more memory, slower processing, bigger output files |
| More photos per sheet | More Pillow compositing operations per output file |
| Large input images | More memory needed for scaling; Pillow streams where possible |
| HEIC files | Slightly slower to decode than JPEG due to codec overhead |

Rough estimates at 300 DPI on a modern machine:

- **4×6 mode:** ~0.5–1 second per photo
- **Letter mode:** ~1–3 seconds per sheet (12 photos at 300 DPI)

For very large batches (500+ photos) at 600 DPI, expect several minutes and
at least 1–2 GB of RAM in use. Processing is single-threaded.

---

## Platform Support

| Platform | Status |
|---|---|
| WSL (Ubuntu on Windows) | ✅ Tested |
| Ubuntu / Debian Linux | ✅ Supported |
| Windows (native Python) | ✅ Supported |
| macOS | ✅ Should work — not formally tested |

The GUI uses **Tkinter**, which is cross-platform and included with most Python distributions.

---

## Troubleshooting

### GUI does not open

Make sure Tkinter is installed. On Ubuntu/WSL it is not always bundled:

```bash
sudo apt install python3-tk
```

On Windows, reinstall Python and check **"tcl/tk and IDLE"** in the installer options.

### HEIC files are not processed

Install the optional HEIF library:

```bash
pip install pillow-heif
```

If it still doesn't work on WSL, you may need the system codec:

```bash
sudo apt install libheif-dev
pip install --force-reinstall pillow-heif
```

### Pillow is missing

```bash
pip install Pillow
```

### Output photos are the wrong size when printed

Make sure your printer is set to **"actual size"** or **100% scale** — not "fit to page."
The DPI metadata embedded in the file tells the printer the correct physical size.
Use `--dpi 300` (default) for standard photo printing.

### Photos look blurry or pixelated

Increase DPI. For high-quality photo prints, 300 DPI is the standard minimum.
600 DPI is better for small prints viewed up close.

### The progress bar freezes

The GUI runs processing on the main thread. For very large batches the window may
become briefly unresponsive between file updates. This is cosmetic — processing
continues normally.

---

## How It Works

1. **Discover** — scans the input folder for image files (non-recursive)
2. **Load** — opens each image with Pillow (or pillow-heif for HEIC)
3. **Scale** — resizes proportionally to fit the target cell using Lanczos resampling
4. **Pad** — centers the scaled image on a white canvas matching the exact cell size
5. **Composite** — pastes photo cells onto a blank white print canvas at calculated positions
6. **Save** — writes the final canvas as JPEG with quality 95 and embedded DPI metadata

---

## Known Limitations

- No recursive directory scanning — only the top-level input folder is processed
- JPEG output only — no PDF, PNG, or TIFF output option
- No custom page sizes — only 4×6 and letter (8.5×11) are supported
- No EXIF rotation correction — photos shot in portrait orientation may appear sideways
  if the camera stored them as landscape with a rotation tag
- No duplicate detection — if the same image appears under two names, it is processed twice
- Single-threaded — does not use multiple CPU cores
- No preview — the GUI does not show a layout preview before processing

---

## License

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
