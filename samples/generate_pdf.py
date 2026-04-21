"""
Run this once to generate meeting3.pdf from meeting3.txt.
Requires: pip install fpdf2
"""
from fpdf import FPDF
from pathlib import Path


def txt_to_pdf(input_path: str, output_path: str):
    text = Path(input_path).read_text(encoding="utf-8")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.set_auto_page_break(auto=True, margin=15)
    for line in text.splitlines():
        pdf.multi_cell(0, 6, line if line.strip() else "")
    pdf.output(output_path)
    print(f"Created: {output_path}")


if __name__ == "__main__":
    base = Path(__file__).parent
    txt_to_pdf(str(base / "meeting3.txt"), str(base / "meeting3.pdf"))
