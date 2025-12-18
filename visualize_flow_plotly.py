#!/usr/bin/env python3
"""
Interactive Plotly-based visualization with hover support showing individual alumni names.
"""

import json
import plotly.graph_objects as go
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Tuple


def load_data():
    """Load alumni and schools data."""
    with open('data/cdtm_alumni_consolidated.json', 'r', encoding='utf-8') as f:
        alumni_data = json.load(f)
    with open('data/unique_schools_normalized.json', 'r', encoding='utf-8') as f:
        schools_data = json.load(f)
    return alumni_data, schools_data


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


def get_institution_type(school_name: str, schools_data: Dict) -> str:
    """Get institution type."""
    if school_name in schools_data:
        return schools_data[school_name].get('institution_type', 'University')
    return 'University'


def is_cdtm(school_name: str) -> bool:
    """Check if school is CDTM."""
    return 'CDTM' in school_name or 'Center for Digital Technology' in school_name


def extract_paths(alumni_data: List[Dict], schools_data: Dict) -> List[Dict]:
    """Extract education paths from alumni data, INCLUDING CDTM."""
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
                institution_type = get_institution_type(school, schools_data)

                all_entries.append({
                    'degree': degree_level,
                    'field': field_category,
                    'institution': institution_type,
                    'is_cdtm': False
                })

        if not all_entries:
            continue

        # Determine where CDTM fits
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

        if len(all_entries) >= 2:
            paths.append({
                'nodes': all_entries,
                'primary_field': primary_field or "Other",
                'name': person.get('full_name', 'Unknown'),
                'headline': person.get('headline', '')
            })

    return paths


def define_stations() -> Dict[str, Tuple[float, float]]:
    """Define node positions including ONE CENTRAL CDTM NODE."""
    return {
        "Bachelor's|Engineering/Tech": (0.5, 6.5),
        "Bachelor's|Business": (0.5, 4.5),
        "Bachelor's|Sciences": (0.5, 2.5),
        "Bachelor's|Other": (0.5, 1.0),
        "Diploma|Engineering/Tech": (2.0, 6.0),
        "Diploma|Business": (2.0, 3.5),
        "Diploma|Other": (2.0, 1.5),
        "CDTM": (3.0, 4.0),  # Single CDTM node
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


def sigmoid_curve(p1: Tuple[float, float], p2: Tuple[float, float], n_points: int = 50) -> Tuple[np.ndarray, np.ndarray]:
    """Generate an S-curve between two points."""
    x1, y1 = p1
    x2, y2 = p2

    x = np.linspace(x1, x2, n_points)
    t = (x - x1) / (x2 - x1) if x2 != x1 else np.zeros_like(x)
    y = y1 + (y2 - y1) * (1 - np.cos(np.pi * t)) / 2

    return x, y


def create_plotly_visualization(paths: List[Dict], output_file: str = 'education_flow_interactive.html'):
    """Create interactive Plotly visualization with hover support."""

    stations = define_stations()

    field_colors = {
        "Engineering/Tech": "#3b82f6",
        "Business": "#ef4444",
        "Sciences": "#10b981",
        "Other": "#94a3b8",
        "CDTM": "#f59e0b"
    }

    fig = go.Figure()

    # Count station usage for sizing
    station_counts = Counter()

    # Draw paths as individual traces (for hover)
    for path_data in paths:
        path_nodes = path_data['nodes']
        primary_field = path_data['primary_field']
        color = field_colors.get(primary_field, field_colors["Other"])

        alumni_name = path_data['name']
        headline = path_data['headline']

        # Draw each segment of the path
        for i in range(len(path_nodes) - 1):
            current = path_nodes[i]
            next_node = path_nodes[i + 1]

            # Build station keys
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

            # Add small jitter
            y_jitter_start = np.random.uniform(-0.1, 0.1)
            y_jitter_end = np.random.uniform(-0.1, 0.1)

            xs, ys = sigmoid_curve(
                (x1, y1 + y_jitter_start),
                (x2, y2 + y_jitter_end),
                n_points=30
            )

            # Use orange for CDTM connections
            if current.get('is_cdtm') or next_node.get('is_cdtm'):
                line_color = field_colors["CDTM"]
                line_alpha = 0.3
            else:
                line_color = color
                line_alpha = 0.2

            # Add trace for this path segment
            fig.add_trace(go.Scatter(
                x=xs,
                y=ys,
                mode='lines',
                line=dict(color=line_color, width=1),
                opacity=line_alpha,
                hovertemplate=f'<b>{alumni_name}</b><br>{headline}<br><extra></extra>',
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

        # Add node
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

    # Update layout
    fig.update_layout(
        title={
            'text': "CDTM Alumni Education Pathways - Interactive",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24}
        },
        xaxis=dict(
            range=[-0.5, 8],
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        yaxis=dict(
            range=[-0.5, 8],
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=800,
        width=1600,
        hovermode='closest'
    )

    fig.write_html(output_file)
    print(f"\n✓ Saved interactive visualization to: {output_file}")
    print(f"✓ Open in browser to hover over paths and see alumni names!")

    return fig


def main():
    """Main function."""
    print("Loading CDTM alumni data...")
    alumni_data, schools_data = load_data()
    print(f"Loaded {len(alumni_data)} alumni profiles")

    print("\nExtracting education paths...")
    paths = extract_paths(alumni_data, schools_data)
    print(f"Extracted {len(paths)} valid education paths")

    print("\nCreating interactive Plotly visualization...")
    create_plotly_visualization(paths)

    print("\n✅ Done! Open 'education_flow_interactive.html' in your browser.")


if __name__ == '__main__':
    main()
