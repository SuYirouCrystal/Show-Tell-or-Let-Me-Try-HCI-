import time
import uuid
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from .experiment import (
    assign_condition,
    assign_balanced_condition,
    compute_weighted_scores,
    evaluate_error_detection,
    make_task_order,
    new_participant_id,
    public_task_payload,
)
from .storage import (
    PARTICIPANT_FIELDS,
    RESPONSE_FIELDS,
    SURVEY_FIELDS,
    append_row,
    count_rows_by_value,
    get_task_by_id,
    load_tasks,
    utc_now_iso,
)

bp = Blueprint("main", __name__)


def _tasks():
    return load_tasks(current_app.config["TASKS_FILE"])


def _require_participant():
    return bool(session.get("participant_id") and session.get("condition") and session.get("task_order"))


def _current_user_agent():
    return request.headers.get("User-Agent", "")


@bp.route("/")
def welcome():
    return render_template("welcome.html", has_session=_require_participant())


@bp.route("/consent", methods=["GET", "POST"])
def consent():
    requested_condition = request.args.get("condition") or request.form.get("condition")

    if request.method == "POST":
        age_confirm = request.form.get("age_confirm") == "yes"
        consent_agree = request.form.get("consent_agree") == "yes"
        if not age_confirm or not consent_agree:
            return render_template(
                "error.html",
                message="You must confirm eligibility and consent before starting the study.",
            ), 400

        session["consent_given"] = True
        session["consented_at"] = utc_now_iso()
        if requested_condition:
            return redirect(url_for("main.start", condition=requested_condition))
        return redirect(url_for("main.start"))

    return render_template("consent.html", requested_condition=requested_condition)


@bp.route("/start", methods=["GET", "POST"])
def start():
    if not session.get("consent_given"):
        requested_condition = request.args.get("condition") or request.form.get("condition")
        if requested_condition:
            return redirect(url_for("main.consent", condition=requested_condition))
        return redirect(url_for("main.consent"))

    tasks = _tasks()
    requested_condition = request.args.get("condition") or request.form.get("condition")
    if requested_condition:
        condition = assign_condition(current_app.config["CONDITIONS"], requested_condition)
    else:
        observed_counts = count_rows_by_value(Path(current_app.config["PARTICIPANTS_FILE"]), "condition")
        condition = assign_balanced_condition(current_app.config["CONDITIONS"], observed_counts)
    participant_id = new_participant_id()
    task_order = make_task_order(tasks, current_app.config["RANDOMIZE_TASK_ORDER"])
    consented_at = session.get("consented_at", utc_now_iso())

    session.clear()
    session["participant_id"] = participant_id
    session["condition"] = condition
    session["task_order"] = task_order
    session["trial_index"] = 0
    session["started_at"] = utc_now_iso()
    session["completed_trials"] = []

    append_row(
        Path(current_app.config["PARTICIPANTS_FILE"]),
        PARTICIPANT_FIELDS,
        {
            "participant_id": participant_id,
            "condition": condition,
            "task_order": ",".join(task_order),
            "started_at": session["started_at"],
            "consented_at": consented_at,
            "consent_version": "v1",
            "user_agent": _current_user_agent(),
        },
    )

    return redirect(url_for("main.task", trial_number=1))


@bp.route("/task")
def current_task():
    if not _require_participant():
        return redirect(url_for("main.welcome"))
    next_trial = int(session.get("trial_index", 0)) + 1
    task_count = len(session.get("task_order", []))
    if next_trial > task_count:
        return redirect(url_for("main.survey"))
    return redirect(url_for("main.task", trial_number=next_trial))


@bp.route("/task/<int:trial_number>", methods=["GET", "POST"])
def task(trial_number: int):
    if not _require_participant():
        return redirect(url_for("main.welcome"))

    tasks = _tasks()
    task_order = session["task_order"]
    task_count = len(task_order)

    if trial_number < 1 or trial_number > task_count:
        return render_template("error.html", message="Task number is out of range."), 404

    task_id = task_order[trial_number - 1]
    task_data = get_task_by_id(tasks, task_id)

    if request.method == "POST":
        selected_option = request.form.get("selected_option", "")
        user_thinks_ai_correct = request.form.get("user_thinks_ai_correct", "")
        confidence_rating = request.form.get("confidence_rating", "")
        client_decision_ms = request.form.get("client_decision_ms", "")

        start_key = f"trial_{trial_number}_start_ms"
        shown_at_key = f"trial_{trial_number}_shown_at"
        now_ms = int(time.time() * 1000)
        start_ms = session.get(start_key)
        server_decision_ms = now_ms - int(start_ms) if start_ms else ""
        submitted_at = utc_now_iso()

        correct_answer = task_data["correct_answer"]
        is_correct = selected_option == correct_answer
        error_detection_correct = evaluate_error_detection(task_data, user_thinks_ai_correct)

        append_row(
            Path(current_app.config["RESPONSES_FILE"]),
            RESPONSE_FIELDS,
            {
                "response_id": str(uuid.uuid4()),
                "participant_id": session["participant_id"],
                "condition": session["condition"],
                "trial_index": trial_number,
                "task_id": task_data["task_id"],
                "selected_option": selected_option,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "ai_recommendation": task_data["ai_recommendation"],
                "ai_is_correct": task_data["ai_is_correct"],
                "user_thinks_ai_correct": user_thinks_ai_correct,
                "error_detection_correct": error_detection_correct,
                "confidence_rating": confidence_rating,
                "client_decision_ms": client_decision_ms,
                "server_decision_ms": server_decision_ms,
                "shown_at": session.get(shown_at_key, ""),
                "submitted_at": submitted_at,
                "user_agent": _current_user_agent(),
            },
        )

        completed_trials = list(session.get("completed_trials", []))
        if trial_number not in completed_trials:
            completed_trials.append(trial_number)
        session["completed_trials"] = completed_trials
        session["trial_index"] = max(int(session.get("trial_index", 0)), trial_number)

        if trial_number >= task_count:
            return redirect(url_for("main.survey"))
        return redirect(url_for("main.task", trial_number=trial_number + 1))

    session[f"trial_{trial_number}_start_ms"] = int(time.time() * 1000)
    session[f"trial_{trial_number}_shown_at"] = utc_now_iso()

    public_task = public_task_payload(task_data, session["condition"])
    progress = {
        "trial_number": trial_number,
        "task_count": task_count,
        "percent": int((trial_number - 1) / task_count * 100),
    }
    return render_template(
        "task.html",
        task=public_task,
        condition=session["condition"],
        progress=progress,
    )


@bp.route("/survey", methods=["GET", "POST"])
def survey():
    if not _require_participant():
        return redirect(url_for("main.welcome"))

    if request.method == "POST":
        append_row(
            Path(current_app.config["SURVEYS_FILE"]),
            SURVEY_FIELDS,
            {
                "survey_id": str(uuid.uuid4()),
                "participant_id": session["participant_id"],
                "condition": session["condition"],
                "perceived_understanding": request.form.get("perceived_understanding", ""),
                "trust": request.form.get("trust", ""),
                "mental_demand": request.form.get("mental_demand", ""),
                "effort": request.form.get("effort", ""),
                "frustration": request.form.get("frustration", ""),
                "engagement": request.form.get("engagement", ""),
                "feedback": request.form.get("feedback", ""),
                "submitted_at": utc_now_iso(),
                "user_agent": _current_user_agent(),
            },
        )
        session["survey_completed"] = True
        return redirect(url_for("main.done"))

    return render_template("survey.html", condition=session["condition"])


@bp.route("/done")
def done():
    return render_template("done.html")


@bp.route("/api/health")
def api_health():
    return jsonify({"status": "ok"})


@bp.route("/api/session")
def api_session():
    if not _require_participant():
        return jsonify({"active": False})
    return jsonify({
        "active": True,
        "participant_id": session["participant_id"],
        "condition": session["condition"],
        "trial_index": session.get("trial_index", 0),
        "task_order": session.get("task_order", []),
    })


@bp.route("/api/tasks/<task_id>")
def api_task(task_id: str):
    if not _require_participant():
        return jsonify({"error": "No active participant session."}), 400
    task_data = get_task_by_id(_tasks(), task_id)
    return jsonify(public_task_payload(task_data, session["condition"]))


@bp.route("/api/tasks/<task_id>/simulate", methods=["POST"])
def api_simulate(task_id: str):
    task_data = get_task_by_id(_tasks(), task_id)
    payload = request.get_json(silent=True) or {}
    weights = payload.get("weights", {})
    result = compute_weighted_scores(task_data, weights)
    return jsonify(result)


@bp.route("/admin/export/responses")
def export_responses():
    return send_file(Path(current_app.config["RESPONSES_FILE"]), as_attachment=True)


@bp.route("/admin/export/surveys")
def export_surveys():
    return send_file(Path(current_app.config["SURVEYS_FILE"]), as_attachment=True)


@bp.route("/admin/export/participants")
def export_participants():
    return send_file(Path(current_app.config["PARTICIPANTS_FILE"]), as_attachment=True)
