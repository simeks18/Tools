
import pikepdf
import argparse
import getpass
from pathlib import Path


def unlock_pdf(input_file, output_file):
    try:
        pdf = pikepdf.open(input_file)

    except pikepdf.PasswordError:
        password = getpass.getpass("Enter PDF password: ")
        pdf = pikepdf.open(input_file, password=password)

    with pdf:
        print(f"Encrypted: {pdf.is_encrypted}")
        print(f"Printing allowed: {pdf.allow.print_highres}")
        print(f"Pages: {len(pdf.pages)}")

        pdf.save(output_file, encryption=False)

    with pikepdf.open(output_file) as verified:
        print("\nVerification:")
        print(f"Encrypted: {verified.is_encrypted}")
        print(f"Printing allowed: {verified.allow.print_highres}")

    print(f"\nUnlocked PDF saved to: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Remove PDF printing restrictions."
    )

    parser.add_argument("input", help="Input PDF file")
    parser.add_argument("-o", "--output", help="Output PDF file")

    args = parser.parse_args()

    source = Path(args.input)

    destination = Path(args.output) if args.output else (
        source.with_name(source.stem + "_unlocked.pdf")
    )

    if source.resolve() == destination.resolve():
        parser.error("Output must differ from input.")

    try:
        unlock_pdf(source, destination)
    except Exception as error:
        print(f"Error: {error}")
        raise SystemExit(1)
