def compute_completeness(sys):
    """Calculate completeness from objective metrics

    Formula (100 points total):
    - File coverage: up to 40 points
    - Insight depth: up to 35 points
    - Dependency mapping: 15 points
    - Clarity bonus: up to 10 points
    """
    # 1. File coverage (40 points max)
    file_count = len(sys.get("key_files", []))
    file_score = min(file_count / 10.0, 1.0) * 40

    # 2. Insight depth (35 points max)
    insight_count = len(sys.get("insights", []))
    insight_score = min(insight_count / 5.0, 1.0) * 35

    # 3. Dependency mapping (15 points)
    has_deps = len(sys.get("dependencies", [])) > 0
    dep_score = 15 if has_deps else 0

    # 4. Clarity bonus (10 points)
    clarity = sys.get("clarity", "low")
    clarity_map = {"high": 10, "medium": 5, "low": 0}
    clarity_score = clarity_map.get(clarity, 0)

    # Total score (capped at 100)
    total = file_score + insight_score + dep_score + clarity_score
    return int(min(total, 100))