import pypdf


def parse(file_path: str) -> str:
    """Extract text from a PDF file and return it as a string."""
    try:
        reader = pypdf.PdfReader(file_path)

        if reader.is_encrypted:
            raise ValueError(f"PDF is password-protected and cannot be read: {file_path}")

        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())

        if not pages:
            raise ValueError(f"No text could be extracted from PDF: {file_path}")

        return "\n\n".join(pages)

    except pypdf.errors.PdfReadError as e:
        raise ValueError(f"Could not read PDF (possibly corrupted): {file_path}\n{e}")
