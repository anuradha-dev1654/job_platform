def score(checks: dict) -> int:
    """Weighted score 0-100."""
    weights = {"domain_match": 40, "reachable": 20, "ssl": 15, "domain_age": 25}
    return sum(w for k, w in weights.items() if checks.get(k))
