#!/usr/bin/env python3
"""
Interactive Dash web application using Plotly with hover support for individual alumni.
"""

import json
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Tuple


# Data loading
def load_data():
    """Load alumni and schools data."""
    with open('data/cdtm_alumni_consolidated.json', 'r', encoding='utf-8') as f:
        alumni_data = json.load(f)
    with open('data/unique_schools_normalized.json', 'r', encoding='utf-8') as f:
        schools_data = json.load(f)
    return alumni_data, schools_data


ALUMNI_DATA, SCHOOLS_DATA = load_data()


# Helper functions (same as before)
def categorize_degree(degree: str, field: str) -> str:
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
    if not field:
        if degree and 'mba' in degree.lower():
            return "Business"
        return "Other"
    field_lower = field.lower()
    if any(term in field_lower for term in ['engineering', 'computer', 'informatics', 'software', 'electrical', 'mechanical', 'technology']):
        return "Engineering/Tech"
    if any(term in field_lower for term in ['business', 'management', 'mba', 'economics', 'finance', 'bwl']):
        return "Business"
    if any(term in field_lower for term in ['physics', 'chemistry', 'biology', 'mathematics', 'science', 'biotech']):
        return "Sciences"
    return "Other"


def get_institution_type(school_name: str) -> str:
    if school_name in SCHOOLS_DATA:
        return SCHOOLS_DATA[school_name].get('institution_type', 'University')
    return 'University'


def is_cdtm(school_name: str) -> bool:
    return 'CDTM' in school_name or 'Center for Digital Technology' in school_name


def extract_paths(alumni_data: List[Dict], filters: Dict = None) -> List[Dict]:
    """Extract education paths with optional filtering."""
    paths = []

    for person in alumni_data:
        education_path = person.get('education_path', [])
        if not education_path:
            continue

        all_entries = []
        cdtm_entry = None

        for edu in education_path:
            school = edu.get('school', '')
            degree = edu.get('degree', '')
            field = edu.get('field', '')

            if is_cdtm(school):
                cdtm_entry = edu
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

        # Determine CDTM position
        cdtm_level = None
        insert_position = None

        for i, entry in enumerate(all_entries):
            if entry['degree'] in ["Bachelor's", "Diploma"]:
                insert_position = i + 1
                cdtm_level = "Bachelor's Level"
                break

        if insert_position is None:
            for i, entry in enumerate(all_entries):
                if entry['degree'] == "Master's":
                    insert_position = i + 1
                    cdtm_level = "Master's Level"
                    break

        if insert_position is None and len(all_entries) > 0:
            insert_position = 1 if len(all_entries) > 1 else 0
            cdtm_level = "Bachelor's Level"

        if cdtm_entry and insert_position is not None and cdtm_level:
            cdtm_node = {
                'degree': 'CDTM',
                'field': 'CDTM',
                'institution': 'CDTM',
                'is_cdtm': True,
                'cdtm_level': cdtm_level
            }
            all_entries.insert(insert_position, cdtm_node)

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

        if len(all_entries) >= 2:
            paths.append({
                'nodes': all_entries,
                'primary_field': primary_field or "Other",
                'name': person.get('full_name', 'Unknown'),
                'headline': person.get('headline', '')
            })

    return paths


def define_stations() -> Dict[str, Tuple[float, float]]:
    """Define node positions."""
    return {
        "Bachelor's|Engineering/Tech": (0.5, 6.5),
        "Bachelor's|Business": (0.5, 4.5),
        "Bachelor's|Sciences": (0.5, 2.5),
        "Bachelor's|Other": (0.5, 1.0),
        "Diploma|Engineering/Tech": (2.0, 6.0),
        "Diploma|Business": (2.0, 3.5),
        "Diploma|Other": (2.0, 1.5),
        "CDTM": (3.0, 4.0),
        "Master's|Engineering/Tech": (4.5, 6.8),
        "Master's|Business": (4.5, 5.0),
        "Master's|Sciences": (4.5, 3.2),
        "Master's|Other": (4.5, 1.8),
        "Doctorate|Engineering/Tech": (7.0, 6.5),
        "Doctorate|Sciences": (7.0, 4.5),
        "Doctorate|Other": (7.0, 2.5),
        "Other|Engineering/Tech": (3.5, 0.5),
        "Other|Business": (4.0, 0.3),
        "Other|Sciences": (5.5, 0.5),
        "Other|Other": (6.0, 0.3),
    }


def sigmoid_curve(p1: Tuple[float, float], p2: Tuple[float, float], n_points: int = 30) -> Tuple[np.ndarray, np.ndarray]:
    """Generate S-curve."""
    x1, y1 = p1
    x2, y2 = p2
    x = np.linspace(x1, x2, n_points)
    t = (x - x1) / (x2 - x1) if x2 != x1 else np.zeros_like(x)
    y = y1 + (y2 - y1) * (1 - np.cos(np.pi * t)) / 2
    return x, y


def create_plotly_figure(paths: List[Dict]):
    """Create Plotly figure with hover support."""
    stations = define_stations()

    field_colors = {
        "Engineering/Tech": "#3b82f6",
        "Business": "#ef4444",
        "Sciences": "#10b981",
        "Other": "#94a3b8",
        "CDTM": "#f59e0b"
    }

    fig = go.Figure()
    station_counts = Counter()

    # Draw paths
    for path_data in paths:
        path_nodes = path_data['nodes']
        primary_field = path_data['primary_field']
        color = field_colors.get(primary_field, field_colors["Other"])

        alumni_name = path_data['name']
        headline = path_data['headline']

        for i in range(len(path_nodes) - 1):
            current = path_nodes[i]
            next_node = path_nodes[i + 1]

            if current.get('is_cdtm'):
                current_key = "CDTM"
            else:
                current_key = f"{current['degree']}|{current['field']}"

            if next_node.get('is_cdtm'):
                next_key = "CDTM"
            else:
                next_key = f"{next_node['degree']}|{next_node['field']}"

            if current_key not in stations or next_key not in stations:
                continue

            x1, y1 = stations[current_key]
            x2, y2 = stations[next_key]

            y_jitter_start = np.random.uniform(-0.1, 0.1)
            y_jitter_end = np.random.uniform(-0.1, 0.1)

            xs, ys = sigmoid_curve(
                (x1, y1 + y_jitter_start),
                (x2, y2 + y_jitter_end)
            )

            if current.get('is_cdtm') or next_node.get('is_cdtm'):
                line_color = field_colors["CDTM"]
                line_alpha = 0.3
            else:
                line_color = color
                line_alpha = 0.2

            fig.add_trace(go.Scatter(
                x=xs,
                y=ys,
                mode='lines',
                line=dict(color=line_color, width=2.5),  # Thicker for easier hover
                opacity=line_alpha,
                hovertemplate=f'<b>{alumni_name}</b><br>{headline}<br><extra></extra>',
                hoverlabel=dict(
                    bgcolor=line_color,
                    font_size=13,
                    font_family="Arial",
                    font_color="white"
                ),
                showlegend=False
            ))

            station_counts[current_key] += 1
            station_counts[next_key] += 1

    # Draw nodes
    for station_name, (sx, sy) in stations.items():
        count = station_counts.get(station_name, 0)
        if count == 0:
            continue

        is_cdtm_node = (station_name == "CDTM")

        if is_cdtm_node:
            node_color = field_colors["CDTM"]
            node_size = min(50, 15 + count * 0.03)
            label = "CDTM"
        else:
            node_color = "#1e293b"
            node_size = min(30, 10 + count * 0.02)
            degree, field = station_name.split('|')
            label = f"{degree}<br>{field}"

        fig.add_trace(go.Scatter(
            x=[sx],
            y=[sy],
            mode='markers+text',
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(color='white', width=2)
            ),
            text=label,
            textposition="top center" if sy > 3.5 else "bottom center",
            textfont=dict(size=10 if is_cdtm_node else 8, color=node_color),
            hovertemplate=f'<b>{label}</b><br>{count} alumni<extra></extra>',
            showlegend=False
        ))

    fig.update_layout(
        title={
            'text': "CDTM Alumni Education Pathways",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis=dict(range=[-0.5, 8], showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(range=[-0.5, 8], showgrid=False, showticklabels=False, zeroline=False),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=700,
        hovermode='closest',
        hoverdistance=20  # Increased hover detection distance
    )

    return fig


def get_statistics(paths):
    """Calculate statistics."""
    if not paths:
        return {}

    total_alumni = len(paths)
    paths_with_cdtm = sum(1 for p in paths if any(n.get('is_cdtm') for n in p['nodes']))
    field_counter = Counter([p['primary_field'] for p in paths])

    degree_counter = Counter()
    for path in paths:
        for node in path['nodes']:
            if not node.get('is_cdtm'):
                degree_counter[node['degree']] += 1

    path_lengths = [len(p['nodes']) for p in paths]

    return {
        'total_alumni': total_alumni,
        'paths_with_cdtm': paths_with_cdtm,
        'field_counter': field_counter.most_common(),
        'degree_counter': degree_counter.most_common(5),
        'avg_path_length': np.mean(path_lengths),
        'median_path_length': np.median(path_lengths)
    }


# Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "CDTM Alumni Education Paths"

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🎓 CDTM Alumni Education Path Explorer", className="text-center mb-4 mt-4"),
            html.P(
                "Hover over any path to see individual alumni names and their headlines!",
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
                            dcc.Graph(id='flow-diagram', config={'displayModeBar': True})
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
                html.H5("How to Use", className="mb-3"),
                html.Ul([
                    html.Li("Hover over any line to see the alumni's name and headline"),
                    html.Li("Hover over nodes to see how many alumni pass through"),
                    html.Li("Use filters to focus on specific fields or degrees"),
                    html.Li("Orange paths and node show the central CDTM program")
                ], className="small text-muted")
            ], className="mb-3")
        ])
    ])
], fluid=True)


@app.callback(
    [Output('flow-diagram', 'figure'),
     Output('statistics-panel', 'children')],
    [Input('field-filter', 'value'),
     Input('degree-filter', 'value')]
)
def update_visualization(field_filter, degree_filter):
    """Update visualization based on filters."""
    filters = {
        'field': field_filter if field_filter != 'All' else None,
        'degree': degree_filter if degree_filter != 'All' else None
    }

    paths = extract_paths(ALUMNI_DATA, filters)
    fig = create_plotly_figure(paths)
    stats = get_statistics(paths)

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

            html.H6("Path Stats:", className="mt-3 mb-2 small"),
            html.P([
                f"Avg: {stats['avg_path_length']:.1f} stages",
                html.Br(),
                f"Median: {stats['median_path_length']:.0f} stages"
            ], className="small mb-0")
        ]
    else:
        stats_content = [html.P("No data available", className="small")]

    return fig, stats_content


@app.callback(
    [Output('field-filter', 'value'),
     Output('degree-filter', 'value')],
    [Input('reset-button', 'n_clicks')],
    prevent_initial_call=True
)
def reset_filters(n_clicks):
    """Reset filters."""
    return 'All', 'All'


if __name__ == '__main__':
    print("\n" + "="*60)
    print("CDTM Alumni Education Path Explorer (Interactive Plotly)")
    print("="*60)
    print(f"\nLoaded {len(ALUMNI_DATA)} alumni profiles")
    print("\nOpen your browser and navigate to: http://127.0.0.1:8050")
    print("Hover over paths to see alumni names!")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    app.run_server(debug=True, host='0.0.0.0', port=8050)
