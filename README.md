# PhotoMorph Deduplicator

Local full-stack app that scans image folders, groups similar photos, recommends what to keep/delete, and stores scan history.

## Project structure

- `/backend` — FastAPI API, image analysis pipeline, SQLite persistence.
- `/frontend` — React + TypeScript + Tailwind UI for setup, report history, and grouped clean-up gallery.

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend endpoints:
- `POST /api/scans`
- `GET /api/sessions`
- `GET /api/sessions/{id}`
- `POST /api/sessions/{id}/decisions`
- `POST /api/sessions/{id}/delete-marked`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE` if the backend is not on `http://localhost:8000`.

## Testing

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=. pytest tests -q
```
