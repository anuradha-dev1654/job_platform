from typing import TypedDict, Optional


class CheckState(TypedDict, total=False):
    candidate_id: int
    github_username: Optional[str]
    linkedin_pdf_path: Optional[str]
    github_data: dict
    linkedin_data: dict
    report: str
