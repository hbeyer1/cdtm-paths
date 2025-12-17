#!/usr/bin/env python3
"""
Interactive Dash web application for visualizing CDTM alumni education paths.
"""

import json
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from collections import defaultdict, Counter
import colorsys
from typing import Dict, List, Tuple, Set


# Load data
def load_data():
    """Load alumni and schools data from JSON files."""
    with open('data/cdtm_alumni_consolidated.json', 'r', encoding='utf-8') as f:
        alumni_data = json.load(f)

    with open('data/unique_schools_normalized.json', 'r', encoding='utf-8') as f:
        schools_data = json.load(f)

    return alumni_data, schools_data


ALUMNI_DATA, SCHOOLS_DATA = load_data()


def categorize_degree(degree: str, field: str) -> str:
    """Categorize a degree into a standardized level."""
    if not degree:
        if field:
            return "Certificate/Other"
        return "Unknown"

    degree_lower = degree.lower()

    if any(term in degree_lower for term in ['bachelor', 'b.sc', 'b.a', 'b.eng', 'bsc', 'ba ', 'bs ']):
        return "Bachelor's"
    if any(term in degree_lower for term in ['master', 'm.sc', 'm.a', 'm.eng', 'msc', 'ma ', 'ms ', 'mba']):
        return "Master's"
    if any(term in degree_lower for term in ['phd', 'ph.d', 'doctor', 'doctorate']):
        return "Doctorate"
    if any(term in degree_lower for term in ['dipl', 'diploma']):
        return "Diploma"

    return "Certificate/Other"


def categorize_field(field: str, degree: str) -> str:
    """Categorize field of study into broader categories."""
    if not field:
        if degree and 'mba' in degree.lower():
            return "Business"
        return "Unknown"

    field_lower = field.lower()

    if any(term in field_lower for term in [
        'engineering', 'computer science', 'informatics', 'information systems',
        'software', 'electrical', 'mechanical', 'industrial', 'technology', 'computer'
    ]):
        return "Engineering/Tech"

    if any(term in field_lower for term in [
        'business', 'management', 'mba', 'economics', 'finance', 'accounting',
        'marketing', 'entrepreneurship', 'bwl'
    ]):
        return "Business"

    if any(term in field_lower for term in [
        'physics', 'chemistry', 'biology', 'mathematics', 'science',
        'biotechnology', 'biotech'
    ]):
        return "Sciences"

    if any(term in field_lower for term in [
        'psychology', 'sociology', 'political', 'law', 'humanities',
        'communication', 'media', 'design'
    ]):
        return "Humanities"

    return "Other"


def get_institution_info(school_name: str) -> Tuple[str, str, bool]:
    """Get institution type, country, and top-tier status."""
    if school_name in SCHOOLS_DATA:
        school_info = SCHOOLS_DATA[school_name]
        return (
            school_info.get('institution_type', 'Unknown'),
            school_info.get('country', 'Unknown'),
            school_info.get('is_top_tier', False)
        )
    return 'Unknown', 'Unknown', False


def extract_education_sequences(alumni_data: List[Dict], filters: Dict = None) -> Tuple[List[List[Dict]], List[Dict]]:
    """Extract education sequences from alumni data with optional filtering."""
    sequences = []
    alumni_info = []

    for person in alumni_data:
        education_path = person.get('education_path', [])

        if not education_path:
            continue

        sequence = []

        for edu in education_path:
            school = edu.get('school', '')
            degree = edu.get('degree', '')
            field = edu.get('field', '')

            if 'CDTM' in school or 'Center for Digital Technology' in school:
                continue

            degree_level = categorize_degree(degree, field)
            field_category = categorize_field(field, degree)
            institution_type, country, is_top_tier = get_institution_info(school)

            sequence.append({
                'school': school,
                'degree_level': degree_level,
                'field_category': field_category,
                'institution_type': institution_type,
                'country': country,
                'is_top_tier': is_top_tier,
                'original_degree': degree,
                'original_field': field
            })

        # Apply filters
        if filters:
            if filters.get('field') and filters['field'] != 'All':
                if not any(e['field_category'] == filters['field'] for e in sequence):
                    continue

            if filters.get('degree') and filters['degree'] != 'All':
                if not any(e['degree_level'] == filters['degree'] for e in sequence):
                    continue

            if filters.get('institution') and filters['institution'] != 'All':
                if not any(e['institution_type'] == filters['institution'] for e in sequence):
                    continue

        if sequence:
            sequences.append(sequence)
            alumni_info.append({
                'name': person.get('full_name', 'Unknown'),
                'headline': person.get('headline', ''),
                'location': person.get('location', ''),
                'linkedin_url': person.get('linkedin_url', ''),
                'sequence': sequence
            })

    return sequences, alumni_info


def generate_colors(n: int, saturation: float = 0.7, value: float = 0.8) -> List[str]:
    """Generate n visually distinct colors."""
    colors = []
    for i in range(n):
        hue = i / n
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        colors.append(f'rgba({int(rgb[0]*255)}, {int(rgb[1]*255)}, {int(rgb[2]*255)}, 0.8)')
    return colors


def build_sankey_data(sequences: List[List[Dict]], alumni_info: List[Dict], view_mode: str = 'field'):
    """Build Sankey diagram data from education sequences."""

    node_set = set()
    flow_counter = defaultdict(int)
    flow_alumni = defaultdict(list)  # Track which alumni use each flow

    degree_levels = ['Bachelor\'s', 'Diploma', 'Master\'s', 'Doctorate']

    for idx, sequence in enumerate(sequences):
        stages = []

        for degree_level in degree_levels:
            entries = [e for e in sequence if e['degree_level'] == degree_level]
            if entries:
                stages.append(entries[0])

        for i in range(len(stages) - 1):
            current = stages[i]
            next_stage = stages[i + 1]

            if view_mode == 'field':
                current_node = f"{current['degree_level']}\n{current['field_category']}"
                next_node = f"{next_stage['degree_level']}\n{next_stage['field_category']}"
            elif view_mode == 'institution':
                current_node = f"{current['degree_level']}\n{current['institution_type']}"
                next_node = f"{next_stage['degree_level']}\n{next_stage['institution_type']}"
            else:  # country
                current_node = f"{current['degree_level']}\n{current['country']}"
                next_node = f"{next_stage['degree_level']}\n{next_stage['country']}"

            node_set.add(current_node)
            node_set.add(next_node)

            flow_key = (current_node, next_node)
            flow_counter[flow_key] += 1
            flow_alumni[flow_key].append(alumni_info[idx])

    node_list = sorted(list(node_set))
    node_dict = {node: idx for idx, node in enumerate(node_list)}

    node_colors = generate_colors(len(node_list))

    sources = []
    targets = []
    values = []
    customdata = []

    for (source_node, target_node), count in flow_counter.items():
        sources.append(node_dict[source_node])
        targets.append(node_dict[target_node])
        values.append(count)

        # Prepare custom data for hover
        alumni_list = flow_alumni[(source_node, target_node)]
        alumni_names = [a['name'] for a in alumni_list[:10]]  # First 10
        if len(alumni_list) > 10:
            alumni_names.append(f"... and {len(alumni_list) - 10} more")

        customdata.append({
            'count': count,
            'alumni': alumni_names,
            'source': source_node.replace('\n', ' - '),
            'target': target_node.replace('\n', ' - ')
        })

    return node_list, sources, targets, values, node_colors, customdata


def create_sankey_figure(sequences, alumni_info, view_mode='field'):
    """Create a Sankey figure."""

    if not sequences:
        # Return empty figure
        fig = go.Figure()
        fig.update_layout(
            title="No data available with current filters",
            height=700
        )
        return fig

    nodes, sources, targets, values, colors, customdata = build_sankey_data(
        sequences, alumni_info, view_mode
    )

    # Create hover text for links
    link_labels = []
    for cd in customdata:
        hover_text = f"<b>{cd['source']} → {cd['target']}</b><br>"
        hover_text += f"<b>Count:</b> {cd['count']} alumni<br><br>"
        hover_text += "<b>Sample alumni:</b><br>"
        hover_text += "<br>".join(cd['alumni'])
        link_labels.append(hover_text)

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=30,
            line=dict(color="white", width=2),
            label=nodes,
            color=colors,
            hovertemplate='<b>%{label}</b><br>%{value} transitions<extra></extra>'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(150, 150, 150, 0.3)",
            hovertemplate='%{customdata}<extra></extra>',
            customdata=link_labels
        )
    )])

    title_suffix = {
        'field': 'by Field of Study',
        'institution': 'by Institution Type',
        'country': 'by Country'
    }

    fig.update_layout(
        title={
            'text': f"CDTM Alumni Education Paths - {title_suffix.get(view_mode, '')}",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'family': 'Arial, sans-serif'}
        },
        font=dict(size=11, family='Arial, sans-serif'),
        height=700,
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    return fig


def get_statistics(sequences, alumni_info):
    """Calculate statistics from sequences."""
    if not sequences:
        return {}

    total_alumni = len(sequences)

    degree_counter = Counter()
    field_counter = Counter()
    institution_counter = Counter()

    for sequence in sequences:
        for edu in sequence:
            degree_counter[edu['degree_level']] += 1
            field_counter[edu['field_category']] += 1
            institution_counter[edu['institution_type']] += 1

    # Most common transitions
    transition_counter = Counter()
    degree_levels = ['Bachelor\'s', 'Diploma', 'Master\'s', 'Doctorate']

    for sequence in sequences:
        stages = []
        for degree_level in degree_levels:
            entries = [e for e in sequence if e['degree_level'] == degree_level]
            if entries:
                stages.append(entries[0])

        for i in range(len(stages) - 1):
            current = stages[i]
            next_stage = stages[i + 1]
            transition = (
                f"{current['degree_level']} ({current['field_category']})",
                f"{next_stage['degree_level']} ({next_stage['field_category']})"
            )
            transition_counter[transition] += 1

    return {
        'total_alumni': total_alumni,
        'degree_counter': degree_counter.most_common(10),
        'field_counter': field_counter.most_common(10),
        'institution_counter': institution_counter.most_common(10),
        'top_transitions': transition_counter.most_common(10)
    }


# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "CDTM Alumni Education Paths"

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🎓 CDTM Alumni Education Path Explorer", className="text-center mb-4 mt-4"),
            html.P(
                "Interactive visualization of education paths for CDTM alumni. "
                "Hover over flows to see individual alumni names and details.",
                className="text-center text-muted mb-4"
            )
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Filters & Controls")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("View Mode:", className="fw-bold"),
                            dcc.Dropdown(
                                id='view-mode',
                                options=[
                                    {'label': 'By Field of Study', 'value': 'field'},
                                    {'label': 'By Institution Type', 'value': 'institution'},
                                    {'label': 'By Country', 'value': 'country'}
                                ],
                                value='field',
                                clearable=False
                            )
                        ], md=4),

                        dbc.Col([
                            html.Label("Filter by Field:", className="fw-bold"),
                            dcc.Dropdown(
                                id='field-filter',
                                options=[
                                    {'label': 'All Fields', 'value': 'All'},
                                    {'label': 'Engineering/Tech', 'value': 'Engineering/Tech'},
                                    {'label': 'Business', 'value': 'Business'},
                                    {'label': 'Sciences', 'value': 'Sciences'},
                                    {'label': 'Humanities', 'value': 'Humanities'},
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
                        ], md=4)
                    ]),

                    dbc.Row([
                        dbc.Col([
                            html.Label("Filter by Institution:", className="fw-bold mt-3"),
                            dcc.Dropdown(
                                id='institution-filter',
                                options=[
                                    {'label': 'All Institutions', 'value': 'All'},
                                    {'label': 'University', 'value': 'University'},
                                    {'label': 'Technical University', 'value': 'Technical University'},
                                    {'label': 'Business School', 'value': 'Business School'},
                                    {'label': 'College', 'value': 'College'}
                                ],
                                value='All',
                                clearable=False
                            )
                        ], md=4),

                        dbc.Col([
                            html.Div([
                                html.Label("", className="d-block"),
                                dbc.Button(
                                    "Reset All Filters",
                                    id='reset-button',
                                    color="secondary",
                                    className="mt-4 w-100"
                                )
                            ])
                        ], md=4)
                    ], className="mt-3")
                ])
            ], className="mb-4")
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Education Flow Diagram")),
                dbc.CardBody([
                    dcc.Loading(
                        id="loading-sankey",
                        type="default",
                        children=[
                            dcc.Graph(
                                id='sankey-diagram',
                                config={'displayModeBar': True, 'displaylogo': False}
                            )
                        ]
                    )
                ])
            ])
        ], md=8),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Statistics")),
                dbc.CardBody([
                    html.Div(id='statistics-panel')
                ])
            ], className="mb-3"),

            dbc.Card([
                dbc.CardHeader(html.H5("Top Transitions")),
                dbc.CardBody([
                    html.Div(id='transitions-panel', style={'max-height': '400px', 'overflow-y': 'auto'})
                ])
            ])
        ], md=4)
    ]),

    dbc.Row([
        dbc.Col([
            html.Hr(className="my-4"),
            html.P(
                "Data source: CDTM Alumni LinkedIn profiles | "
                "Hover over flows to see individual alumni paths",
                className="text-center text-muted small"
            )
        ])
    ])
], fluid=True)


@app.callback(
    [Output('sankey-diagram', 'figure'),
     Output('statistics-panel', 'children'),
     Output('transitions-panel', 'children')],
    [Input('view-mode', 'value'),
     Input('field-filter', 'value'),
     Input('degree-filter', 'value'),
     Input('institution-filter', 'value')]
)
def update_visualization(view_mode, field_filter, degree_filter, institution_filter):
    """Update the visualization based on filters."""

    filters = {
        'field': field_filter if field_filter != 'All' else None,
        'degree': degree_filter if degree_filter != 'All' else None,
        'institution': institution_filter if institution_filter != 'All' else None
    }

    sequences, alumni_info = extract_education_sequences(ALUMNI_DATA, filters)

    # Create Sankey figure
    fig = create_sankey_figure(sequences, alumni_info, view_mode)

    # Calculate statistics
    stats = get_statistics(sequences, alumni_info)

    # Create statistics panel
    if stats:
        stats_content = [
            html.H6(f"Total Alumni: {stats['total_alumni']}", className="mb-3"),

            html.H6("Top Degree Levels:", className="mt-3 mb-2"),
            html.Ul([
                html.Li(f"{degree}: {count}", className="small")
                for degree, count in stats['degree_counter'][:5]
            ]),

            html.H6("Top Fields:", className="mt-3 mb-2"),
            html.Ul([
                html.Li(f"{field}: {count}", className="small")
                for field, count in stats['field_counter'][:5]
            ])
        ]
    else:
        stats_content = [html.P("No data available")]

    # Create transitions panel
    if stats and stats.get('top_transitions'):
        transitions_content = [
            html.Div([
                html.P([
                    html.Span(f"{count}", className="badge bg-primary me-2"),
                    html.Span(f"{source} → {target}", className="small")
                ], className="mb-2")
                for (source, target), count in stats['top_transitions']
            ])
        ]
    else:
        transitions_content = [html.P("No transitions found")]

    return fig, stats_content, transitions_content


@app.callback(
    [Output('field-filter', 'value'),
     Output('degree-filter', 'value'),
     Output('institution-filter', 'value')],
    [Input('reset-button', 'n_clicks')],
    prevent_initial_call=True
)
def reset_filters(n_clicks):
    """Reset all filters to default values."""
    return 'All', 'All', 'All'


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Starting CDTM Alumni Education Path Explorer")
    print("="*60)
    print(f"\nLoaded {len(ALUMNI_DATA)} alumni profiles")
    print("\nOpen your browser and navigate to: http://127.0.0.1:8050")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    app.run_server(debug=True, host='0.0.0.0', port=8050)
