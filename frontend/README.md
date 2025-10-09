# Microgrid Dashboard - Next.js Frontend

Next.js 14+ frontend for the Microgrid Dashboard with TypeScript, Tailwind CSS, and Plotly.js charts.

## Features

- **Home View**: Economy visualization with animated rings showing daily, monthly, and annual savings
- **Technical View**: Comprehensive dashboard with:
  - Real-time consumption monitoring
  - 24-hour ML forecasting with multiple algorithms (Random Forest, Linear, Ridge, Lasso)
  - Battery optimization with different modes (normal, econômico, conforto)
  - Equipment state visualization (PV, Battery, Grid, Load)
  - Pricing analytics with TOU tariffs
  - SSE streaming for live updates
- **Dark Mode**: Automatic dark mode support
- **Responsive Design**: Works on all screen sizes

## Setup

### Prerequisites

- Node.js 18+
- Flask backend running on port 5000

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL to your Flask backend URL

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Environment Variables

Create a `.env.local` file:

```bash
# Flask API URL
NEXT_PUBLIC_API_URL=http://localhost:5000
```

For production, set this to your deployed Flask API URL.

## Development

```bash
# Development server with hot reload
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Architecture

- **App Router**: Next.js 14+ App Router with TypeScript
- **Styling**: Tailwind CSS with custom design tokens
- **Charts**: Plotly.js via react-plotly.js
- **State Management**: React hooks with custom hooks for API calls
- **Real-time**: Server-Sent Events (SSE) for live data streaming

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Main dashboard page
│   └── globals.css         # Global styles + Tailwind
├── components/             # React components
│   ├── HomeView.tsx        # Economy visualization
│   ├── TechnicalView.tsx   # Technical dashboard
│   ├── PlotlyChart.tsx     # Chart components
│   ├── ContextCubes.tsx    # Context display
│   ├── Alerts.tsx          # Alert notifications
│   ├── PricingCard.tsx     # Pricing breakdown
│   ├── OptimizationCard.tsx # Battery optimization
│   ├── NavArrows.tsx       # View navigation
│   ├── Badge.tsx           # Badge component
│   ├── Card.tsx            # Card container
│   ├── Select.tsx          # Select input
│   └── RangeSlider.tsx     # Range slider
├── lib/
│   ├── api.ts             # API client functions
│   ├── hooks.ts           # Custom React hooks
│   └── types.ts           # TypeScript interfaces
├── public/                # Static assets
├── tailwind.config.ts     # Tailwind configuration
└── next.config.js         # Next.js config
```

## API Integration

The frontend communicates with the Flask backend via:

1. **REST API**: `/api/dashboard`, `/api/export`
2. **SSE Stream**: `/api/stream` for real-time updates

All API calls go through the centralized client in `lib/api.ts`.

## Navigation

- **Arrow Buttons**: Click left/right arrows to navigate between views
- **Keyboard**: Use arrow keys (← →) to navigate
- **URL Hash**: Direct links via `#home` or `#technical`

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variable in Vercel dashboard
# NEXT_PUBLIC_API_URL = your-flask-api-url
```

### Other Platforms

Build the production bundle:

```bash
npm run build
npm start
```

Set the `NEXT_PUBLIC_API_URL` environment variable to your Flask API URL.

## License

MIT