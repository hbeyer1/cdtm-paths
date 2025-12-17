# CDTM Alumni Education Path Visualization

This project visualizes the education paths of CDTM (Center for Digital Technology and Management) alumni using interactive Sankey diagrams.

## Overview

The visualization shows how CDTM alumni progress through different educational stages, from Bachelor's degrees through Master's and Doctoral programs. The diagrams illustrate common education pathways and transitions between fields of study and institution types.

## Data

The project uses two main data files:

- `data/cdtm_alumni_consolidated.json` - Contains education and career information for CDTM alumni
- `data/unique_schools_normalized.json` - Contains normalized information about educational institutions

## Visualizations

### Interactive Web Application (Recommended)

The project includes an interactive Dash web application that provides:

- **Real-time filtering** by field, degree level, and institution type
- **Multiple view modes**: By field of study, institution type, or country
- **Hover information** showing individual alumni names for each education path
- **Statistics dashboard** with top transitions and distributions
- **Responsive design** that works on desktop and tablet devices

### Static Visualizations

The project also generates static HTML Sankey diagrams:

1. **By Field of Study** - Shows transitions between different academic fields (Engineering/Tech, Business, Sciences, etc.)
2. **By Institution Type** - Shows transitions between institution types (University, Technical University, Business School, etc.)

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
- **Filters**: Use dropdowns to filter by field, degree level, or institution type
- **View Modes**: Switch between field of study, institution type, or country views
- **Hover Information**: Hover over any flow to see names of individual alumni following that path
- **Statistics**: View real-time statistics in the right panel
- **Reset**: Click "Reset All Filters" to clear all filters

### Generating Static Visualizations

#### Basic Version

```bash
python visualize_education_paths.py
```

This generates `education_paths_sankey.html`

#### Enhanced Version

```bash
python visualize_education_paths_enhanced.py
```

This generates two HTML files:
- `education_paths_by_field.html` - Education paths by field of study
- `education_paths_by_institution.html` - Education paths by institution type

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
├── app.py                                   # Interactive Dash web application
├── run_app.sh                               # Launch script for web app
├── visualize_education_paths.py            # Basic static visualization script
├── visualize_education_paths_enhanced.py   # Enhanced static visualization
├── requirements.txt                        # Python dependencies
└── README.md                               # This file
```

## Technical Details

The visualization uses:
- **Dash** - Python framework for building interactive web applications
- **Plotly** - For creating interactive Sankey diagrams
- **Bootstrap** - For responsive UI components (via dash-bootstrap-components)
- **Python 3** - For data processing and analysis
- Custom categorization logic to group degrees and fields into meaningful categories

**Technologies:**
- Frontend: Dash + Plotly + Bootstrap
- Backend: Python 3
- Data Format: JSON
- Visualization: Interactive Sankey Diagrams

## License

This project is for educational and research purposes.