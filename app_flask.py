#!/usr/bin/env python3
"""
Simple Flask web application serving interactive Plotly visualization.
"""

from flask import Flask, render_template_string, jsonify, request
import json
import plotly.graph_objects as go
import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

app = Flask(__name__)

# Data loading
def load_data():
    """Load alumni and schools data."""
    with open('data/cdtm_alumni_consolidated.json', 'r', encoding='utf-8') as f:
        alumni_data = json.load(f)
    with open('data/unique_schools_normalized.json', 'r', encoding='utf-8') as f:
        schools_data = json.load(f)
    return alumni_data, schools_data


ALUMNI_DATA, SCHOOLS_DATA = load_data()


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


def categorize_field(field: str) -> str:
    if not field:
        return "Other"
    field_lower = field.lower()

    engineering_keywords = ['engineering', 'computer science', 'informatics', 'technology', 'cs', 'electrical', 'mechanical']
    business_keywords = ['business', 'management', 'economics', 'mba', 'finance', 'marketing']
    science_keywords = ['science', 'physics', 'chemistry', 'biology', 'mathematics', 'math']

    if any(kw in field_lower for kw in engineering_keywords):
        return "Engineering/Tech"
    if any(kw in field_lower for kw in business_keywords):
        return "Business"
    if any(kw in field_lower for kw in science_keywords):
        return "Sciences"

    return "Other"


def define_stations() -> Dict[str, Tuple[float, float]]:
    """Define station positions for the visualization."""
    stations = {
        "CDTM": (3.0, 4.0),

        "Bachelor's|Engineering/Tech": (0.5, 6.5),
        "Bachelor's|Business": (0.5, 5.0),
        "Bachelor's|Sciences": (0.5, 3.5),
        "Bachelor's|Other": (0.5, 2.0),

        "Diploma|Engineering/Tech": (1.5, 6.0),
        "Diploma|Business": (1.5, 4.5),
        "Diploma|Other": (1.5, 3.0),

        "Master's|Engineering/Tech": (5.0, 6.5),
        "Master's|Business": (5.0, 5.0),
        "Master's|Sciences": (5.0, 3.5),
        "Master's|Other": (5.0, 2.0),

        "Doctorate|Engineering/Tech": (7.0, 6.0),
        "Doctorate|Business": (7.0, 4.5),
        "Doctorate|Sciences": (7.0, 3.0),
        "Doctorate|Other": (7.0, 1.5),
    }
    return stations


def extract_paths(alumni_data: List[Dict], filters: Dict = None):
    """Extract education paths from alumni data."""
    paths = []

    for person in alumni_data:
        education_path = person.get('education_path', [])
        if not education_path:
            continue

        all_entries = []
        cdtm_level = None

        for idx, entry in enumerate(education_path):
            institution = entry.get('institution', '')
            degree = entry.get('degree_name', '')
            field = entry.get('field_of_study', '')

            if 'CDTM' in institution.upper() or 'CENTER FOR DIGITAL TECHNOLOGY' in institution.upper():
                cdtm_level = idx
                continue

            categorized_degree = categorize_degree(degree, field)
            categorized_field = categorize_field(field)

            if filters:
                if filters.get('field') and categorized_field != filters['field']:
                    continue
                if filters.get('degree') and categorized_degree != filters['degree']:
                    continue

            all_entries.append({
                'degree': categorized_degree,
                'field': categorized_field,
                'institution': institution,
                'is_cdtm': False
            })

        if not all_entries:
            continue

        if cdtm_level is not None:
            bachelor_idx = next((i for i, e in enumerate(all_entries)
                               if e['degree'] in ["Bachelor's", "Diploma"]), None)

            if bachelor_idx is not None:
                insert_idx = bachelor_idx + 1
            else:
                master_idx = next((i for i, e in enumerate(all_entries)
                                 if e['degree'] == "Master's"), None)
                if master_idx is not None:
                    insert_idx = master_idx + 1
                else:
                    insert_idx = 1

            cdtm_node = {
                'degree': 'CDTM',
                'field': 'CDTM',
                'institution': 'CDTM',
                'is_cdtm': True,
                'cdtm_level': cdtm_level
            }
            all_entries.insert(min(insert_idx, len(all_entries)), cdtm_node)

        primary_field = None
        for entry in all_entries:
            if entry['field'] != "Other" and not entry.get('is_cdtm'):
                primary_field = entry['field']
                break

        if len(all_entries) >= 2:
            paths.append({
                'nodes': all_entries,
                'primary_field': primary_field or "Other",
                'name': person.get('full_name', 'Unknown'),
                'headline': person.get('headline', ''),
                'linkedin_url': person.get('linkedin_url', '')
            })

    return paths


def sigmoid_curve(p1: Tuple[float, float], p2: Tuple[float, float], n_points: int = 30):
    """Generate sigmoid curve between two points."""
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
    for path_idx, path_data in enumerate(paths):
        path_nodes = path_data['nodes']
        primary_field = path_data['primary_field']
        color = field_colors.get(primary_field, field_colors["Other"])

        alumni_name = path_data['name']
        headline = path_data['headline']
        linkedin_url = path_data.get('linkedin_url', '')
        path_id = f"path_{path_idx}"

        hover_text = f'<b>{alumni_name}</b><br>{headline}'
        if linkedin_url:
            hover_text += f'<br><br>Click to open LinkedIn profile'

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
                line=dict(color=line_color, width=2.5),
                opacity=line_alpha,
                hovertemplate=hover_text + '<extra></extra>',
                hoverlabel=dict(
                    bgcolor=line_color,
                    font_size=13,
                    font_family="Arial",
                    font_color="white"
                ),
                customdata=[[path_id, line_color, line_alpha, linkedin_url]] * len(xs),
                showlegend=False,
                name=path_id,
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
            'font': {'size': 24}
        },
        xaxis=dict(range=[-0.5, 8], showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(range=[-0.5, 8], showgrid=False, showticklabels=False, zeroline=False),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=800,
        hovermode='closest',
        hoverdistance=20,
    )

    return fig


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CDTM Alumni Education Paths</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .controls {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .control-group {
            flex: 1;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        button {
            padding: 8px 20px;
            background: #6c757d;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 26px;
        }
        button:hover {
            background: #5a6268;
        }
        #graph {
            width: 100%;
            height: 800px;
        }
        .stats {
            margin-top: 20px;
            padding: 15px;
            background: #e9ecef;
            border-radius: 8px;
        }
        .instructions {
            margin-top: 20px;
            padding: 15px;
            background: #fff3cd;
            border-left: 4px solid #f59e0b;
            border-radius: 4px;
        }
        .instructions h3 {
            margin-top: 0;
        }
        .instructions ul {
            margin-bottom: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 CDTM Alumni Education Path Explorer</h1>
        <p class="subtitle">Interactive visualization of {{ total_alumni }} CDTM alumni education journeys</p>

        <div class="controls">
            <div class="control-group">
                <label for="fieldFilter">Filter by Field:</label>
                <select id="fieldFilter">
                    <option value="All">All Fields</option>
                    <option value="Engineering/Tech">Engineering/Tech</option>
                    <option value="Business">Business</option>
                    <option value="Sciences">Sciences</option>
                    <option value="Other">Other</option>
                </select>
            </div>
            <div class="control-group">
                <label for="degreeFilter">Filter by Degree:</label>
                <select id="degreeFilter">
                    <option value="All">All Degrees</option>
                    <option value="Bachelor's">Bachelor's</option>
                    <option value="Master's">Master's</option>
                    <option value="Doctorate">Doctorate</option>
                    <option value="Diploma">Diploma</option>
                </select>
            </div>
            <div class="control-group">
                <button onclick="resetFilters()">Reset Filters</button>
            </div>
        </div>

        <div id="graph"></div>

        <div class="stats" id="stats">
            Loading statistics...
        </div>

        <div class="instructions">
            <h3>How to Use:</h3>
            <ul>
                <li><strong>Hover</strong> over any path line to highlight it - other paths will fade out dramatically</li>
                <li><strong>Click</strong> on any path to open the alumni's LinkedIn profile in a new tab</li>
                <li><strong>Hover</strong> over nodes to see how many alumni pass through that stage</li>
                <li><strong>Use filters</strong> above to focus on specific fields or degree types</li>
                <li><strong>Orange paths and nodes</strong> represent the CDTM program</li>
            </ul>
        </div>
    </div>

    <script>
        var currentFilters = {field: 'All', degree: 'All'};
        var hoveredPath = null;

        function loadGraph() {
            var url = '/api/graph?field=' + currentFilters.field + '&degree=' + currentFilters.degree;
            console.log('Loading graph from:', url);

            fetch(url)
                .then(response => {
                    console.log('Response status:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log('Received data:', data);
                    console.log('Number of traces:', data.data.length);
                    console.log('Layout:', data.layout);

                    Plotly.newPlot('graph', data.data, data.layout, {displayModeBar: true})
                        .then(() => {
                            console.log('Graph plotted successfully');
                            // Update stats
                            document.getElementById('stats').innerHTML = data.stats;

                            // Set up hover highlighting
                            var graphDiv = document.getElementById('graph');

                            graphDiv.on('plotly_hover', function(eventData) {
                                console.log('Hover event:', eventData);
                                var point = eventData.points[0];
                                if (!point.data.customdata || !point.data.customdata[0]) return;

                                var pathId = point.data.customdata[0][0];
                                console.log('Hovered path:', pathId);
                                if (hoveredPath === pathId) return;
                                hoveredPath = pathId;

                                var update = {opacity: [], 'line.width': []};
                                for (var i = 0; i < graphDiv.data.length; i++) {
                                    var trace = graphDiv.data[i];
                                    if (trace.mode === 'lines' && trace.customdata) {
                                        var tracePathId = trace.customdata[0][0];
                                        if (tracePathId === pathId) {
                                            update.opacity.push(1.0);
                                            update['line.width'].push(5);
                                        } else {
                                            update.opacity.push(0.03);
                                            update['line.width'].push(1.5);
                                        }
                                    } else {
                                        update.opacity.push(trace.opacity !== undefined ? trace.opacity : 1);
                                        update['line.width'].push(trace.marker ? trace.marker.size : 1);
                                    }
                                }
                                console.log('Applying hover style');
                                Plotly.restyle(graphDiv, update);
                            });

                            graphDiv.on('plotly_unhover', function() {
                                console.log('Unhover event');
                                if (hoveredPath === null) return;
                                hoveredPath = null;

                                var update = {opacity: [], 'line.width': []};
                                for (var i = 0; i < graphDiv.data.length; i++) {
                                    var trace = graphDiv.data[i];
                                    if (trace.mode === 'lines' && trace.customdata) {
                                        var originalAlpha = trace.customdata[0][2];
                                        update.opacity.push(originalAlpha);
                                        update['line.width'].push(2.5);
                                    } else {
                                        update.opacity.push(trace.opacity !== undefined ? trace.opacity : 1);
                                        update['line.width'].push(trace.marker ? trace.marker.size : 1);
                                    }
                                }
                                console.log('Resetting to normal style');
                                Plotly.restyle(graphDiv, update);
                            });

                            graphDiv.on('plotly_click', function(eventData) {
                                console.log('Click event:', eventData);
                                var point = eventData.points[0];
                                if (!point.data.customdata || !point.data.customdata[0]) return;

                                var linkedinUrl = point.data.customdata[0][3];
                                if (linkedinUrl) {
                                    console.log('Opening LinkedIn:', linkedinUrl);
                                    window.open(linkedinUrl, '_blank');
                                }
                            });
                        })
                        .catch(err => {
                            console.error('Error plotting graph:', err);
                            document.getElementById('stats').innerHTML = '<strong style="color: red;">Error loading graph: ' + err.message + '</strong>';
                        });
                })
                .catch(err => {
                    console.error('Error fetching data:', err);
                    document.getElementById('stats').innerHTML = '<strong style="color: red;">Error fetching data: ' + err.message + '</strong>';
                });
        }

        function updateFilters() {
            currentFilters.field = document.getElementById('fieldFilter').value;
            currentFilters.degree = document.getElementById('degreeFilter').value;
            loadGraph();
        }

        function resetFilters() {
            document.getElementById('fieldFilter').value = 'All';
            document.getElementById('degreeFilter').value = 'All';
            updateFilters();
        }

        document.getElementById('fieldFilter').addEventListener('change', updateFilters);
        document.getElementById('degreeFilter').addEventListener('change', updateFilters);

        // Load initial graph
        loadGraph();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Serve the main page."""
    return render_template_string(HTML_TEMPLATE, total_alumni=len(ALUMNI_DATA))


@app.route('/api/graph')
def get_graph():
    """API endpoint to get graph data."""
    field_filter = request.args.get('field', 'All')
    degree_filter = request.args.get('degree', 'All')

    filters = {
        'field': field_filter if field_filter != 'All' else None,
        'degree': degree_filter if degree_filter != 'All' else None
    }

    paths = extract_paths(ALUMNI_DATA, filters)
    fig = create_plotly_figure(paths)

    # Calculate statistics
    total = len(paths)
    with_cdtm = sum(1 for p in paths if any(n.get('is_cdtm') for n in p['nodes']))

    if total > 0:
        stats_html = f"""
            <strong>📊 Statistics:</strong> {total} alumni paths shown
            ({with_cdtm} include CDTM - {with_cdtm/total*100:.0f}%)
        """
    else:
        stats_html = "<strong>📊 Statistics:</strong> No alumni paths match the selected filters"

    # Convert Plotly figure to JSON-serializable dict
    fig_dict = fig.to_dict()

    return jsonify({
        'data': fig_dict['data'],
        'layout': fig_dict['layout'],
        'stats': stats_html
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("CDTM Alumni Education Path Explorer (Flask)")
    print("="*60)
    print(f"\nLoaded {len(ALUMNI_DATA)} alumni profiles")
    print("\nOpen your browser and navigate to: http://127.0.0.1:5000")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
