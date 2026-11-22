import os
import uuid
from flask import current_app

# extension -> required first bytes of the file
ALLOWED = {
    ".pdf": b"%PDF",
    ".png": b"\x89PNG",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
}
MAX_FILE_BYTES = 5 * 1024 * 1024


def validate_upload(file):
    """Returns (ok, error). Checks extension, size and real file type (magic bytes)."""
    if not file or not file.filename:
        return False, "Upload this document."
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED:
        return False, "Only PDF, PNG or JPG files are allowed."
    head = file.stream.read(8)
    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if not head.startswith(ALLOWED[ext]):
        return False, "This file's content does not match its type."
    if size > MAX_FILE_BYTES:
        return False, "File must be 5 MB or smaller."
    return True, None


def save_company_doc(file, company_id):
    """Saves under uploads/company_docs/<company_id>/ with a random name. Returns relative path."""
    ext = os.path.splitext(file.filename)[1].lower()
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "company_docs", str(company_id))
    os.makedirs(folder, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    file.save(os.path.join(folder, name))
    return f"company_docs/{company_id}/{name}"


def save_candidate_file(file, candidate_id, kind):
    """Save a candidate photo or resume under uploads/candidates/<candidate_id>/."""
    ext = os.path.splitext(file.filename)[1].lower()
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "candidates", str(candidate_id))
    os.makedirs(folder, exist_ok=True)
    name = f"{kind}-{uuid.uuid4().hex}{ext}"
    file.save(os.path.join(folder, name))
    return f"candidates/{candidate_id}/{name}"


def save_company_logo(file, company_id):
    ext = os.path.splitext(file.filename)[1].lower()
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "company_logos", str(company_id))
    os.makedirs(folder, exist_ok=True)
    name = f"logo-{uuid.uuid4().hex}{ext}"
    file.save(os.path.join(folder, name))
    return f"company_logos/{company_id}/{name}"