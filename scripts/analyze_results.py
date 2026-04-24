from pathlib import Path

import pandas as pd
from scipy import stats

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RESPONSES_FILE = DATA_DIR / "responses.csv"
SURVEYS_FILE = DATA_DIR / "surveys.csv"
OUT_DIR = BASE_DIR / "analysis_output"


def safe_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def anova_by_condition(df, value_col):
    groups = []
    for _, group in df.groupby("condition"):
        values = safe_numeric(group[value_col]).dropna()
        if len(values) > 1:
            groups.append(values)
    if len(groups) < 2:
        return None
    result = stats.f_oneway(*groups)
    return {"metric": value_col, "f_statistic": result.statistic, "p_value": result.pvalue}


def main():
    OUT_DIR.mkdir(exist_ok=True)

    responses = pd.read_csv(RESPONSES_FILE)
    surveys = pd.read_csv(SURVEYS_FILE)

    if len(responses) == 0:
        print("No task response data yet.")
        return

    responses["is_correct"] = responses["is_correct"].astype(str).str.lower().eq("true")
    responses["error_detection_correct"] = responses["error_detection_correct"].astype(str).str.lower().eq("true")
    responses["server_decision_ms"] = safe_numeric(responses["server_decision_ms"])
    responses["confidence_rating"] = safe_numeric(responses["confidence_rating"])

    task_summary = responses.groupby("condition").agg(
        participant_count=("participant_id", "nunique"),
        task_count=("task_id", "count"),
        task_accuracy=("is_correct", "mean"),
        error_detection_accuracy=("error_detection_correct", "mean"),
        mean_confidence=("confidence_rating", "mean"),
        mean_decision_time_ms=("server_decision_ms", "mean"),
    ).reset_index()

    task_summary.to_csv(OUT_DIR / "task_summary_by_condition.csv", index=False)
    print("Task summary by condition:")
    print(task_summary.to_string(index=False))

    if len(surveys) > 0:
        survey_cols = [
            "perceived_understanding",
            "trust",
            "mental_demand",
            "effort",
            "frustration",
            "engagement",
        ]
        for col in survey_cols:
            surveys[col] = safe_numeric(surveys[col])
        survey_summary = surveys.groupby("condition")[survey_cols].mean().reset_index()
        survey_summary.to_csv(OUT_DIR / "survey_summary_by_condition.csv", index=False)
        print("\nSurvey summary by condition:")
        print(survey_summary.to_string(index=False))

    anova_rows = []
    for metric in ["is_correct", "error_detection_correct", "confidence_rating", "server_decision_ms"]:
        metric_df = responses.copy()
        if metric in ["is_correct", "error_detection_correct"]:
            metric_df[metric] = metric_df[metric].astype(float)
        result = anova_by_condition(metric_df, metric)
        if result:
            anova_rows.append(result)

    if len(surveys) > 0:
        for metric in survey_cols:
            result = anova_by_condition(surveys, metric)
            if result:
                anova_rows.append(result)

    if anova_rows:
        anova_df = pd.DataFrame(anova_rows)
        anova_df.to_csv(OUT_DIR / "anova_results.csv", index=False)
        print("\nANOVA results:")
        print(anova_df.to_string(index=False))


if __name__ == "__main__":
    main()
