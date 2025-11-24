def compute_clarity(sys):
    """Auto-compute clarity from objective rubric

    HIGH CLARITY:
    - 5+ insights recorded
    - 70%+ completeness (base)
    - Has dependencies

    MEDIUM CLARITY:
    - 3-4 insights recorded
    - 40-69% completeness (base)

    LOW CLARITY:
    - 0-2 insights recorded
    - <40% completeness (base)
    """
    insight_count = len(sys.get("insights", []))
    has_deps = len(sys.get("dependencies", [])) > 0

    # Calculate BASE completeness (without clarity bonus)
    file_count = len(sys.get("key_files", []))
    file_score = min(file_count / 10.0, 1.0) * 40
    insight_score = min(insight_count / 5.0, 1.0) * 35
    dep_score = 15 if has_deps else 0
    base_completeness = int(file_score + insight_score + dep_score)

    if insight_count >= 5 and base_completeness >= 70 and has_deps:
        return "high"

    if insight_count >= 3 and base_completeness >= 40:
        return "medium"

    return "low"