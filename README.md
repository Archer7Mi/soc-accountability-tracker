# SOC Accountability Tracker

Local Streamlit + SQLite app for tracking SC-200 progress, SOC labs, artifacts, and execution discipline.

## Features

- Glassmorphism dashboard and UI theme
- Today dashboard with KPI metrics and anti-gaming score model
- Work block logging (planned vs completed)
- Artifact logging with quality gate fields (objective, query, recommendation, evidence)
- Daily progress tracking (modules, labs, commits, assignments)
- 14-day sprint planner with task status tracking
- Manage entries page for edit/delete corrections
- Weekly review with health status
- Penalty board for missed quality artifact days

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   py -m streamlit run app.py
   ```

The SQLite database is created automatically as `tracker.db` in the project root.

## Deploy

### Streamlit Community Cloud

1. Push this repo to GitHub.
2. In Streamlit Community Cloud, create a new app from your repository.
3. Set main file path to `app.py`.
4. Deploy.

### Render

This repository includes `render.yaml` and is ready for blueprint deploy.

1. Push this repo to GitHub.
2. In Render, create a new Blueprint from the repository.
3. Confirm service settings from `render.yaml`.
4. Deploy.

### Data Persistence Note

The app uses local SQLite (`tracker.db`). On cloud platforms with ephemeral disks, data may reset on restart.
Use a persistent disk or migrate to a managed database if you need durable production data.

## Suggested Daily Use

1. Update daily progress first.
2. Log each work block as you complete it.
3. Log at least one artifact per day.
4. Review weekly score and missed artifact days.

## Quality Rules

- A day is not successful unless at least one quality artifact exists.
- Quality artifact requires non-empty: objective, query logic, recommendation, and evidence path.
- Sprint task status is constrained to: `todo`, `doing`, `done`, `blocked`.

## Data Model

- `daily_progress`: per-day metrics and review notes
- `work_blocks`: execution time records
- `artifacts`: proof-of-work entries
