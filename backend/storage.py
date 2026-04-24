import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


RESPONSE_FIELDS = [
    "response_id",
    "participant_id",
    "condition",
    "trial_index",
    "task_id",
    "selected_option",
    "correct_answer",
    "is_correct",
    "ai_recommendation",
    "ai_is_correct",
    "user_thinks_ai_correct",
    "error_detection_correct",
    "confidence_rating",
    "client_decision_ms",
    "server_decision_ms",
    "shown_at",
    "submitted_at",
    "user_agent",
]

SURVEY_FIELDS = [
    "survey_id",
    "participant_id",
    "condition",
    "perceived_understanding",
    "trust",
    "mental_demand",
    "effort",
    "frustration",
    "engagement",
    "feedback",
    "submitted_at",
    "user_agent",
]

PARTICIPANT_FIELDS = [
    "participant_id",
    "condition",
    "task_order",
    "started_at",
    "user_agent",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_csv(path: Path, fieldnames: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(fieldnames))
            writer.writeheader()


def ensure_storage_files(config: Dict[str, Any]) -> None:
    data_dir = Path(config["DATA_DIR"])
    data_dir.mkdir(parents=True, exist_ok=True)
    ensure_csv(Path(config["RESPONSES_FILE"]), RESPONSE_FIELDS)
    ensure_csv(Path(config["SURVEYS_FILE"]), SURVEY_FIELDS)
    ensure_csv(Path(config["PARTICIPANTS_FILE"]), PARTICIPANT_FIELDS)


def load_tasks(tasks_file: Path) -> List[Dict[str, Any]]:
    with Path(tasks_file).open("r", encoding="utf-8") as f:
        return json.load(f)


def get_task_by_id(tasks: List[Dict[str, Any]], task_id: str) -> Dict[str, Any]:
    for task in tasks:
        if str(task["task_id"]) == str(task_id):
            return task
    raise KeyError(f"Task not found: {task_id}")


def append_row(path: Path, fieldnames: List[str], row: Dict[str, Any]) -> None:
    ensure_csv(Path(path), fieldnames)
    clean_row = {field: row.get(field, "") for field in fieldnames}
    with Path(path).open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(clean_row)
