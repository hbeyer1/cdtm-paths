#!/usr/bin/env python3
"""
Interactive Dash web application for visualizing CDTM alumni education paths
using flow-style matplotlib visualization with sigmoid curves.
NOW INCLUDING CDTM NODES!
"""

import json
import io
import base64
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Tuple


# ==========================================
# DATA LOADING
# ==========================================
def load_data():
    """Load alumni and schools data from JSON files."""
    with open('data/cdtm_alumni_consolidated.json', 'r', encoding='utf-8') as f:
        alumni_data = json.load(f)
    with open('data/unique_schools_normalized.json', 'r', encoding='utf-8') as f:
        schools_data = json.load(f)
    return alumni_data, schools_data


ALUMNI_DATA, SCHOOLS_DATA = load_data()


# ==========================================
# DATA PROCESSING FUNCTIONS
# ==========================================
def categorize_degree(degree: str, field: str) -> str:
    """Categorize a degree into a standardized level."""
    if not degree:
        return "Other"

    degree_lower = degree.lower()

    if any(term in degree_lower for term in ['bachelor', 'b.sc', 'b.a', 'b.eng', 'bsc']):
        return "Bachelor's"
    if any(term in degree_lower for term in ['master', 'm.sc', 'm.a', 'm.eng', 'msc', 'mba']):
        return "Master's"
    if any(term in degree_lower for term in ['phd', 'ph.d', 'doctor', 'doctorate']):
        return "Doctorate"
    if any(term in degree_lower for term in ['dipl', 'diploma']):
        return "Diploma"

    return "Other"


def categorize_field(field: str, degree: str) -> str:
    """Categorize field of study."""
    if not field:
        if degree and 'mba' in degree.lower():
            return "Business"
        return "Other"

    field_lower = field.lower()

    if any(term in field_lower for term in [
        'engineering', 'computer', 'informatics', 'software', 'electrical',
        'mechanical', 'technology'
    ]):
        return "Engineering/Tech"

    if any(term in field_lower for term in [
        'business', 'management', 'mba', 'economics', 'finance', 'bwl'
    ]):
        return "Business"

    if any(term in field_lower for term in [
        'physics', 'chemistry', 'biology', 'mathematics', 'science', 'biotech'
    ]):
        return "Sciences"

    return "Other"


def get_institution_type(school_name: str) -> str:
    """Get institution type."""
    if school_name in SCHOOLS_DATA:
        return SCHOOLS_DATA[school_name].get('institution_type', 'University')
    return 'University'


def is_cdtm(school_name: str) -> bool:
    """Check if school is CDTM."""
    return 'CDTM' in school_name or 'Center for Digital Technology' in school_name


def extract_paths(alumni_data: List[Dict], filters: Dict = None) -> List[Dict]:
    """Extract education paths from alumni data, INCLUDING CDTM, with optional filtering."""
    paths = []

    for person in alumni_data:
        education_path = person.get('education_path', [])
        if not education_path:
            continue

        # First pass: collect all education entries
        all_entries = []
        cdtm_entry = None

        for edu in education_path:
            school = edu.get('school', '')
            degree = edu.get('degree', '')
            field = edu.get('field', '')

            if is_cdtm(school):
                cdtm_entry = edu  # Save CDTM for later
            else:
                degree_level = categorize_degree(degree, field)
                field_category = categorize_field(field, degree)
                institution_type = get_institution_type(school)

                all_entries.append({
                    'degree': degree_level,
                    'field': field_category,
                    'institution': institution_type,
                    'is_cdtm': False
                })

        if not all_entries:
            continue

        # Determine where CDTM fits in the path
        cdtm_level = None
        insert_position = None

        # Find Bachelor's or Diploma
        for i, entry in enumerate(all_entries):
            if entry['degree'] in ["Bachelor's", "Diploma"]:
                insert_position = i + 1
                cdtm_level = "Bachelor's Level"
                break

        # If no Bachelor's found, check for Master's
        if insert_position is None:
            for i, entry in enumerate(all_entries):
                if entry['degree'] == "Master's":
                    insert_position = i + 1
                    cdtm_level = "Master's Level"
                    break

        # If still no position, put CDTM at the beginning
        if insert_position is None and len(all_entries) > 0:
            insert_position = 1 if len(all_entries) > 1 else 0
            cdtm_level = "Bachelor's Level"

        # Insert CDTM node if we found a position
        if cdtm_entry and insert_position is not None and cdtm_level:
            # Determine CDTM's "field" based on the primary field of the path
            primary_field = None
            for entry in all_entries:
                if entry['field'] != "Other":
                    primary_field = entry['field']
                    break

            cdtm_node = {
                'degree': 'CDTM',
                'field': primary_field or "Other",
                'institution': 'CDTM',
                'is_cdtm': True,
                'cdtm_level': cdtm_level
            }

            # Insert CDTM into the path
            all_entries.insert(insert_position, cdtm_node)

        # Determine primary field
        primary_field = None
        for entry in all_entries:
            if entry['field'] != "Other" and not entry.get('is_cdtm'):
                primary_field = entry['field']
                break

        # Apply filters
        if filters:
            if filters.get('field') and filters['field'] != 'All':
                if primary_field != filters['field']:
                    continue

            if filters.get('degree') and filters['degree'] != 'All':
                if not any(node['degree'] == filters['degree'] for node in all_entries):
                    continue

        if len(all_entries) >= 2:  # Need at least 2 nodes for a path
            paths.append({
                'nodes': all_entries,
                'primary_field': primary_field or "Other",
                'name': person.get('full_name', 'Unknown')
            })

    return paths


def define_stations() -> Dict[str, Tuple[float, float]]:
    """Define the (x, y) positions for each education stage node. NOW INCLUDING CDTM!"""
    stations = {
        # STAGE 1: BACHELOR'S (x ≈ 0-1)
        "Bachelor's|Engineering/Tech": (0.5, 6.5),
        "Bachelor's|Business": (0.5, 4.5),
        "Bachelor's|Sciences": (0.5, 2.5),
        "Bachelor's|Other": (0.5, 1.0),

        # STAGE 2: INTERMEDIATE (Diploma, etc.) (x ≈ 2-3)
        "Diploma|Engineering/Tech": (2.0, 6.0),
        "Diploma|Business": (2.0, 3.5),
        "Diploma|Other": (2.0, 1.5),

        # STAGE 2.5: CDTM (x ≈ 3) - Between Bachelor's/Diploma and Master's
        "CDTM|Engineering/Tech": (3.0, 6.5),
        "CDTM|Business": (3.0, 4.5),
        "CDTM|Sciences": (3.0, 2.5),
        "CDTM|Other": (3.0, 1.0),

        # STAGE 3: MASTER'S (x ≈ 4-5)
        "Master's|Engineering/Tech": (4.5, 6.8),
        "Master's|Business": (4.5, 5.0),
        "Master's|Sciences": (4.5, 3.2),
        "Master's|Other": (4.5, 1.8),

        # STAGE 4: DOCTORATE (x ≈ 7)
        "Doctorate|Engineering/Tech": (7.0, 6.5),
        "Doctorate|Sciences": (7.0, 4.5),
        "Doctorate|Other": (7.0, 2.5),

        # STAGE 5: OTHER/CERTIFICATES (various positions)
        "Other|Engineering/Tech": (3.5, 0.5),
        "Other|Business": (4.0, 0.3),
        "Other|Sciences": (5.5, 0.5),
        "Other|Other": (6.0, 0.3),
    }

    return stations


def sigmoid_curve(p1: Tuple[float, float], p2: Tuple[float, float], n_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
    """Generate an S-curve between two points."""
    x1, y1 = p1
    x2, y2 = p2

    x = np.linspace(x1, x2, n_points)

    # Sigmoid easing using cosine
    t = (x - x1) / (x2 - x1) if x2 != x1 else np.zeros_like(x)
    y = y1 + (y2 - y1) * (1 - np.cos(np.pi * t)) / 2

    return x, y


# ==========================================
# VISUALIZATION FUNCTION
# ==========================================
def create_flow_visualization(paths: List[Dict]) -> str:
    """Create flow visualization and return as base64 encoded image."""

    stations = define_stations()

    # Define colors for different fields
    field_colors = {
        "Engineering/Tech": "#3b82f6",  # Blue
        "Business": "#ef4444",           # Red
        "Sciences": "#10b981",           # Green
        "Other": "#94a3b8",              # Gray
        "CDTM": "#f59e0b"                # Orange for CDTM
    }

    # Setup figure
    fig, ax = plt.subplots(figsize=(18, 10), facecolor='white', dpi=100)

    # Count paths through each station for sizing
    station_counts = Counter()

    # STEP 1: Draw all the paths
    for path_data in paths:
        path_nodes = path_data['nodes']
        primary_field = path_data['primary_field']
        color = field_colors.get(primary_field, field_colors["Other"])

        # Draw connections between consecutive nodes
        for i in range(len(path_nodes) - 1):
            current = path_nodes[i]
            next_node = path_nodes[i + 1]

            # Build station keys
            current_key = f"{current['degree']}|{current['field']}"
            next_key = f"{next_node['degree']}|{next_node['field']}"

            # Skip if station doesn't exist
            if current_key not in stations or next_key not in stations:
                continue

            # Get coordinates
            x1, y1 = stations[current_key]
            x2, y2 = stations[next_key]

            # Add jitter to y-coordinates for volume effect
            y_jitter_start = np.random.uniform(-0.12, 0.12)
            y_jitter_end = np.random.uniform(-0.12, 0.12)

            # Generate curve
            xs, ys = sigmoid_curve(
                (x1, y1 + y_jitter_start),
                (x2, y2 + y_jitter_end)
            )

            # Use orange color if going through CDTM
            if current.get('is_cdtm') or next_node.get('is_cdtm'):
                plot_color = field_colors["CDTM"]
                alpha = 0.12
            else:
                plot_color = color
                alpha = 0.08

            # Plot with transparency for overlapping effect
            ax.plot(xs, ys, color=plot_color, alpha=alpha, linewidth=1.2, zorder=1)

            # Track station usage
            station_counts[current_key] += 1
            station_counts[next_key] += 1

    # STEP 2: Draw the stations (nodes) on top
    for station_name, (sx, sy) in stations.items():
        count = station_counts.get(station_name, 0)

        if count == 0:
            continue  # Don't draw unused stations

        # Size based on volume
        node_size = min(2000, 500 + count * 2)

        # Special styling for CDTM nodes
        is_cdtm_node = station_name.startswith("CDTM|")

        if is_cdtm_node:
            # CDTM nodes get special orange color
            node_color = '#fff7ed'  # Light orange background
            edge_color = field_colors["CDTM"]
            edge_width = 3
        else:
            node_color = 'white'
            edge_color = '#1e293b'
            edge_width = 2

        # Background circle
        ax.scatter(sx, sy, s=node_size, color=node_color, zorder=10, edgecolors='none')

        # Outline
        ax.scatter(sx, sy, s=node_size, facecolors='none',
                  edgecolors=edge_color, linewidth=edge_width, zorder=11)

        # Label
        degree, field = station_name.split('|')
        if is_cdtm_node:
            label = f"CDTM\n{field}"
        else:
            label = f"{degree}\n{field}"

        # Alternate text position to avoid overlap
        text_y_offset = 0.35 if sy > 3.5 else -0.35

        label_color = field_colors["CDTM"] if is_cdtm_node else '#1e293b'

        ax.text(sx, sy + text_y_offset, label,
               ha='center', va='center', fontsize=8,
               fontweight='bold', color=label_color, zorder=12,
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                        edgecolor='none', alpha=0.9))

    # STEP 3: Add legend
    legend_elements = [
        mpatches.Patch(facecolor=field_colors["Engineering/Tech"],
                      label='Engineering/Tech', alpha=0.7),
        mpatches.Patch(facecolor=field_colors["Business"],
                      label='Business', alpha=0.7),
        mpatches.Patch(facecolor=field_colors["Sciences"],
                      label='Sciences', alpha=0.7),
        mpatches.Patch(facecolor=field_colors["CDTM"],
                      label='CDTM', alpha=0.7),
        mpatches.Patch(facecolor=field_colors["Other"],
                      label='Other', alpha=0.7),
    ]
    ax.legend(handles=legend_elements, loc='upper right',
             fontsize=11, frameon=True, fancybox=True)

    # STEP 4: Final polish
    ax.set_xlim(-0.5, 8)
    ax.set_ylim(-0.5, 8)
    ax.axis('off')
    ax.set_title('CDTM Alumni Education Pathways',
                fontsize=20, fontweight='bold', pad=20, color='#1e293b')

    # Add subtitle with count
    ax.text(0.5, 0.98, f'Visualizing {len(paths)} alumni education journeys through CDTM',
           ha='center', va='top', transform=ax.transAxes,
           fontsize=10, color='#64748b', style='italic')

    plt.tight_layout()

    # Convert to base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    return f"data:image/png;base64,{img_base64}"


def get_statistics(paths):
    """Calculate statistics from paths."""
    if not paths:
        return {}

    total_alumni = len(paths)

    # Count paths with CDTM
    paths_with_cdtm = sum(1 for p in paths if any(n.get('is_cdtm') for n in p['nodes']))

    # Count by primary field
    field_counter = Counter([p['primary_field'] for p in paths])

    # Count degrees
    degree_counter = Counter()
    for path in paths:
        for node in path['nodes']:
            if not node.get('is_cdtm'):
                degree_counter[node['degree']] += 1

    # Path length stats
    path_lengths = [len(p['nodes']) for p in paths]

    return {
        'total_alumni': total_alumni,
        'paths_with_cdtm': paths_with_cdtm,
        'field_counter': field_counter.most_common(),
        'degree_counter': degree_counter.most_common(5),
        'avg_path_length': np.mean(path_lengths),
        'median_path_length': np.median(path_lengths)
    }


# ==========================================
# DASH APP
# ==========================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "CDTM Alumni Education Paths"

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🎓 CDTM Alumni Education Path Explorer", className="text-center mb-4 mt-4"),
            html.P(
                "Flow-style visualization showing how CDTM alumni progress through their education journey. "
                "Each line represents one person's path, with orange highlighting connections through CDTM.",
                className="text-center text-muted mb-4"
            )
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Filters")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Filter by Field:", className="fw-bold"),
                            dcc.Dropdown(
                                id='field-filter',
                                options=[
                                    {'label': 'All Fields', 'value': 'All'},
                                    {'label': 'Engineering/Tech', 'value': 'Engineering/Tech'},
                                    {'label': 'Business', 'value': 'Business'},
                                    {'label': 'Sciences', 'value': 'Sciences'},
                                    {'label': 'Other', 'value': 'Other'}
                                ],
                                value='All',
                                clearable=False
                            )
                        ], md=4),

                        dbc.Col([
                            html.Label("Filter by Degree:", className="fw-bold"),
                            dcc.Dropdown(
                                id='degree-filter',
                                options=[
                                    {'label': 'All Degrees', 'value': 'All'},
                                    {'label': "Bachelor's", 'value': "Bachelor's"},
                                    {'label': "Master's", 'value': "Master's"},
                                    {'label': "Doctorate", 'value': "Doctorate"},
                                    {'label': "Diploma", 'value': "Diploma"}
                                ],
                                value='All',
                                clearable=False
                            )
                        ], md=4),

                        dbc.Col([
                            html.Div([
                                html.Label("", className="d-block"),
                                dbc.Button(
                                    "Reset Filters",
                                    id='reset-button',
                                    color="secondary",
                                    className="mt-4 w-100"
                                )
                            ])
                        ], md=4)
                    ])
                ])
            ], className="mb-4")
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Education Flow Visualization")),
                dbc.CardBody([
                    dcc.Loading(
                        id="loading-viz",
                        type="default",
                        children=[
                            html.Img(id='flow-diagram', style={'width': '100%', 'height': 'auto'})
                        ]
                    )
                ])
            ])
        ], md=9),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Statistics")),
                dbc.CardBody([
                    html.Div(id='statistics-panel')
                ])
            ])
        ], md=3)
    ]),

    dbc.Row([
        dbc.Col([
            html.Hr(className="my-4"),
            html.Div([
                html.H5("How to Read This Visualization", className="mb-3"),
                html.Ul([
                    html.Li("Each flowing line represents one alumni's education path"),
                    html.Li("Colors indicate the alumni's primary field of study"),
                    html.Li("Orange nodes and connections show paths through CDTM"),
                    html.Li("Nodes are sized based on how many alumni pass through them"),
                    html.Li("Left to right shows progression from Bachelor's through advanced degrees")
                ], className="small text-muted")
            ], className="mb-3")
        ])
    ])
], fluid=True)


@app.callback(
    [Output('flow-diagram', 'src'),
     Output('statistics-panel', 'children')],
    [Input('field-filter', 'value'),
     Input('degree-filter', 'value')]
)
def update_visualization(field_filter, degree_filter):
    """Update the visualization based on filters."""

    filters = {
        'field': field_filter if field_filter != 'All' else None,
        'degree': degree_filter if degree_filter != 'All' else None
    }

    # Extract paths
    paths = extract_paths(ALUMNI_DATA, filters)

    # Create visualization
    if paths:
        img_src = create_flow_visualization(paths)
    else:
        # Create empty placeholder
        fig, ax = plt.subplots(figsize=(18, 10))
        ax.text(0.5, 0.5, 'No data matches the selected filters',
               ha='center', va='center', fontsize=16, color='#64748b')
        ax.axis('off')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        img_src = f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"
        plt.close(fig)

    # Calculate statistics
    stats = get_statistics(paths)

    # Create statistics panel
    if stats:
        stats_content = [
            html.H6(f"📊 {stats['total_alumni']} Alumni", className="mb-3"),
            html.P(f"📍 {stats['paths_with_cdtm']} include CDTM ({stats['paths_with_cdtm']/stats['total_alumni']*100:.0f}%)",
                  className="small text-muted mb-3"),

            html.H6("Primary Fields:", className="mt-3 mb-2 small"),
            html.Ul([
                html.Li(f"{field}: {count}", className="small")
                for field, count in stats['field_counter']
            ]),

            html.H6("Degree Levels:", className="mt-3 mb-2 small"),
            html.Ul([
                html.Li(f"{degree}: {count}", className="small")
                for degree, count in stats['degree_counter']
            ]),

            html.H6("Path Stats:", className="mt-3 mb-2 small"),
            html.P([
                f"Avg: {stats['avg_path_length']:.1f} stages",
                html.Br(),
                f"Median: {stats['median_path_length']:.0f} stages"
            ], className="small mb-0")
        ]
    else:
        stats_content = [html.P("No data available", className="small")]

    return img_src, stats_content


@app.callback(
    [Output('field-filter', 'value'),
     Output('degree-filter', 'value')],
    [Input('reset-button', 'n_clicks')],
    prevent_initial_call=True
)
def reset_filters(n_clicks):
    """Reset all filters to default values."""
    return 'All', 'All'


if __name__ == '__main__':
    print("\n" + "="*60)
    print("CDTM Alumni Education Path Explorer (Flow Style)")
    print("="*60)
    print(f"\nLoaded {len(ALUMNI_DATA)} alumni profiles")
    print("\nOpen your browser and navigate to: http://127.0.0.1:8050")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    app.run_server(debug=True, host='0.0.0.0', port=8050)
