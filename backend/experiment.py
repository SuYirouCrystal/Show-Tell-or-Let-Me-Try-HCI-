import random
import uuid
from typing import Any, Dict, List, Optional


def new_participant_id() -> str:
    return str(uuid.uuid4())


def new_response_id() -> str:
    return str(uuid.uuid4())


def assign_condition(conditions: List[str], requested_condition: Optional[str] = None) -> str:
    """Assign one between-subjects condition.

    requested_condition is only for local testing, for example /start?condition=show.
    In real data collection, do not share that URL with participants.
    """
    if requested_condition in conditions:
        return requested_condition
    return random.choice(conditions)


def assign_balanced_condition(
    conditions: List[str],
    observed_counts: Dict[str, int],
    requested_condition: Optional[str] = None,
) -> str:
    if requested_condition in conditions:
        return requested_condition

    min_count = min(observed_counts.get(condition, 0) for condition in conditions)
    eligible_conditions = [
        condition for condition in conditions
        if observed_counts.get(condition, 0) == min_count
    ]
    return random.choice(eligible_conditions)


def make_task_order(tasks: List[Dict[str, Any]], randomize: bool = True) -> List[str]:
    task_ids = [str(task["task_id"]) for task in tasks]
    if randomize:
        random.shuffle(task_ids)
    return task_ids


def public_task_payload(task: Dict[str, Any], condition: str) -> Dict[str, Any]:
    """Return only the data the participant should see.

    The backend keeps correct_answer and ai_is_correct hidden.
    """
    explanation = task.get("explanations", {})
    return {
        "task_id": task["task_id"],
        "title": task["title"],
        "scenario": task["scenario"],
        "decision_prompt": task["decision_prompt"],
        "options": task["options"],
        "ai_recommendation": task["ai_recommendation"],
        "condition": condition,
        "features": task["features"],
        "explanation": explanation.get(condition, {}),
    }


def _normalize_feature(values: List[float], direction: str) -> List[float]:
    min_value = min(values)
    max_value = max(values)
    if max_value == min_value:
        return [1.0 for _ in values]

    if direction == "lower":
        return [(max_value - value) / (max_value - min_value) for value in values]
    return [(value - min_value) / (max_value - min_value) for value in values]


def compute_weighted_scores(task: Dict[str, Any], weights: Dict[str, float]) -> Dict[str, Any]:
    """Compute a simple weighted score for the interactive condition.

    This is not a real AI model. It is a deterministic simulation for the HCI study.
    It lets users change feature importance and observe recommendation changes.
    """
    options = task["options"]
    features = task["features"]

    normalized_by_feature: Dict[str, List[float]] = {}
    for feature in features:
        feature_id = feature["id"]
        raw_values = [float(option["attributes"][feature_id]) for option in options]
        normalized_by_feature[feature_id] = _normalize_feature(raw_values, feature["direction"])

    total_weight = sum(max(float(weights.get(feature["id"], feature.get("default_weight", 0))), 0) for feature in features)
    if total_weight <= 0:
        total_weight = 1.0

    scores = []
    for option_index, option in enumerate(options):
        score = 0.0
        contributions = {}
        for feature in features:
            feature_id = feature["id"]
            raw_weight = max(float(weights.get(feature_id, feature.get("default_weight", 0))), 0)
            normalized_weight = raw_weight / total_weight
            contribution = normalized_weight * normalized_by_feature[feature_id][option_index]
            score += contribution
            contributions[feature_id] = round(contribution, 4)

        scores.append({
            "option_id": option["id"],
            "name": option["name"],
            "score": round(score, 4),
            "contributions": contributions,
        })

    scores.sort(key=lambda item: item["score"], reverse=True)
    return {
        "recommendation": scores[0]["option_id"],
        "recommendation_name": scores[0]["name"],
        "scores": scores,
    }


def evaluate_error_detection(task: Dict[str, Any], user_thinks_ai_correct: str) -> bool:
    ai_is_correct = bool(task["ai_is_correct"])
    normalized = str(user_thinks_ai_correct).strip().lower()
    user_answer = normalized in {"yes", "true", "correct", "1"}
    return user_answer == ai_is_correct
