# Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Web Application

```bash
python app.py
```

Or use the convenience script:

```bash
./run_app.sh
```

### 3. Open in Browser

Navigate to: **http://localhost:8050**

## 📊 Using the Application

### View Modes

Switch between three different visualization modes:

- **By Field of Study** - See transitions between Engineering/Tech, Business, Sciences, etc.
- **By Institution Type** - View flows between Universities, Technical Universities, Business Schools
- **By Country** - Explore international education paths

### Filtering

Use the dropdown filters to focus on specific paths:

- **Filter by Field** - Show only alumni who studied in a particular field
- **Filter by Degree** - Focus on Bachelor's, Master's, or Doctorate paths
- **Filter by Institution** - See paths through specific types of schools

### Interactive Features

- **Hover over flows** - See individual alumni names who followed that path
- **Hover over nodes** - View total number of transitions through that stage
- **Statistics panel** - Real-time updates showing distribution and top transitions
- **Reset button** - Clear all filters to see the full dataset

## 🔍 Example Use Cases

### Find cross-discipline transitions

1. Set view mode to "By Field of Study"
2. Look for flows between different colored nodes
3. Hover to see which alumni made those transitions

### Explore top-tier institution paths

1. Filter by Institution → Select "University"
2. View the flows to see common patterns
3. Check statistics panel for top transitions

### Track Engineering/Tech pathways

1. Filter by Field → Select "Engineering/Tech"
2. See the complete education journey for tech-focused alumni
3. Identify common degree progression patterns

## 💡 Tips

- The diagram updates in real-time as you change filters
- Try combining multiple filters for targeted insights
- The statistics panel shows data based on current filters
- Flow thickness indicates the number of alumni following that path
- Hover tooltips show up to 10 alumni names per flow

## 🛟 Troubleshooting

**Port already in use?**
- Edit `app.py` and change `port=8050` to another number (e.g., `port=8051`)

**Data not loading?**
- Ensure you're running the app from the project root directory
- Check that `data/` folder contains the JSON files

**Filters not working?**
- Click "Reset All Filters" to clear any stuck state
- Refresh the browser page

## 📚 More Information

See the main [README.md](README.md) for detailed documentation and technical details.
