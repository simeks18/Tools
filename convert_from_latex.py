# Convert current directory (all .tex found recursively)
## python3 latex_to_notepad.py

# Specify a source folder
## python3 latex_to_notepad.py /home/user/my_latex_papers

# Specify source AND output folder
## python3 latex_to_notepad.py /home/user/papers /home/user/txt_output

# Quiet mode (no per-file output)
## python3 latex_to_notepad.py /home/user/papers --quiet


#!/usr/bin/env python3
"""
LaTeX to Plain Text Converter
Converts all .tex files in subdirectories to .txt files
Usage: python3 latex_to_notepad.py [source_dir] [output_dir]
"""

import os
import re
import sys
import argparse
from pathlib import Path


# ─────────────────────────────────────────────
#  LaTeX Cleaner
# ─────────────────────────────────────────────

def clean_latex(text: str) -> str:
    """Strip LaTeX markup and return readable plain text."""

    # ── Remove comments ──────────────────────
    text = re.sub(r'%.*', '', text)

    # ── Document structure tags ───────────────
    text = re.sub(r'\\documentclass\[?.*?\]?\{.*?\}', '', text)
    text = re.sub(r'\\usepackage\[?.*?\]?\{.*?\}', '', text)
    text = re.sub(r'\\begin\{document\}', '', text)
    text = re.sub(r'\\end\{document\}',   '', text)

    # ── Title / author / date ─────────────────
    text = re.sub(r'\\title\{(.*?)\}',  r'TITLE: \1',  text, flags=re.DOTALL)
    text = re.sub(r'\\author\{(.*?)\}', r'AUTHOR: \1', text, flags=re.DOTALL)
    text = re.sub(r'\\date\{(.*?)\}',   r'DATE: \1',   text, flags=re.DOTALL)
    text = re.sub(r'\\maketitle', '', text)

    # ── Section headings ─────────────────────
    text = re.sub(r'\\part\*?\{(.*?)\}',          r'\n\n═══ PART: \1 ═══\n',        text, flags=re.DOTALL)
    text = re.sub(r'\\chapter\*?\{(.*?)\}',       r'\n\n══ CHAPTER: \1 ══\n',       text, flags=re.DOTALL)
    text = re.sub(r'\\section\*?\{(.*?)\}',       r'\n\n── SECTION: \1 ──\n',       text, flags=re.DOTALL)
    text = re.sub(r'\\subsection\*?\{(.*?)\}',    r'\n  ── Subsection: \1 ──\n',    text, flags=re.DOTALL)
    text = re.sub(r'\\subsubsection\*?\{(.*?)\}', r'\n    ── Subsubsection: \1 ──\n', text, flags=re.DOTALL)
    text = re.sub(r'\\paragraph\*?\{(.*?)\}',     r'\n    Paragraph: \1\n',         text, flags=re.DOTALL)

    # ── Text formatting ───────────────────────
    text = re.sub(r'\\textbf\{(.*?)\}',   r'**\1**',  text, flags=re.DOTALL)
    text = re.sub(r'\\textit\{(.*?)\}',   r'_\1_',    text, flags=re.DOTALL)
    text = re.sub(r'\\emph\{(.*?)\}',     r'_\1_',    text, flags=re.DOTALL)
    text = re.sub(r'\\underline\{(.*?)\}',r'_\1_',    text, flags=re.DOTALL)
    text = re.sub(r'\\texttt\{(.*?)\}',   r'`\1`',    text, flags=re.DOTALL)
    text = re.sub(r'\\textrm\{(.*?)\}',   r'\1',      text, flags=re.DOTALL)
    text = re.sub(r'\\textsc\{(.*?)\}',   r'\1',      text, flags=re.DOTALL)

    # ── Lists ─────────────────────────────────
    text = re.sub(r'\\begin\{itemize\}',   '\n',  text)
    text = re.sub(r'\\end\{itemize\}',     '\n',  text)
    text = re.sub(r'\\begin\{enumerate\}', '\n',  text)
    text = re.sub(r'\\end\{enumerate\}',   '\n',  text)
    text = re.sub(r'\\item\[(.*?)\]',      r'  • \1 ', text)
    text = re.sub(r'\\item',               '  • ', text)

    # ── Math environments → placeholder ──────
    text = re.sub(r'\$\$(.*?)\$\$', r' [MATH: \1] ', text, flags=re.DOTALL)
    text = re.sub(r'\$(.*?)\$',     r' [math: \1] ', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}',
                  r'\n[EQUATION: \1]\n', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}',
                  r'\n[ALIGN: \1]\n',    text, flags=re.DOTALL)

    # ── Tables → placeholder ──────────────────
    text = re.sub(r'\\begin\{tabular\}.*?\\end\{tabular\}',
                  '\n[TABLE]\n', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{table\}.*?\\end\{table\}',
                  '\n[TABLE FLOAT]\n', text, flags=re.DOTALL)

    # ── Figures → placeholder ─────────────────
    text = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}',
                  '\n[FIGURE]\n', text, flags=re.DOTALL)
    text = re.sub(r'\\includegraphics\[?.*?\]?\{(.*?)\}',
                  r'\n[IMAGE: \1]\n', text)

    # ── References / citations ────────────────
    text = re.sub(r'\\cite\{(.*?)\}',    r'[cite: \1]',  text)
    text = re.sub(r'\\ref\{(.*?)\}',     r'[ref: \1]',   text)
    text = re.sub(r'\\label\{(.*?)\}',   r'',            text)
    text = re.sub(r'\\footnote\{(.*?)\}',r' (footnote: \1)', text, flags=re.DOTALL)

    # ── Spacing / layout commands ─────────────
    text = re.sub(r'\\(newline|linebreak|break)', '\n',   text)
    text = re.sub(r'\\\\',                         '\n',   text)
    text = re.sub(r'\\newpage',                    '\n\n' + '─'*60 + '\n\n', text)
    text = re.sub(r'\\clearpage',                  '\n\n' + '─'*60 + '\n\n', text)
    text = re.sub(r'\\hline',                      '─'*40, text)
    text = re.sub(r'\\(vspace|hspace)\*?\{.*?\}',  '',     text)
    text = re.sub(r'\\(bigskip|medskip|smallskip)','\n',   text)
    text = re.sub(r'\\noindent',                   '',     text)
    text = re.sub(r'\\indent',                     '    ', text)

    # ── Special characters ────────────────────
    text = text.replace(r'\&',  '&')
    text = text.replace(r'\%',  '%')
    text = text.replace(r'\$',  '$')
    text = text.replace(r'\#',  '#')
    text = text.replace(r'\_',  '_')
    text = text.replace(r'\{',  '{')
    text = text.replace(r'\}',  '}')
    text = text.replace(r'\~',  '~')
    text = text.replace(r'\^',  '^')
    text = text.replace(r'``',  '"')
    text = text.replace(r"''",  '"')
    text = text.replace(r'`',   "'")
    text = text.replace(r'---', '—')
    text = text.replace(r'--',  '–')

    # ── Remove remaining LaTeX commands ───────
    text = re.sub(r'\\[a-zA-Z]+\*?\{(.*?)\}', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'\\[a-zA-Z]+\*?',           '',    text)
    text = re.sub(r'\{|\}',                     '',    text)

    # ── Clean up whitespace ───────────────────
    text = re.sub(r'\n{3,}', '\n\n', text)         # max 2 blank lines
    text = re.sub(r'[ \t]+',  ' ',   text)         # collapse spaces
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    text = text.strip()

    return text


# ─────────────────────────────────────────────
#  File / Directory Helpers
# ─────────────────────────────────────────────

def find_tex_files(source_dir: Path) -> list[Path]:
    """Recursively find all .tex files under source_dir."""
    return sorted(source_dir.rglob('*.tex'))


def convert_file(tex_path: Path, output_dir: Path, source_dir: Path,
                 verbose: bool = True) -> bool:
    """
    Convert one .tex file to .txt.
    Mirrors the subdirectory structure inside output_dir.
    Returns True on success.
    """
    try:
        # ── Preserve relative folder structure ──
        relative   = tex_path.relative_to(source_dir)
        out_path   = output_dir / relative.with_suffix('.txt')
        out_path.parent.mkdir(parents=True, exist_ok=True)

        raw_text   = tex_path.read_text(encoding='utf-8', errors='replace')
        clean_text = clean_latex(raw_text)

        out_path.write_text(clean_text, encoding='utf-8')

        if verbose:
            print(f'  ✔  {relative}  →  {out_path.relative_to(output_dir)}')
        return True

    except Exception as exc:
        print(f'  ✘  {tex_path.name}  →  ERROR: {exc}')
        return False


def print_summary(converted: int, failed: int, output_dir: Path) -> None:
    width = 50
    print('\n' + '═' * width)
    print(f'  Converted : {converted}')
    print(f'  Failed    : {failed}')
    print(f'  Output    : {output_dir}')
    print('═' * width)


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Convert LaTeX (.tex) files to plain text (.txt) — WSL friendly',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 latex_to_notepad.py
  python3 latex_to_notepad.py /home/user/papers
  python3 latex_to_notepad.py /home/user/papers /home/user/output
  python3 latex_to_notepad.py . ./converted --quiet
        """
    )
    parser.add_argument('source_dir', nargs='?', default='.',
                        help='Root folder containing LaTeX subfolders (default: .)')
    parser.add_argument('output_dir', nargs='?', default='./converted_txt',
                        help='Where to save .txt files (default: ./converted_txt)')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress per-file output')
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    # ── Validate source ────────────────────────
    if not source_dir.exists():
        print(f'ERROR: Source directory not found: {source_dir}')
        sys.exit(1)

    print(f'\nLaTeX → Plain Text Converter')
    print(f'  Source : {source_dir}')
    print(f'  Output : {output_dir}')
    print('─' * 50)

    tex_files = find_tex_files(source_dir)

    if not tex_files:
        print('No .tex files found.')
        sys.exit(0)

    print(f'Found {len(tex_files)} .tex file(s)\n')

    output_dir.mkdir(parents=True, exist_ok=True)

    converted, failed = 0, 0
    for tex_file in tex_files:
        ok = convert_file(tex_file, output_dir, source_dir,
                          verbose=not args.quiet)
        if ok:
            converted += 1
        else:
            failed += 1

    print_summary(converted, failed, output_dir)


if __name__ == '__main__':
    main()
