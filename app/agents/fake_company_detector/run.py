from .scorer import score


def run(company: dict) -> int:
    checks = {}  # TODO: call domain_checker / website_checker
    return score(checks)
