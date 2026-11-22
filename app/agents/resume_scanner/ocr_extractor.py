
import pymupdf


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a text-based PDF resume.
    """

    try:
        document = pymupdf.open(pdf_path)

        if document.is_encrypted:
            raise ValueError("Password-protected PDFs are not supported.")

        extracted_pages = []

        for page in document:
            page_text = page.get_text()
            if page_text.strip():
                extracted_pages.append(page_text)

        document.close()

        extracted_text = "\n".join(extracted_pages).strip()

        if not extracted_text:
            raise ValueError(
                "No readable text found. This may be a scanned PDF."
            )

        return extracted_text

    except ValueError:
        raise

    except Exception as error:
        raise RuntimeError(
            f"Could not read PDF: {error}"
        ) from error
