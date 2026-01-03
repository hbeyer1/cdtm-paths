# CDTM Alumni Education Paths - Pure JavaScript Webapp

A beautiful, interactive visualization of CDTM alumni education journeys built with **pure HTML/JavaScript** - no frameworks, no dependencies except Plotly.js.

## Features

✅ **Hover Highlighting** - Hover over any path to highlight it (other paths fade to 3% opacity)
✅ **Click to LinkedIn** - Click any path to open the alumni's LinkedIn profile
✅ **Interactive Filters** - Filter by field and degree type
✅ **Real-time Statistics** - See how many paths match your filters
✅ **Beautiful UI** - Modern gradient design with smooth interactions

## How to Run

Since this loads JSON files, you need to serve it from a web server (not file://).

### Option 1: Python HTTP Server (Easiest)

```bash
# Python 3
python -m http.server 8000

# Python 2
python -m SimpleHTTPServer 8000
```

Then open: **http://localhost:8000**

### Option 2: Node.js HTTP Server

```bash
# Install http-server globally
npm install -g http-server

# Run it
http-server -p 8000
```

Then open: **http://localhost:8000**

### Option 3: VS Code Live Server

1. Install "Live Server" extension in VS Code
2. Right-click on `index.html`
3. Select "Open with Live Server"

## How It Works

1. **index.html** - The main page with beautiful UI
2. **app.js** - All the visualization logic:
   - Loads JSON data from `data/` folder
   - Processes alumni education paths
   - Creates Plotly visualization
   - Handles hover/click events and filtering

## Usage

Once the page loads:

1. **Hover** over any path line → It highlights (others fade out)
2. **Click** on any path → Opens LinkedIn profile in new tab
3. **Use filters** → Focus on specific fields or degrees
4. **Reset** → Clear all filters

## Why This Works Better

- ✅ No Python frameworks = No interference
- ✅ Pure JavaScript = Direct Plotly control
- ✅ Simple architecture = Easy to debug
- ✅ Self-contained = Just open and run

## Browser Console

Open DevTools (F12) to see debug logs:
- Data loading progress
- Number of paths extracted
- Hover/click events
- Any errors

Enjoy exploring CDTM alumni education paths! 🎓
