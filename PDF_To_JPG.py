#!/usr/bin/env python3
"""
PDF to JPG Converter
Converts each page of a PDF into a separate JPG image.

Requirements (install once):
    sudo apt update && sudo apt install -y poppler-utils
    pip install pdf2image Pillow

Usage:
    python pdf_to_jpg.py input.pdf
    python pdf_to_jpg.py input.pdf --dpi 300
    python pdf_to_jpg.py input.pdf --output ./my_output_folder
    python pdf_to_jpg.py input.pdf --quality 95 --dpi 200
"""

import argparse
import sys
from pathlib import Path


def check_dependencies():
    """Check that required libraries are installed."""
    try:
        from pdf2image import convert_from_path  # noqa: F401
    except ImportError:
        print("ERROR: pdf2image is not installed.")
        print("  Run: pip install pdf2image Pillow")
        sys.exit(1)

    try:
        import PIL  # noqa: F401
    except ImportError:
        print("ERROR: Pillow is not installed.")
        print("  Run: pip install Pillow")
        sys.exit(1)

    # Check poppler is available (required by pdf2image)
    import shutil
    if not shutil.which("pdftoppm"):
        print("ERROR: poppler-utils is not installed.")
        print("  Run: sudo apt update && sudo apt install -y poppler-utils")
        sys.exit(1)


def convert_pdf_to_jpg(pdf_path: str, output_dir: str = None, dpi: int = 150, quality: int = 90):
    """
    Convert a PDF file to JPG images, one per page.

    Args:
        pdf_path:   Path to the input PDF file.
        output_dir: Directory to save JPGs (defaults to same dir as PDF).
        dpi:        Resolution in dots per inch (higher = sharper but larger files).
        quality:    JPG compression quality 1-95 (higher = better quality, larger files).
    """
    from pdf2image import convert_from_path

    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    if pdf_path.suffix.lower() != ".pdf":
        print(f"ERROR: Input file must be a .pdf (got: {pdf_path.suffix})")
        sys.exit(1)

    # Determine output directory
    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = pdf_path.parent / pdf_path.stem

    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Converting: {pdf_path.name}")
    print(f"Output dir: {out_dir}")
    print(f"DPI: {dpi}  |  JPG quality: {quality}")
    print()

    # Convert PDF pages to PIL images
    try:
        pages = convert_from_path(str(pdf_path), dpi=dpi)
    except Exception as e:
        print(f"ERROR during conversion: {e}")
        sys.exit(1)

    total = len(pages)
    pad = len(str(total))  # zero-pad width based on page count

    saved = []
    for i, page in enumerate(pages, start=1):
        filename = f"{pdf_path.stem}_page_{str(i).zfill(pad)}.jpg"
        out_path = out_dir / filename

        # Convert to RGB (PDFs can be RGBA/palette; JPG requires RGB)
        rgb_page = page.convert("RGB")
        rgb_page.save(str(out_path), "JPEG", quality=quality, optimize=True)

        size_kb = out_path.stat().st_size // 1024
        print(f"  [{i}/{total}] {filename}  ({size_kb} KB)")
        saved.append(out_path)

    print()
    print(f"Done! {total} page(s) saved to: {out_dir}")
    return saved


def main():
    parser = argparse.ArgumentParser(
        description="Convert a PDF to JPG images (one per page).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_to_jpg.py document.pdf
  python pdf_to_jpg.py document.pdf --dpi 300
  python pdf_to_jpg.py document.pdf --output ./images --quality 95
        """,
    )
    parser.add_argument("pdf", help="Path to the input PDF file")
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory (default: a folder named after the PDF)",
    )
    parser.add_argument(
        "--dpi", "-d",
        type=int,
        default=150,
        help="Resolution in DPI (default: 150; use 300 for print quality)",
    )
    parser.add_argument(
        "--quality", "-q",
        type=int,
        default=90,
        choices=range(1, 96),
        metavar="1-95",
        help="JPG quality 1-95 (default: 90)",
    )

    args = parser.parse_args()

    check_dependencies()
    convert_pdf_to_jpg(
        pdf_path=args.pdf,
        output_dir=args.output,
        dpi=args.dpi,
        quality=args.quality,
    )


if __name__ == "__main__":
    main()
