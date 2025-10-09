# Quick Start Guide

Get the migrated Next.js frontend running in 5 minutes.

## Prerequisites

- Python 3.9+ with virtual environment
- Node.js 18+
- The Flask backend already configured

## Step 1: Install Backend Dependencies

```bash
cd /Users/null/microgrid_app

# Activate your virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install Flask-CORS
pip install Flask-CORS

# Verify all dependencies
pip install -r requirements.txt
```

## Step 2: Start Flask Backend

```bash
# Make sure you're in the project root and venv is activated
python app.py
```

You should see:
```
Starting Flask on port 5000 (set PORT env var to override)
```

Keep this terminal open.

## Step 3: Install Frontend Dependencies

Open a **new terminal**:

```bash
cd /Users/null/microgrid_app/frontend
npm install
```

This will install Next.js, React, TypeScript, Tailwind CSS, Plotly.js, and all dependencies.

## Step 4: Start Next.js Frontend

```bash
# Still in /Users/null/microgrid_app/frontend
npm run dev
```

You should see:
```
▲ Next.js 15.x.x
- Local:        http://localhost:3000
- Network:      http://192.168.x.x:3000
```

## Step 5: Open the Dashboard

Navigate to [http://localhost:3000](http://localhost:3000) in your browser.

You should see:
1. **Home View**: Economy visualization with animated rings
2. Use the **right arrow** or press **→** to navigate to the **Technical View**
3. All features from the original dashboard are available

## Verification Checklist

- [ ] Home view displays with economy rings
- [ ] Technical view shows charts and equipment state
- [ ] Can switch between data sources (Live, DB, CSV, Sim)
- [ ] Charts render correctly with Plotly
- [ ] Dark mode toggles with system preference
- [ ] Navigation arrows work (← →)
- [ ] Export CSV button works

## Common Issues

### "Failed to fetch" errors

**Problem**: Frontend can't connect to backend  
**Solution**: 
1. Verify Flask is running on port 5000
2. Check browser console for the exact error
3. Ensure CORS is enabled (Flask-CORS installed)

### "Module not found: Can't resolve 'react-plotly.js'"

**Problem**: Dependencies not installed  
**Solution**:
```bash
cd /Users/null/microgrid_app/frontend
rm -rf node_modules package-lock.json
npm install
```

### Port 3000 already in use

**Problem**: Another app is using port 3000  
**Solution**:
```bash
# Kill the process using port 3000
lsof -ti:3000 | xargs kill -9

# Or use a different port
PORT=3001 npm run dev
```

### CORS errors in browser console

**Problem**: Flask-CORS not installed or not working  
**Solution**:
```bash
# In backend terminal
pip install Flask-CORS
# Restart Flask
python app.py
```

## What's Next?

### Development

Both servers support hot reload:
- **Flask**: Edit `app.py` and it will auto-reload
- **Next.js**: Edit any file in `frontend/` and it will hot-reload

### Production Deployment

See `MIGRATION.md` for detailed deployment instructions.

Quick summary:
1. **Backend**: Deploy Flask to Render/Railway/Fly.io
2. **Frontend**: Deploy Next.js to Vercel
3. Set environment variables:
   - Backend: `CORS_ORIGIN` = your frontend URL
   - Frontend: `NEXT_PUBLIC_API_URL` = your backend URL

### Testing

Run the Next.js linter:
```bash
cd frontend
npm run lint
```

Build for production:
```bash
cd frontend
npm run build
npm start
```

## Architecture Summary

```
┌─────────────────────┐
│  Browser (3000)     │
│  Next.js Frontend   │
└──────────┬──────────┘
           │ HTTP + SSE
           ▼
┌─────────────────────┐
│  Flask API (5000)   │
│  All business logic │
│  ML models, DB, etc │
└─────────────────────┘
```

The frontend is a pure UI layer that calls the Flask API for all data and functionality.

## Support

If you encounter issues:

1. Check both terminal outputs for errors
2. Look at browser console (F12) for frontend errors
3. Verify both servers are running
4. Try restarting both servers
5. Check the MIGRATION.md for detailed troubleshooting
