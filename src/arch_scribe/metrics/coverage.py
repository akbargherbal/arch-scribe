def calculate_coverage_quality(sig_paths, mapped):
    """Coverage quality: what % of significant files are mapped?

    Args:
        sig_paths (set): Set of significant file paths from scan
        mapped (set): Set of files mapped to systems

    Returns:
        float: Percentage (0.0-100.0) of significant files that are mapped
    """
    if not sig_paths:
        return 0.0

    # Only count files that exist in BOTH sets
    mapped_sig = sig_paths.intersection(mapped)
    return round(len(mapped_sig) / len(sig_paths) * 100, 1)