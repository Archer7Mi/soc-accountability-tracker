from typing import Iterable


def daily_score(
    sc200_modules: int,
    labs_completed: int,
    commits_pushed: int,
    planned_minutes: int,
    completed_minutes: int,
    quality_artifacts_count: int,
) -> int:
    # Output is weighted toward quality artifacts, not raw activity volume.
    output_score = min(40, (labs_completed * 8) + (quality_artifacts_count * 12))
    if quality_artifacts_count == 0:
        output_score = min(output_score, 8)

    focus_ratio = 0.0
    if planned_minutes > 0:
        focus_ratio = completed_minutes / planned_minutes
    focus_base = int(min(30, max(0.0, focus_ratio * 30)))

    mismatch_ratio = 0.0
    if planned_minutes > 0:
        mismatch_ratio = abs(completed_minutes - planned_minutes) / planned_minutes
    elif completed_minutes > 0:
        mismatch_ratio = 1.0
    mismatch_penalty = int(min(12, mismatch_ratio * 12))
    focus_score = max(0, focus_base - mismatch_penalty)

    consistency_score = min(20, commits_pushed * 4)
    review_score = 10 if sc200_modules > 0 else 0

    total = output_score + focus_score + consistency_score + review_score
    return min(100, max(0, total))


def week_health(daily_scores: Iterable[int]) -> str:
    scores = list(daily_scores)
    if not scores:
        return "No data"
    avg = sum(scores) / len(scores)
    if avg >= 75:
        return "GREEN"
    if avg >= 55:
        return "AMBER"
    return "RED"
