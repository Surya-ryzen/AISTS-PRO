# AI Smart Traffic System

Development project for traffic video analysis, emergency vehicle evidence, signal simulation and lane forecasting.

## Setup on Windows

1. Install Python 3.12 and PostgreSQL. Create a new database and a database user that owns it.
2. From this folder run:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements/week10.txt
Copy-Item backend/.env.example backend/.env
```

3. Edit `backend/.env`: set your PostgreSQL connection URL and replace `SECRET_KEY` with a random secret. Generate one with `.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"`. Never commit `.env`.
4. Initialize an empty database and create your own login:

```powershell
.venv\Scripts\python.exe -m backend.scripts.setup_ai_backend
.venv\Scripts\python.exe -m backend.scripts.create_admin
```

5. Supply your own video in `datasets/videos/raw/traffic_main.mp4`. Register its relative path in the `cameras` table with `source_type` = `file`, `is_active` = true, and a creation timestamp. For example, in pgAdmin's Query Tool against your new database:

```sql
INSERT INTO cameras (name, source, source_type, is_active, created_at)
VALUES ('Traffic main', 'datasets/videos/raw/traffic_main.mp4', 'file', true, CURRENT_TIMESTAMP);
```

6. Run `Start-Traffic.cmd`. Open http://127.0.0.1:8000/docs for APIs, `/video-preview` for playback and `/road-setup` to configure the road and lanes. Authorize in the API documentation with your own new username and password; leave client ID and secret blank.

## Implemented components

- YOLO vehicle detection, tracking, optical flow speed estimates and lane traffic analytics.
- Rule-based signal simulation and emergency evidence/history with reviewed priority requests.
- Forecast stream/sample ingestion, training jobs, 1/5/15-minute forecasting, contribution explanations, database caching and history.
- JWT authentication and bcrypt password hashing.

Forecasts need sufficient contiguous minute samples; short repeated clips do not establish real forecasting accuracy. Speed estimates require calibration. Experimental emergency model weights are not enabled by default. Signals are simulated; this is not a validated road controller. Some legacy services and frontend folders are scaffolding.

## Tests

```powershell
.venv\Scripts\python.exe -m pip install pytest httpx
.venv\Scripts\python.exe -m pytest backend/tests -q
```

Tests use isolated databases and fixtures; passing them does not establish real-world detection accuracy.

## Package contents

This repository is a source snapshot. Existing project file names are retained. Local passwords, database records, chats, personal review notes, backups, caches, downloaded footage and training outputs are excluded. Supply media separately and use fresh credentials. `Start-Week10.cmd` is an optional isolated SQLite demo; `Show-Database.cmd` is a legacy SQLite viewer, not a PostgreSQL browser. For PostgreSQL use pgAdmin.
