Setup (WSL):
pip install Pillow
python photo_layout.py          # opens the GUI

What it does:
4×6 mode — for each image in the folder, produces one 4×6 JPG with the same photo placed twice side-by-side as two 2×3 prints. Any aspect ratio mismatch is handled by fit-and-pad (scales to fill, adds white margins).


Letter mode — collects all images and tiles them as 2×3 photos on 8.5×11 sheets. Default grid is 4 columns × 3 rows = 12 photos per sheet. Extra photos spill onto additional sheets.


CLI examples:

# 4x6 mode headless
python photo_layout.py --mode 4x6 --input ./photos --output ./out

# Letter mode, custom grid, 300 DPI
python photo_layout.py --mode letter --input ./photos --output ./out --cols 4 --rows 3 --dpi 300

# Partially fill args → GUI opens with those fields pre-filled
python photo_layout.py --input ./photos


GUI features: folder pickers, DPI spinner, cols/rows spinners (disabled in 4×6 mode), live progress bar, status line showing current file.Photo layout


