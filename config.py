from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TASKS_FILE = DATA_DIR / "tasks.json"
RESPONSES_FILE = DATA_DIR / "responses.csv"
SURVEYS_FILE = DATA_DIR / "surveys.csv"
PARTICIPANTS_FILE = DATA_DIR / "participants.csv"

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-before-deployment")
CONDITIONS = ["show", "tell", "try"]
TASK_COUNT = 6
RANDOMIZE_TASK_ORDER = os.environ.get("RANDOMIZE_TASK_ORDER", "true").lower() == "true"
