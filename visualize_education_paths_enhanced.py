#!/usr/bin/env python3
"""
Enhanced visualization of education paths of CDTM alumni using Sankey diagrams.
Creates multiple views: by degree level & field, by institution type, and by country.
"""

import json
from collections import defaultdict, Counter
import plotly.graph_objects as go
from typing import Dict, List, Tuple
import colorsys


def load_data(alumni_file: str, schools_file: str) -> Tuple[List[Dict], Dict]:
    """Load alumni and schools data from JSON files."""
    with open(alumni_file, 'r', encoding='utf-8') as f:
        alumni_data = json.load(f)

    with open(schools_file, 'r', encoding='utf-8') as f:
        schools_data = json.load(f)

    return alumni_data, schools_data


def categorize_degree(degree: str, field: str) -> str:
    """Categorize a degree into a standardized level."""
    if not degree:
        if field:
            return "Certificate/Other"
        return "Unknown"

    degree_lower = degree.lower()

    # Bachelor's degrees
    if any(term in degree_lower for term in ['bachelor', 'b.sc', 'b.a', 'b.eng', 'bsc', 'ba ', 'bs ']):
        return "Bachelor's"

    # Master's degrees
    if any(term in degree_lower for term in ['master', 'm.sc', 'm.a', 'm.eng', 'msc', 'ma ', 'ms ', 'mba']):
        return "Master's"

    # Doctoral degrees
    if any(term in degree_lower for term in ['phd', 'ph.d', 'doctor', 'doctorate']):
        return "Doctorate"

    # Diploma
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

    # Engineering & Technology
    if any(term in field_lower for term in [
        'engineering', 'computer science', 'informatics', 'information systems',
        'software', 'electrical', 'mechanical', 'industrial', 'technology', 'computer'
    ]):
        return "Engineering/Tech"

    # Business & Management
    if any(term in field_lower for term in [
        'business', 'management', 'mba', 'economics', 'finance', 'accounting',
        'marketing', 'entrepreneurship', 'bwl'
    ]):
        return "Business"

    # Natural Sciences
    if any(term in field_lower for term in [
        'physics', 'chemistry', 'biology', 'mathematics', 'science',
        'biotechnology', 'biotech'
    ]):
        return "Sciences"

    # Social Sciences & Humanities
    if any(term in field_lower for term in [
        'psychology', 'sociology', 'political', 'law', 'humanities',
        'communication', 'media', 'design'
    ]):
        return "Humanities"

    return "Other"


def get_institution_info(school_name: str, schools_data: Dict) -> Tuple[str, str, bool]:
    """Get institution type, country, and top-tier status from normalized schools data."""
    if school_name in schools_data:
        school_info = schools_data[school_name]
        return (
            school_info.get('institution_type', 'Unknown'),
            school_info.get('country', 'Unknown'),
            school_info.get('is_top_tier', False)
        )
    return 'Unknown', 'Unknown', False


def extract_education_sequences(alumni_data: List[Dict], schools_data: Dict) -> List[List[Dict]]:
    """Extract education sequences from alumni data."""
    sequences = []

    for person in alumni_data:
        education_path = person.get('education_path', [])

        if not education_path:
            continue

        sequence = []

        for edu in education_path:
            school = edu.get('school', '')
            degree = edu.get('degree', '')
            field = edu.get('field', '')

            # Skip if school is CDTM (we'll handle it separately)
            if 'CDTM' in school or 'Center for Digital Technology' in school:
                continue

            degree_level = categorize_degree(degree, field)
            field_category = categorize_field(field, degree)
            institution_type, country, is_top_tier = get_institution_info(school, schools_data)

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

        if sequence:
            sequences.append(sequence)

    return sequences


def generate_colors(n: int, saturation: float = 0.7, value: float = 0.8) -> List[str]:
    """Generate n visually distinct colors."""
    colors = []
    for i in range(n):
        hue = i / n
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        colors.append(f'rgba({int(rgb[0]*255)}, {int(rgb[1]*255)}, {int(rgb[2]*255)}, 0.8)')
    return colors


def build_sankey_data_by_field(sequences: List[List[Dict]]) -> Tuple[List[str], List[int], List[int], List[int], List[str]]:
    """Build Sankey diagram data showing degree level and field transitions."""

    node_set = set()
    flow_counter = defaultdict(int)

    # Process each sequence
    for sequence in sequences:
        # Group by degree level to create stages
        degree_levels = ['Bachelor\'s', 'Diploma', 'Master\'s', 'Doctorate']

        stages = []
        for degree_level in degree_levels:
            # Find entries matching this degree level
            entries = [e for e in sequence if e['degree_level'] == degree_level]
            if entries:
                stages.append(entries[0])

        # Create flows between consecutive stages
        for i in range(len(stages) - 1):
            current = stages[i]
            next_stage = stages[i + 1]

            # Create node labels
            current_node = f"{current['degree_level']}\n{current['field_category']}"
            next_node = f"{next_stage['degree_level']}\n{next_stage['field_category']}"

            node_set.add(current_node)
            node_set.add(next_node)

            flow_key = (current_node, next_node)
            flow_counter[flow_key] += 1

    # Convert to lists for Plotly
    node_list = sorted(list(node_set))
    node_dict = {node: idx for idx, node in enumerate(node_list)}

    # Generate colors for nodes
    node_colors = generate_colors(len(node_list))

    sources = []
    targets = []
    values = []

    for (source_node, target_node), count in flow_counter.items():
        sources.append(node_dict[source_node])
        targets.append(node_dict[target_node])
        values.append(count)

    return node_list, sources, targets, values, node_colors


def build_sankey_data_by_institution(sequences: List[List[Dict]]) -> Tuple[List[str], List[int], List[int], List[int], List[str]]:
    """Build Sankey diagram data showing institution type transitions."""

    node_set = set()
    flow_counter = defaultdict(int)

    # Process each sequence
    for sequence in sequences:
        degree_levels = ['Bachelor\'s', 'Diploma', 'Master\'s', 'Doctorate']

        stages = []
        for degree_level in degree_levels:
            entries = [e for e in sequence if e['degree_level'] == degree_level]
            if entries:
                stages.append(entries[0])

        # Create flows
        for i in range(len(stages) - 1):
            current = stages[i]
            next_stage = stages[i + 1]

            current_node = f"{current['degree_level']}\n{current['institution_type']}"
            next_node = f"{next_stage['degree_level']}\n{next_stage['institution_type']}"

            node_set.add(current_node)
            node_set.add(next_node)

            flow_key = (current_node, next_node)
            flow_counter[flow_key] += 1

    node_list = sorted(list(node_set))
    node_dict = {node: idx for idx, node in enumerate(node_list)}

    node_colors = generate_colors(len(node_list))

    sources = []
    targets = []
    values = []

    for (source_node, target_node), count in flow_counter.items():
        sources.append(node_dict[source_node])
        targets.append(node_dict[target_node])
        values.append(count)

    return node_list, sources, targets, values, node_colors


def create_visualizations(alumni_data: List[Dict], schools_data: Dict):
    """Create multiple Sankey diagram visualizations."""

    print(f"Loading data for {len(alumni_data)} alumni...")

    # Extract sequences
    sequences = extract_education_sequences(alumni_data, schools_data)
    print(f"Extracted {len(sequences)} education sequences")

    # Visualization 1: By Field of Study
    print("\nCreating visualization by field of study...")
    nodes, sources, targets, values, colors = build_sankey_data_by_field(sequences)
    print(f"Created {len(nodes)} nodes and {len(sources)} flows")

    fig1 = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=30,
            line=dict(color="white", width=2),
            label=nodes,
            color=colors
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(150, 150, 150, 0.3)"
        )
    )])

    fig1.update_layout(
        title={
            'text': "CDTM Alumni Education Paths - By Field of Study",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'family': 'Arial, sans-serif'}
        },
        font=dict(size=11, family='Arial, sans-serif'),
        height=900,
        width=1600,
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    fig1.write_html('education_paths_by_field.html')
    print("Saved to: education_paths_by_field.html")

    # Visualization 2: By Institution Type
    print("\nCreating visualization by institution type...")
    nodes2, sources2, targets2, values2, colors2 = build_sankey_data_by_institution(sequences)
    print(f"Created {len(nodes2)} nodes and {len(sources2)} flows")

    fig2 = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=30,
            line=dict(color="white", width=2),
            label=nodes2,
            color=colors2
        ),
        link=dict(
            source=sources2,
            target=targets2,
            value=values2,
            color="rgba(150, 150, 150, 0.3)"
        )
    )])

    fig2.update_layout(
        title={
            'text': "CDTM Alumni Education Paths - By Institution Type",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'family': 'Arial, sans-serif'}
        },
        font=dict(size=11, family='Arial, sans-serif'),
        height=900,
        width=1600,
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    fig2.write_html('education_paths_by_institution.html')
    print("Saved to: education_paths_by_institution.html")

    # Print statistics
    print_statistics(sequences)


def print_statistics(sequences: List[List[Dict]]):
    """Print interesting statistics about the education paths."""
    print("\n" + "="*60)
    print("CDTM ALUMNI EDUCATION PATH STATISTICS")
    print("="*60)

    total_alumni = len(sequences)
    print(f"\nTotal alumni with education data: {total_alumni}")

    # Count by degree level
    degree_counter = Counter()
    field_counter = Counter()
    institution_counter = Counter()

    for sequence in sequences:
        for edu in sequence:
            degree_counter[edu['degree_level']] += 1
            field_counter[edu['field_category']] += 1
            institution_counter[edu['institution_type']] += 1

    print("\n--- Degree Levels ---")
    for degree, count in degree_counter.most_common():
        percentage = (count / total_alumni) * 100
        print(f"  {degree:20s}: {count:4d} ({percentage:.1f}%)")

    print("\n--- Fields of Study ---")
    for field, count in field_counter.most_common():
        percentage = (count / total_alumni) * 100
        print(f"  {field:20s}: {count:4d} ({percentage:.1f}%)")

    print("\n--- Institution Types ---")
    for inst_type, count in institution_counter.most_common():
        percentage = (count / total_alumni) * 100
        print(f"  {inst_type:20s}: {count:4d} ({percentage:.1f}%)")

    # Common transitions
    print("\n--- Most Common Education Transitions ---")
    transition_counter = Counter()

    for sequence in sequences:
        degree_levels = ['Bachelor\'s', 'Diploma', 'Master\'s', 'Doctorate']
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

    for (source, target), count in transition_counter.most_common(15):
        print(f"  {count:3d} alumni: {source} → {target}")


def main():
    """Main function."""
    alumni_file = 'data/cdtm_alumni_consolidated.json'
    schools_file = 'data/unique_schools_normalized.json'

    print("Loading data...")
    alumni_data, schools_data = load_data(alumni_file, schools_file)

    print(f"Loaded {len(alumni_data)} alumni and {len(schools_data)} schools\n")

    create_visualizations(alumni_data, schools_data)

    print("\n" + "="*60)
    print("Visualization complete!")
    print("Open the HTML files in a web browser to view the interactive diagrams.")
    print("="*60)


if __name__ == '__main__':
    main()
