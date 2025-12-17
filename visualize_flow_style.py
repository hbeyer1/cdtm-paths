#!/usr/bin/env python3
"""
Create a flow-style visualization of CDTM alumni education paths using matplotlib
with sigmoid curves, similar to the Congressional pathways visualization style.
"""

import json
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Tuple
import matplotlib.patches as mpatches


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


def extract_paths(alumni_data: List[Dict], schools_data: Dict) -> List[Dict]:
    """Extract education paths from alumni data."""
    paths = []

    for person in alumni_data:
        education_path = person.get('education_path', [])
        if not education_path:
            continue

        # Build path
        path_nodes = []
        primary_field = None

        for edu in education_path:
            school = edu.get('school', '')
            degree = edu.get('degree', '')
            field = edu.get('field', '')

            # Skip CDTM
            if 'CDTM' in school or 'Center for Digital Technology' in school:
                continue

            degree_level = categorize_degree(degree, field)
            field_category = categorize_field(field, degree)
            institution_type = get_institution_type(school, schools_data)

            # Track primary field (first non-Other field)
            if primary_field is None and field_category != "Other":
                primary_field = field_category

            path_nodes.append({
                'degree': degree_level,
                'field': field_category,
                'institution': institution_type
            })

        if len(path_nodes) >= 2:  # Need at least 2 nodes for a path
            paths.append({
                'nodes': path_nodes,
                'primary_field': primary_field or "Other",
                'name': person.get('full_name', 'Unknown')
            })

    return paths


def define_stations() -> Dict[str, Tuple[float, float]]:
    """
    Define the (x, y) positions for each education stage node.
    This creates the irregular, flowing layout similar to the reference image.
    """
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
        "Other|Engineering/Tech": (3.0, 0.5),
        "Other|Business": (3.5, 0.3),
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


def plot_education_flows(paths: List[Dict], output_file: str = 'education_flow_viz.png'):
    """Create the main flow visualization."""

    stations = define_stations()

    # Define colors for different fields (like the reference image)
    field_colors = {
        "Engineering/Tech": "#3b82f6",  # Blue
        "Business": "#ef4444",           # Red
        "Sciences": "#10b981",           # Green
        "Other": "#94a3b8"               # Gray
    }

    # Setup figure
    fig, ax = plt.subplots(figsize=(20, 12), facecolor='white')

    print(f"Plotting {len(paths)} alumni paths...")

    # Count paths through each station for sizing
    station_counts = Counter()

    # STEP 1: Draw all the paths
    plotted_count = 0
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

            # Plot with transparency for overlapping effect
            ax.plot(xs, ys, color=color, alpha=0.08, linewidth=1.2, zorder=1)

            plotted_count += 1

            # Track station usage
            station_counts[current_key] += 1
            station_counts[next_key] += 1

    print(f"Drew {plotted_count} path segments")

    # STEP 2: Draw the stations (nodes) on top
    for station_name, (sx, sy) in stations.items():
        count = station_counts.get(station_name, 0)

        if count == 0:
            continue  # Don't draw unused stations

        # Size based on volume (but keep reasonable)
        node_size = min(1500, 400 + count * 2)

        # White background circle
        ax.scatter(sx, sy, s=node_size, color='white', zorder=10, edgecolors='none')

        # Outline
        ax.scatter(sx, sy, s=node_size, facecolors='none',
                  edgecolors='#1e293b', linewidth=2, zorder=11)

        # Label
        degree, field = station_name.split('|')
        label = f"{degree}\n{field}"

        # Alternate text position to avoid overlap
        text_y_offset = 0.35 if sy > 3.5 else -0.35
        ax.text(sx, sy + text_y_offset, label,
               ha='center', va='center', fontsize=8,
               fontweight='bold', color='#1e293b', zorder=12,
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                        edgecolor='none', alpha=0.8))

    # STEP 3: Add legend
    legend_elements = [
        mpatches.Patch(facecolor=field_colors["Engineering/Tech"],
                      label='Engineering/Tech', alpha=0.7),
        mpatches.Patch(facecolor=field_colors["Business"],
                      label='Business', alpha=0.7),
        mpatches.Patch(facecolor=field_colors["Sciences"],
                      label='Sciences', alpha=0.7),
        mpatches.Patch(facecolor=field_colors["Other"],
                      label='Other', alpha=0.7),
    ]
    ax.legend(handles=legend_elements, loc='upper right',
             fontsize=12, frameon=True, fancybox=True)

    # STEP 4: Final polish
    ax.set_xlim(-0.5, 8)
    ax.set_ylim(-0.5, 8)
    ax.axis('off')
    ax.set_title('CDTM Alumni Education Pathways',
                fontsize=24, fontweight='bold', pad=30, color='#1e293b')

    # Add subtitle with count
    ax.text(0.5, 0.98, f'Visualizing education journeys of {len(paths)} CDTM alumni',
           ha='center', va='top', transform=ax.transAxes,
           fontsize=12, color='#64748b', style='italic')

    plt.tight_layout()

    # Save
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n✓ Saved visualization to: {output_file}")

    plt.close()

    return fig


def print_statistics(paths: List[Dict]):
    """Print statistics about the paths."""
    print("\n" + "="*60)
    print("EDUCATION PATH STATISTICS")
    print("="*60)

    print(f"\nTotal alumni with paths: {len(paths)}")

    # Count by primary field
    field_counter = Counter([p['primary_field'] for p in paths])
    print("\n--- Primary Fields ---")
    for field, count in field_counter.most_common():
        print(f"  {field:20s}: {count:4d} ({count/len(paths)*100:.1f}%)")

    # Path length distribution
    path_lengths = [len(p['nodes']) for p in paths]
    print("\n--- Path Lengths ---")
    print(f"  Average: {np.mean(path_lengths):.1f} stages")
    print(f"  Median: {np.median(path_lengths):.0f} stages")
    print(f"  Max: {max(path_lengths)} stages")


def main():
    """Main function."""
    print("Loading CDTM alumni data...")
    alumni_data, schools_data = load_data()
    print(f"Loaded {len(alumni_data)} alumni profiles")

    print("\nExtracting education paths...")
    paths = extract_paths(alumni_data, schools_data)
    print(f"Extracted {len(paths)} valid education paths")

    # Print statistics
    print_statistics(paths)

    # Create visualization
    print("\nCreating flow visualization...")
    plot_education_flows(paths)

    print("\n" + "="*60)
    print("✅ Visualization complete!")
    print("="*60)


if __name__ == '__main__':
    main()
