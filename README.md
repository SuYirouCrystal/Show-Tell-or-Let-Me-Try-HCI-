# Show, Tell, or Let Me Try

This is a Flask-based backend skeleton for an HCI study. It implements the full experiment flow while keeping the frontend intentionally minimal so it can be replaced later.

## Project Goal

This project compares how three AI explanation modalities affect user understanding, trust calibration, cognitive load, and task performance.

The three conditions are:

1. `show`: visual explanation
2. `tell`: text explanation
3. `try`: interactive explanation

When a participant starts the study, the backend assigns one condition and the participant will only see that explanation format for the entire session.

## How To Run

Python 3.10 or newer is recommended.

```bash
cd /Users/crystal_su/Show-Tell-or-Let-Me-Try-HCI-
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Local Testing With A Specific Condition

These links are only for development testing and should not be sent to real participants.

```text
http://127.0.0.1:5000/consent?condition=show
http://127.0.0.1:5000/consent?condition=tell
http://127.0.0.1:5000/consent?condition=try
```

For the actual study flow, send participants to the welcome page and have them start from the consent screen so the system can randomize the condition.

## Project Structure

```text
hci_explanation_backend/
  app.py
  config.py
  requirements.txt
  requirements-analysis.txt
  backend/
    __init__.py
    routes.py
    experiment.py
    storage.py
  data/
    tasks.json
    participants.csv
    responses.csv
    surveys.csv
  templates/
    base.html
    consent.html
    welcome.html
    task.html
    survey.html
    done.html
    error.html
  static/
    css/style.css
    js/task.js
  scripts/
    analyze_results.py
```

## Optional Analysis Script

After collecting data, you can install the analysis dependencies and run the basic analysis script:

```bash
pip install -r requirements-analysis.txt
python scripts/analyze_results.py
```

The output will be saved to:

```text
analysis_output/
```

## Implemented Backend Features

### 1. Condition assignment

When a participant starts the study, the backend assigns one of:

```text
show / tell / try
```

In normal data collection, the app prefers the least-filled condition to keep groups balanced. Condition-specific URLs are still available for local testing.

Implementation:

```text
backend/experiment.py
```

### 2. Task loading

All experiment tasks are stored in:

```text
data/tasks.json
```

Each task includes:

```text
task scenario
product options
AI recommendation
correct answer
whether the AI is correct
data needed for the three explanation conditions
```

### 3. Experiment flow control

The flow is:

```text
/              welcome page
/consent       participant consent and eligibility confirmation
/start         create participant session and assign condition
/task/1        task 1
/task/2        task 2
...
/task/6        task 6
/survey        final survey
/done          completion page
```

### 4. Response storage

After each task submission, the backend writes data to:

```text
data/responses.csv
```

Fields include:

```text
participant_id
condition
task_id
selected_option
correct_answer
is_correct
ai_recommendation
ai_is_correct
user_thinks_ai_correct
error_detection_correct
confidence_rating
client_decision_ms
server_decision_ms
```

### 5. Survey storage

The final survey is written to:

```text
data/surveys.csv
```

Fields include:

```text
perceived_understanding
trust
mental_demand
effort
frustration
engagement
feedback
```

### 6. Interactive explanation API

The sliders in the `try` condition call this endpoint:

```text
POST /api/tasks/<task_id>/simulate
```

Request format:

```json
{
  "weights": {
    "price": 30,
    "battery_life": 50,
    "weight": 20
  }
}
```

Response format:

```json
{
  "recommendation": "A",
  "recommendation_name": "NovaBook Air",
  "scores": []
}
```

This endpoint is not a real machine learning model. It is a deterministic weighted scoring simulation used to support the interactive explanation condition in the HCI study.

## Recommended User Study Procedure

1. Pilot the study internally with all 3 conditions using the developer links above.
2. Replace the placeholder contact language on the consent page before collecting real data.
3. Open the app on one study device or deploy it to a shared URL.
4. Send real participants only to `http://127.0.0.1:5000/` or your deployed root URL.
5. Ask participants to complete the study in one sitting without refreshing or opening multiple tabs.
6. After data collection, export `data/participants.csv`, `data/responses.csv`, and `data/surveys.csv` for analysis.

Recommended moderator script:

- Ask the participant to read the consent form and continue only if they agree.
- Do not explain the three conditions in advance.
- Tell them to choose the best product for each scenario and answer honestly about whether the AI is correct.
- Do not help with task decisions once the study begins.

## Data Export

During local development, you can access:

```text
/admin/export/responses
/admin/export/surveys
/admin/export/participants
```

These routes do not have authentication. Remove them or protect them before deploying to a public environment.

## Frontend Notes

The frontend pages are only a minimal skeleton. Their main purpose is to let the backend flow run end to end.

Frontend teammates can later replace:

```text
templates/*.html
static/css/style.css
static/js/task.js
```

As long as the form field names stay the same, the backend does not need to change.

Important form field names:

```text
selected_option
user_thinks_ai_correct
confidence_rating
client_decision_ms
perceived_understanding
trust
mental_demand
effort
frustration
engagement
feedback
```

## Possible Future Improvements

1. A more polished frontend interface
2. Balanced random assignment so group sizes stay closer
3. Protection against duplicate submissions
4. Admin authentication
5. A data analysis dashboard
6. Deployment to Render, Railway, or a university server
