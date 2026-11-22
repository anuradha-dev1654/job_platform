
import re


def parse_resume(raw_text: str) -> dict:
    """
    Clean extracted resume text and return structured basic information.
    """

    if not raw_text or not raw_text.strip():
        raise ValueError("Resume text cannot be empty.")

    # Remove extra spaces and tabs
    cleaned_text = re.sub(r"[ \t]+", " ", raw_text)

    # Normalize multiple blank lines
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

    # Clean text
    cleaned_text = cleaned_text.strip()

    # Extract email
    email_match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        cleaned_text
    )

    # Extract phone number (basic international/Indian format)
    phone_match = re.search(
        r"(?<!\w)(?:\+?\d{1,3}[-.\s]?)?\d{10}(?!\w)",
        cleaned_text
    )

    return {
        "cleaned_text": cleaned_text,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
    }
