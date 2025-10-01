# Microgrid App

A Flask-based microgrid dashboard with real-time streaming (SSE), ML forecasting, pricing insights, and battery optimization modes.

## Features
- Live/SIM/DB/CSV data sources
- 24h ML forecast (RF / Linear / Ridge / Lasso) with uncertainty bands
- Real-time updates via SSE
- Pricing tracking (today, last 24h, by tariff period, forecast by period) and next peak hint
- Battery optimization with modes (normal / econômico / conforto), SOC mínimo and goal parsing ("quero economizar 200 reais por mês")
- CSV export and anomaly markers

## Local run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
# open http://localhost:5000
```

## Deploy (Option A — Render.com)
1. Push this repo to GitHub (see below).
2. On Render: New + Web Service → Connect your repo.
3. Render detects `render.yaml` or configure manually:
	- Build Command: `pip install -r requirements.txt`
	- Start Command: `gunicorn -w 2 -k gevent -b 0.0.0.0:$PORT app:app`
	- Environment: Python; set PYTHON_VERSION=3.11
4. Add env vars if needed: LIVE_API_URL, LIVE_API_TOKEN, WEATHER_API_URL.
5. After first deploy, map your custom domain and enable HTTPS.

### SSE considerations
- We set `X-Accel-Buffering: no` header for `/api/stream` in `render.yaml` to avoid buffering.
- Ensure any CDN/proxy in front respects long-lived connections.

## Git: create repo and push
```bash
# from project root
cd /Users/tarsobertolini/Documents/College/PESQUISA_APLICADA/microgrid_app

git init -b main
printf "__pycache__/\n.venv/\n.env\n*.pyc\n.DS_Store\n" > .gitignore
git add .
git commit -m "Initial commit: microgrid app with ML, SSE, pricing, optimization, and Render deploy files"
# create a GitHub repo named microgrid_app (via web or gh CLI)
# using gh CLI (optional):
# gh repo create KurlenMurlen/microgrid_app --public --source=. --push
# or set remote manually:
# git remote add origin git@github.com:KurlenMurlen/microgrid_app.git
# git push -u origin main
```

## Environment variables
- `PORT` (managed by platform)
- `LIVE_API_URL`, `LIVE_API_TOKEN` (optional external live data)
- `WEATHER_API_URL` (optional weather forecast)

## License
MIT
