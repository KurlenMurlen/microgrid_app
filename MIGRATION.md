# Migration Guide: Flask to Next.js

This document explains how to run the migrated Next.js frontend with the Flask backend.

## Architecture

The application is now split into two parts:

- **Backend**: Flask API (`/Users/null/microgrid_app/app.py`) - Serves all `/api/*` endpoints
- **Frontend**: Next.js application (`/Users/null/microgrid_app/frontend/`) - Serves the UI

## Development Setup

### 1. Install Flask-CORS dependency

```bash
cd /Users/null/microgrid_app
source venv/bin/activate  # or your virtual environment
pip install Flask-CORS
```

### 2. Start Flask Backend

```bash
cd /Users/null/microgrid_app
source venv/bin/activate
python app.py
```

Flask will start on `http://localhost:5000` (or the next available port).

### 3. Start Next.js Frontend

In a new terminal:

```bash
cd /Users/null/microgrid_app/frontend
npm install  # First time only
npm run dev
```

Next.js will start on `http://localhost:3000`.

### 4. Open the Application

Navigate to [http://localhost:3000](http://localhost:3000) in your browser.

## What Changed

### Backend Changes

1. **Added CORS Support**: `Flask-CORS` package added to allow cross-origin requests from Next.js
2. **No Other Changes**: All Flask routes, logic, and ML models remain unchanged

### Frontend Changes

1. **New Frontend**: Complete Next.js application in `frontend/` directory
2. **TypeScript**: Fully typed with TypeScript interfaces
3. **Tailwind CSS**: Modern utility-first CSS framework
4. **Same Features**: All original features preserved:
   - Home view with economy visualization
   - Technical dashboard with charts
   - Real-time SSE streaming
   - Multiple algorithms and optimization modes
   - Export functionality

## Features Preserved

✅ Live/DB/CSV/Simulation data sources  
✅ ML forecasting (RF/Linear/Ridge/Lasso)  
✅ Real-time SSE streaming  
✅ Battery optimization modes  
✅ Pricing analytics with TOU tariffs  
✅ Equipment state visualization  
✅ Anomaly detection  
✅ CSV export  
✅ Dark mode  

## Environment Variables

### Backend (.env - optional)

```bash
# Allow Next.js production frontend
CORS_ORIGIN=https://your-frontend-domain.vercel.app
```

### Frontend (.env.local)

```bash
# Flask API URL
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## Production Deployment

### Option 1: Separate Deployments (Recommended)

**Backend (Flask)**:
- Deploy to Render, Railway, or Fly.io
- Keep existing `render.yaml` configuration
- Add `CORS_ORIGIN` environment variable with your frontend URL

**Frontend (Next.js)**:
- Deploy to Vercel (easiest)
- Set `NEXT_PUBLIC_API_URL` to your Flask backend URL

**Example**:
```bash
# Backend on Render
https://microgrid-api.onrender.com

# Frontend on Vercel  
https://microgrid.vercel.app
```

### Option 2: Same Server

You can serve both from the same server, but this requires additional configuration:
1. Build Next.js: `npm run build`
2. Use Flask to serve the Next.js build output
3. Not recommended - defeats the purpose of Next.js

## Troubleshooting

### CORS Errors

If you see CORS errors in the browser console:

1. Ensure Flask-CORS is installed: `pip install Flask-CORS`
2. Restart the Flask server
3. Check that the Flask server shows CORS is enabled in startup logs

### SSE Not Working

Server-Sent Events require:
1. The Flask backend must be running
2. Source must be set to 'live' or 'sim'
3. Browser must support EventSource API (all modern browsers do)

### Plotly Charts Not Showing

Plotly.js is dynamically imported to avoid SSR issues. If charts don't appear:
1. Check browser console for errors
2. Ensure `plotly.js` and `react-plotly.js` are installed
3. Refresh the page

## Original Flask App

The original Flask application with HTML templates is still intact:
- Templates: `/Users/null/microgrid_app/templates/dashboard.html`
- Static files: `/Users/null/microgrid_app/static/`

You can still access the original version by:
1. Stop the Next.js frontend
2. Navigate directly to `http://localhost:5000` (Flask server)

## File Structure

```
microgrid_app/
├── app.py                 # Flask backend (CORS added)
├── requirements.txt       # Flask dependencies (Flask-CORS added)
├── frontend/              # NEW: Next.js frontend
│   ├── app/              # Next.js pages
│   ├── components/       # React components
│   ├── lib/              # API client & hooks
│   └── package.json      # Node dependencies
├── templates/            # OLD: Flask HTML templates (still works)
├── static/               # OLD: Static assets (still works)
├── models/               # ML models (unchanged)
└── data/                 # Database (unchanged)
```

## Next Steps

1. Test all features in the Next.js frontend
2. Verify SSE streaming works in live/sim modes
3. Test all controls (source, algo, mode, sliders)
4. Verify CSV export functionality
5. Test on different screen sizes
6. Deploy to production when ready

## Support

For issues or questions:
1. Check browser console for errors
2. Check Flask backend logs
3. Verify both servers are running
4. Ensure environment variables are set correctly
