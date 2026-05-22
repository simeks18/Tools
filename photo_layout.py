#!/usr/bin/env python3
"""
photo_layout.py — Batch photo layout tool

Modes:
  4x6   : Place two 2x3 photos side-by-side on a 4x6 print (one input → one output)
  letter: Tile multiple 2x3 photos on a letter-size sheet (8.5x11)

Usage:
  python photo_layout.py                     # Launch GUI
  python photo_layout.py --help              # Show CLI help

CLI examples:
  python photo_layout.py --mode 4x6     --input ./photos --output ./out
  python photo_layout.py --mode letter  --input ./photos --output ./out
  python photo_layout.py --mode letter  --input ./photos --output ./out --dpi 300
  python photo_layout.py --mode letter  --input ./photos --output ./out --cols 3 --rows 4
"""

import argparse
import os
import sys
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Pillow is required. Install with:  pip install Pillow")
    sys.exit(1)

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    _HEIF_AVAILABLE = True
except ImportError:
    _HEIF_AVAILABLE = False

# ── constants ────────────────────────────────────────────────────────────────

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp",
                  ".heic", ".heif"}   # iPhone formats require pillow-heif

# physical dimensions in inches
PHOTO_W_IN  = 2.0
PHOTO_H_IN  = 3.0
SHEET_4X6_W = 4.0
SHEET_4X6_H = 6.0
LETTER_W    = 8.5
LETTER_H    = 11.0

DEFAULT_DPI  = 300
DEFAULT_COLS = 4
DEFAULT_ROWS = 3
MARGIN_IN    = 0.125   # 1/8 inch margin between photos and edges


# ── core helpers ─────────────────────────────────────────────────────────────

def inches_to_px(inches, dpi):
    return int(round(inches * dpi))


def open_image(path: Path) -> Image.Image | None:
    """Open an image, applying EXIF rotation correction. Returns None on failure."""
    try:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)   # fix phone portrait rotation
        return img.convert("RGB")
    except Exception as e:
        print(f"  WARNING: skipping {path.name} — {e}", file=sys.stderr)
        return None


def fit_and_pad(img: Image.Image, target_w_px: int, target_h_px: int) -> Image.Image:
    """Scale image to fill target box (maintain aspect ratio), then pad with white."""
    src_w, src_h = img.size
    ratio  = min(target_w_px / src_w, target_h_px / src_h)
    new_w  = int(round(src_w * ratio))
    new_h  = int(round(src_h * ratio))
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGB", (target_w_px, target_h_px), (255, 255, 255))
    x_off  = (target_w_px - new_w) // 2
    y_off  = (target_h_px - new_h) // 2
    canvas.paste(resized, (x_off, y_off))
    return canvas


def list_images(folder: str) -> list[Path]:
    """Return image files in folder (non-recursive, sorted)."""
    p = Path(folder)
    return sorted(
        f for f in p.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS
    )


# ── mode: 4x6 (two 2x3 side-by-side) ────────────────────────────────────────

def make_4x6(img_path: Path, out_dir: Path, dpi: int) -> Path | None:
    """Place one photo twice side-by-side on a 4x6 sheet. Returns output path or None on error."""
    img = open_image(img_path)
    if img is None:
        return None

    sheet_w = inches_to_px(SHEET_4X6_W, dpi)
    sheet_h = inches_to_px(SHEET_4X6_H, dpi)
    margin  = inches_to_px(MARGIN_IN, dpi)

    # two cells side-by-side with left / middle / right margins
    cell_w  = (sheet_w - 3 * margin) // 2
    cell_h  = sheet_h - 2 * margin

    cell   = fit_and_pad(img, cell_w, cell_h)
    sheet  = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
    sheet.paste(cell, (margin, margin))
    sheet.paste(cell, (margin + cell_w + margin, margin))

    out_path = out_dir / (img_path.stem + "_4x6.jpg")
    sheet.save(out_path, "JPEG", quality=95, dpi=(dpi, dpi))
    return out_path


def process_4x6(input_folder: str, output_folder: str, dpi: int,
                progress_cb=None) -> tuple[int, int]:
    """Returns (processed, skipped)."""
    images = list_images(input_folder)
    if not images:
        return 0, 0

    out_dir = Path(output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)

    processed, skipped = 0, 0
    for i, img_path in enumerate(images):
        result = make_4x6(img_path, out_dir, dpi)
        if result:
            processed += 1
        else:
            skipped += 1
        if progress_cb:
            progress_cb(i + 1, len(images), img_path.name)

    return processed, skipped


# ── mode: letter (tile 2x3 photos on 8.5×11) ─────────────────────────────────

def process_letter(input_folder: str, output_folder: str, dpi: int,
                   cols: int, rows: int,
                   progress_cb=None) -> tuple[int, int]:
    """Returns (sheets_written, skipped_images)."""
    images = list_images(input_folder)
    if not images:
        return 0, 0

    out_dir = Path(output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)

    sheet_w_px = inches_to_px(LETTER_W, dpi)
    sheet_h_px = inches_to_px(LETTER_H, dpi)
    margin_px  = inches_to_px(MARGIN_IN, dpi)

    cell_w = (sheet_w_px - (cols + 1) * margin_px) // cols
    cell_h = (sheet_h_px - (rows + 1) * margin_px) // rows

    per_sheet = cols * rows
    total     = len(images)
    n_sheets  = math.ceil(total / per_sheet)

    done, skipped, sheet_count = 0, 0, 0

    for sheet_idx in range(n_sheets):
        sheet = Image.new("RGB", (sheet_w_px, sheet_h_px), (255, 255, 255))
        batch = images[sheet_idx * per_sheet : (sheet_idx + 1) * per_sheet]
        sheet_has_content = False

        for slot, img_path in enumerate(batch):
            img = open_image(img_path)
            done += 1
            if progress_cb:
                progress_cb(done, total, img_path.name)
            if img is None:
                skipped += 1
                continue

            row  = slot // cols
            col  = slot % cols
            x    = margin_px + col * (cell_w + margin_px)
            y    = margin_px + row * (cell_h + margin_px)
            cell = fit_and_pad(img, cell_w, cell_h)
            sheet.paste(cell, (x, y))
            sheet_has_content = True

        if sheet_has_content:
            out_path = out_dir / f"sheet_{sheet_count + 1:03d}.jpg"
            sheet.save(out_path, "JPEG", quality=95, dpi=(dpi, dpi))
            sheet_count += 1

    return sheet_count, skipped


# ── GUI ──────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Photo Layout Tool")
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        pad = dict(padx=8, pady=4)

        # ── mode ──
        mode_frame = ttk.LabelFrame(self, text="Mode")
        mode_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 4))
        self.mode_var = tk.StringVar(value="letter")
        ttk.Radiobutton(mode_frame, text="Letter sheet  (tile 2×3 photos on 8.5×11)",
                        variable=self.mode_var, value="letter",
                        command=self._toggle_mode).pack(anchor="w", padx=6, pady=2)
        ttk.Radiobutton(mode_frame, text="4×6 print  (two 2×3 side-by-side)",
                        variable=self.mode_var, value="4x6",
                        command=self._toggle_mode).pack(anchor="w", padx=6, pady=2)

        # ── folders ──
        ttk.Label(self, text="Input folder:").grid(row=1, column=0, sticky="e", **pad)
        self.input_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.input_var, width=42).grid(row=1, column=1, **pad)
        ttk.Button(self, text="Browse…", command=self._pick_input).grid(row=1, column=2, **pad)

        ttk.Label(self, text="Output folder:").grid(row=2, column=0, sticky="e", **pad)
        self.output_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.output_var, width=42).grid(row=2, column=1, **pad)
        ttk.Button(self, text="Browse…", command=self._pick_output).grid(row=2, column=2, **pad)

        # ── options ──
        opts_frame = ttk.LabelFrame(self, text="Options")
        opts_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=4)

        ttk.Label(opts_frame, text="DPI:").grid(row=0, column=0, sticky="e", **pad)
        self.dpi_var = tk.IntVar(value=DEFAULT_DPI)
        ttk.Spinbox(opts_frame, from_=72, to=600, textvariable=self.dpi_var,
                    width=6).grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(opts_frame, text="Columns:").grid(row=0, column=2, sticky="e", **pad)
        self.cols_var = tk.IntVar(value=DEFAULT_COLS)
        self.cols_spin = ttk.Spinbox(opts_frame, from_=1, to=8, textvariable=self.cols_var,
                                     width=4)
        self.cols_spin.grid(row=0, column=3, sticky="w", **pad)

        ttk.Label(opts_frame, text="Rows:").grid(row=0, column=4, sticky="e", **pad)
        self.rows_var = tk.IntVar(value=DEFAULT_ROWS)
        self.rows_spin = ttk.Spinbox(opts_frame, from_=1, to=10, textvariable=self.rows_var,
                                     width=4)
        self.rows_spin.grid(row=0, column=5, sticky="w", **pad)

        # ── heif notice ──
        heif_text = "✓ HEIC/HEIF supported" if _HEIF_AVAILABLE else "⚠ HEIC not available (pip install pillow-heif)"
        heif_color = "green" if _HEIF_AVAILABLE else "orange"
        ttk.Label(self, text=heif_text, foreground=heif_color).grid(
            row=4, column=0, columnspan=3, padx=10, pady=(2, 0))

        # ── progress ──
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var,
                                            maximum=100, length=420)
        self.progress_bar.grid(row=5, column=0, columnspan=3, padx=10, pady=(6, 2))

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status_var, foreground="gray").grid(
            row=6, column=0, columnspan=3, padx=10, pady=(0, 4))

        # ── run ──
        self.run_btn = ttk.Button(self, text="▶  Run", command=self._run, width=14)
        self.run_btn.grid(row=7, column=0, columnspan=3, pady=(4, 10))

        self._toggle_mode()

    def _toggle_mode(self):
        state = "normal" if self.mode_var.get() == "letter" else "disabled"
        self.cols_spin.config(state=state)
        self.rows_spin.config(state=state)

    def _pick_input(self):
        d = filedialog.askdirectory(title="Select input folder")
        if d:
            self.input_var.set(d)

    def _pick_output(self):
        d = filedialog.askdirectory(title="Select output folder")
        if d:
            self.output_var.set(d)

    def _run(self):
        inp = self.input_var.get().strip()
        out = self.output_var.get().strip()
        if not inp or not out:
            messagebox.showerror("Missing folders", "Please set both input and output folders.")
            return
        if not os.path.isdir(inp):
            messagebox.showerror("Bad folder", f"Input folder not found:\n{inp}")
            return

        self.run_btn.config(state="disabled")
        self.progress_var.set(0)
        self.status_var.set("Starting…")
        self.update()

        dpi  = self.dpi_var.get()
        mode = self.mode_var.get()

        def cb(done, total, name):
            pct = done / total * 100
            self.progress_var.set(pct)
            self.status_var.set(f"[{done}/{total}]  {name}")
            self.update()

        try:
            if mode == "4x6":
                processed, skipped = process_4x6(inp, out, dpi, progress_cb=cb)
                msg = f"Done!\n\n{processed} file(s) created in:\n{out}"
                if skipped:
                    msg += f"\n\n{skipped} file(s) skipped (unreadable or unsupported)."
            else:
                cols = self.cols_var.get()
                rows = self.rows_var.get()
                sheets, skipped = process_letter(inp, out, dpi, cols, rows, progress_cb=cb)
                msg = f"Done!\n\n{sheets} sheet(s) created in:\n{out}"
                if skipped:
                    msg += f"\n\n{skipped} file(s) skipped (unreadable or unsupported)."
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            self.run_btn.config(state="normal")
            self.status_var.set("Error — see dialog.")
            return

        self.progress_var.set(100)
        self.status_var.set("Complete.")
        self.run_btn.config(state="normal")
        messagebox.showinfo("Done", msg)


# ── CLI ───────────────────────────────────────────────────────────────────────

def cli():
    parser = argparse.ArgumentParser(
        description="Batch photo layout tool: 4×6 or letter-sheet tiling.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--mode",   choices=["4x6", "letter"],
                        help="Layout mode (required for headless run)")
    parser.add_argument("--input",  metavar="DIR",
                        help="Input folder (images only, no subfolders)")
    parser.add_argument("--output", metavar="DIR", help="Output folder")
    parser.add_argument("--dpi",    type=int, default=DEFAULT_DPI,
                        help=f"Output DPI (default {DEFAULT_DPI})")
    parser.add_argument("--cols",   type=int, default=DEFAULT_COLS,
                        help=f"Columns on letter sheet (default {DEFAULT_COLS})")
    parser.add_argument("--rows",   type=int, default=DEFAULT_ROWS,
                        help=f"Rows on letter sheet (default {DEFAULT_ROWS})")
    args = parser.parse_args()

    # if any required arg is missing, launch GUI instead
    if not args.mode or not args.input or not args.output:
        app = App()
        if args.input:  app.input_var.set(args.input)
        if args.output: app.output_var.set(args.output)
        if args.mode:
            app.mode_var.set(args.mode)
            app._toggle_mode()
        app.dpi_var.set(args.dpi)
        app.cols_var.set(args.cols)
        app.rows_var.set(args.rows)
        app.mainloop()
        return

    if not _HEIF_AVAILABLE:
        print("NOTE: pillow-heif not installed — HEIC/HEIF files will be skipped.")

    def cb(done, total, name):
        pct = int(done / total * 100)
        bar = "#" * (pct // 2) + "-" * (50 - pct // 2)
        print(f"\r[{bar}] {pct:3d}%  {name[:30]:<30}", end="", flush=True)

    print(f"Mode: {args.mode}  |  DPI: {args.dpi}  |  Input: {args.input}")

    if args.mode == "4x6":
        processed, skipped = process_4x6(args.input, args.output, args.dpi, progress_cb=cb)
        print(f"\nDone — {processed} file(s) written to {args.output}")
        if skipped:
            print(f"Skipped {skipped} unreadable/unsupported file(s).")
    else:
        sheets, skipped = process_letter(args.input, args.output, args.dpi,
                                         args.cols, args.rows, progress_cb=cb)
        print(f"\nDone — {sheets} sheet(s) written to {args.output}")
        if skipped:
            print(f"Skipped {skipped} unreadable/unsupported file(s).")


if __name__ == "__main__":
    cli()
