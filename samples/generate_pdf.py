"""
Convert a text file to PDF. Requires: pip install fpdf2

Usage:
    python samples/generate_pdf.py meeting3.txt
    python samples/generate_pdf.py notes.txt --output custom.pdf
"""
import click
from fpdf import FPDF
from pathlib import Path


_UNICODE_MAP = str.maketrans({
    "—": "--", "–": "-",
    "‘": "'", "’": "'",
    "“": '"', "”": '"',
    "…": "...",
})


def txt_to_pdf(input_path: Path, output_path: Path):
    text = (
        input_path.read_text(encoding="utf-8")
        .translate(_UNICODE_MAP)
        .encode("latin-1", errors="ignore")
        .decode("latin-1")
    )
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.set_auto_page_break(auto=True, margin=15)
    width = pdf.w - pdf.l_margin - pdf.r_margin
    for line in text.splitlines():
        pdf.multi_cell(width, 6, line if line.strip() else "")
    pdf.output(str(output_path))
    click.echo(f"Created: {output_path}")


@click.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--output", "-o", type=click.Path(dir_okay=False, path_type=Path), default=None,
              help="Output PDF path. Defaults to same name as input with .pdf extension.")
def main(input_file: Path, output: Path | None):
    output_path = output or input_file.with_suffix(".pdf")
    txt_to_pdf(input_file, output_path)


if __name__ == "__main__":
    main()
