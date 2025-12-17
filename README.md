# CDTM Alumni Education Path Visualization

This project visualizes the education paths of CDTM (Center for Digital Technology and Management) alumni using interactive Sankey diagrams.

## Overview

The visualization uses a flow-style diagram with sigmoid curves to show how CDTM alumni progress through different educational stages, from Bachelor's degrees through Master's and Doctoral programs. Each line represents one alumni's education journey, with colors indicating their primary field of study. This creates a beautiful, organic visualization that reveals common pathways and transitions at a glance.

## Data

The project uses two main data files:

- `data/cdtm_alumni_consolidated.json` - Contains education and career information for CDTM alumni
- `data/unique_schools_normalized.json` - Contains normalized information about educational institutions

## Visualizations

### Interactive Web Application (Recommended) - Flow Style

The main application uses a **flow-style visualization** with sigmoid curves, similar to professional pathway diagrams. Features include:

- **Beautiful flow diagram** with smooth curves showing individual paths
- **Color coding** by primary field of study (Blue: Engineering/Tech, Red: Business, Green: Sciences)
- **Volume visualization** through line density - thicker areas show more common paths
- **Real-time filtering** by field and degree level
- **Statistics dashboard** showing distribution and path characteristics
- **Responsive design** that works on desktop and tablet devices

### Static Visualizations

The project also includes scripts to generate static visualizations:

1. **Flow-Style PNG** (`visualize_flow_style.py`) - Creates high-resolution flow diagrams
2. **Sankey Diagrams** (`visualize_education_paths_enhanced.py`) - Traditional Sankey charts with:
   - By Field of Study view
   - By Institution Type view

## Usage

### Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Running the Interactive Web Application (Recommended)

**Option 1: Using the launch script**

```bash
./run_app.sh
```

**Option 2: Direct Python execution**

```bash
python app.py
```

Then open your browser and navigate to: **http://localhost:8050**

**Features:**
- **Flow Visualization**: Beautiful sigmoid curves showing individual education paths
- **Color Coding**: Blue (Engineering/Tech), Red (Business), Green (Sciences), Gray (Other)
- **Filters**: Filter by primary field or specific degree level
- **Statistics**: View real-time statistics including path lengths and field distribution
- **Volume Effect**: Line density shows how common each pathway is
- **Reset**: Click "Reset Filters" to clear all filters and see the full dataset

### Generating Static Visualizations

#### Flow-Style Diagram (Recommended)

```bash
python visualize_flow_style.py
```

This generates `education_flow_viz.png` - a high-resolution flow diagram with sigmoid curves

#### Sankey Diagrams

```bash
python visualize_education_paths.py  # Basic version
python visualize_education_paths_enhanced.py  # Enhanced version
```

These generate interactive HTML Sankey diagrams:
- `education_paths_sankey.html` - Basic Sankey diagram
- `education_paths_by_field.html` - By field of study
- `education_paths_by_institution.html` - By institution type

### Viewing Static Results

Open any of the generated HTML files in a web browser to view the interactive Sankey diagrams. The diagrams support:

- Hovering over nodes and links to see detailed information
- Zooming and panning
- Clicking and dragging to rearrange the view

## Key Insights

Based on the analysis of 1,037 CDTM alumni with education data:

- **Most Common Path**: Bachelor's in Engineering/Tech → Master's in Engineering/Tech (201 alumni)
- **Cross-Discipline Transitions**: 52 alumni moved from Bachelor's in Business to Master's in Engineering/Tech
- **Popular Fields**: Engineering/Tech (128.6%), Business (75.1%), and Natural Sciences (16.2%)
- **Institution Types**: Most attended Universities (165.1%) and Technical Universities (112.2%)

## Project Structure

```
cdtm-paths/
├── data/
│   ├── cdtm_alumni_consolidated.json       # Alumni education and career data
│   └── unique_schools_normalized.json      # Normalized school information
├── app.py                                   # Interactive Dash web app (flow style)
├── app_sankey.py                            # Alternative Sankey-based web app
├── run_app.sh                               # Launch script for web app
├── visualize_flow_style.py                  # Flow-style static visualization
├── visualize_education_paths.py            # Basic Sankey visualization script
├── visualize_education_paths_enhanced.py   # Enhanced Sankey visualizations
├── requirements.txt                        # Python dependencies
├── README.md                               # This file
└── QUICKSTART.md                           # Quick start guide
```

## Technical Details

The visualization uses:
- **Matplotlib** - For creating flow-style diagrams with sigmoid curves
- **Dash** - Python framework for building interactive web applications
- **NumPy** - For mathematical curve generation and data processing
- **Bootstrap** - For responsive UI components (via dash-bootstrap-components)
- **Python 3** - For data processing and analysis
- Custom categorization logic to group degrees and fields into meaningful categories

**Visualization Techniques:**
- **Sigmoid curves** - Smooth S-curves between education stages
- **Y-axis jitter** - Creates volume effect by slightly randomizing positions
- **Alpha blending** - Transparent overlapping lines show density
- **Color coding** - Different fields shown in distinct colors
- **Dynamic node sizing** - Nodes sized based on traffic volume

**Technologies:**
- Frontend: Dash + Matplotlib + Bootstrap
- Backend: Python 3 + NumPy
- Data Format: JSON
- Visualization: Flow diagrams with sigmoid curves, Sankey diagrams (alternative)

## License

This project is for educational and research purposes.