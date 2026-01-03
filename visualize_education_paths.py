#!/usr/bin/env python3
"""
Visualize education paths of CDTM alumni using a Sankey diagram.
"""

import json
from collections import defaultdict, Counter
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Set


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
            return "Business/Management"
        return "Unknown"

    field_lower = field.lower()

    # Engineering & Technology
    if any(term in field_lower for term in [
        'engineering', 'computer science', 'informatics', 'information systems',
        'software', 'electrical', 'mechanical', 'industrial', 'technology'
    ]):
        return "Engineering/Tech"

    # Business & Management
    if any(term in field_lower for term in [
        'business', 'management', 'mba', 'economics', 'finance', 'accounting',
        'marketing', 'entrepreneurship', 'bwl'
    ]):
        return "Business/Management"

    # Natural Sciences
    if any(term in field_lower for term in [
        'physics', 'chemistry', 'biology', 'mathematics', 'science',
        'biotechnology', 'biotech'
    ]):
        return "Natural Sciences"

    # Social Sciences & Humanities
    if any(term in field_lower for term in [
        'psychology', 'sociology', 'political', 'law', 'humanities',
        'communication', 'media', 'design'
    ]):
        return "Social Sciences/Humanities"

    return "Other"


def get_institution_type(school_name: str, schools_data: Dict) -> str:
    """Get the institution type from normalized schools data."""
    if school_name in schools_data:
        return schools_data[school_name].get('institution_type', 'Unknown')
    return 'Unknown'


def extract_education_sequences(alumni_data: List[Dict], schools_data: Dict) -> List[List[Dict]]:
    """Extract education sequences from alumni data."""
    sequences = []

    for person in alumni_data:
        education_path = person.get('education_path', [])

        if not education_path:
            continue

        # Sort by date if possible (simple heuristic: earlier entries tend to be earlier education)
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
            institution_type = get_institution_type(school, schools_data)

            sequence.append({
                'school': school,
                'degree_level': degree_level,
                'field_category': field_category,
                'institution_type': institution_type,
                'original_degree': degree,
                'original_field': field
            })

        if sequence:
            sequences.append(sequence)

    return sequences


def build_sankey_data(sequences: List[List[Dict]], max_stages: int = 4) -> Tuple[List[str], List[int], List[int], List[int]]:
    """Build Sankey diagram data from education sequences."""

    # Track all nodes and flows
    node_set = set()
    flow_counter = defaultdict(int)

    # Process each sequence
    for sequence in sequences:
        # Group by degree level to create stages
        degree_levels = ['Bachelor\'s', 'Diploma', 'Master\'s', 'Doctorate', 'Certificate/Other']

        stages = []
        for degree_level in degree_levels:
            # Find entries matching this degree level
            entries = [e for e in sequence if e['degree_level'] == degree_level]
            if entries:
                # Take the first occurrence
                stages.append(entries[0])

        # Create flows between consecutive stages
        for i in range(len(stages) - 1):
            current = stages[i]
            next_stage = stages[i + 1]

            # Create node labels: Stage + Field
            current_node = f"{current['degree_level']} - {current['field_category']}"
            next_node = f"{next_stage['degree_level']} - {next_stage['field_category']}"

            node_set.add(current_node)
            node_set.add(next_node)

            # Track flow
            flow_key = (current_node, next_node)
            flow_counter[flow_key] += 1

    # Convert to lists for Plotly
    node_list = sorted(list(node_set))
    node_dict = {node: idx for idx, node in enumerate(node_list)}

    sources = []
    targets = []
    values = []

    for (source_node, target_node), count in flow_counter.items():
        sources.append(node_dict[source_node])
        targets.append(node_dict[target_node])
        values.append(count)

    return node_list, sources, targets, values


def create_sankey_diagram(alumni_data: List[Dict], schools_data: Dict, output_file: str = 'education_paths_sankey.html'):
    """Create and save a Sankey diagram of education paths."""

    print(f"Loading data for {len(alumni_data)} alumni...")

    # Extract sequences
    sequences = extract_education_sequences(alumni_data, schools_data)
    print(f"Extracted {len(sequences)} education sequences")

    # Build Sankey data
    nodes, sources, targets, values = build_sankey_data(sequences)
    print(f"Created {len(nodes)} nodes and {len(sources)} flows")

    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes,
            color="rgba(31, 119, 180, 0.8)"
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(0, 0, 0, 0.2)"
        )
    )])

    fig.update_layout(
        title={
            'text': "CDTM Alumni Education Paths",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24}
        },
        font=dict(size=12),
        height=800,
        width=1400
    )

    # Save to HTML
    fig.write_html(output_file)
    print(f"Sankey diagram saved to {output_file}")

    # Print some statistics
    print("\n=== Statistics ===")
    print(f"Total alumni with education data: {len(sequences)}")
    print(f"Total unique education nodes: {len(nodes)}")
    print(f"Total education transitions: {sum(values)}")

    # Most common paths
    path_counter = Counter()
    for i, (s, t, v) in enumerate(zip(sources, targets, values)):
        path_counter[(nodes[s], nodes[t])] = v

    print("\n=== Top 10 Education Transitions ===")
    for (source, target), count in path_counter.most_common(10):
        print(f"{count:3d} alumni: {source} → {target}")


def main():
    """Main function."""
    alumni_file = 'data/cdtm_alumni_consolidated.json'
    schools_file = 'data/unique_schools_normalized.json'

    print("Loading data...")
    alumni_data, schools_data = load_data(alumni_file, schools_file)

    print(f"Loaded {len(alumni_data)} alumni and {len(schools_data)} schools")

    create_sankey_diagram(alumni_data, schools_data)


if __name__ == '__main__':
    main()
