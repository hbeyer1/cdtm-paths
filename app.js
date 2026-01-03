// CDTM Alumni Education Path Visualization
// Updated to use educational_paths.csv with normalized columns

// Global state
let educationData = [];
let groupedAlumni = {};
let currentFilters = { field: 'All', degree: 'All' };
let hoveredPath = null;

// Field colors - updated for new normalized fields
const FIELD_COLORS = {
    "Computer Science & AI": "#3b82f6",
    "Business & Economics": "#ef4444",
    "Engineering": "#10b981",
    "Technology Management": "#f59e0b",
    "Information Systems & HCI": "#8b5cf6",
    "Natural Sciences & Mathematics": "#06b6d4",
    "Medicine & Health Sciences": "#ec4899",
    "Psychology & Social Sciences": "#f97316",
    "Design, Architecture & Media": "#a855f7",
    "Law & Legal Studies": "#64748b",
    "Education & Other": "#94a3b8",
    "Other": "#94a3b8",
    "CDTM": "#f59e0b"
};

// Station positions - based on normalized_degree levels
// X-axis: Education stage (left to right = earlier to later)
// Y-axis: Field categories
const STATIONS = {
    // CDTM (center position)
    "CDTM": [4.0, 4.5],

    // High School / Pre-University (leftmost)
    "High School|Other": [0.5, 1.0],

    // Undergraduate level
    "Undergraduate|Computer Science & AI": [1.5, 8.0],
    "Undergraduate|Business & Economics": [1.5, 6.5],
    "Undergraduate|Engineering": [1.5, 5.0],
    "Undergraduate|Information Systems & HCI": [1.5, 3.5],
    "Undergraduate|Natural Sciences & Mathematics": [1.5, 2.0],
    "Undergraduate|Other": [1.5, 0.5],

    // Exchange/Visiting (between undergrad and grad)
    "Exchange|Computer Science & AI": [2.5, 7.5],
    "Exchange|Business & Economics": [2.5, 6.0],
    "Exchange|Engineering": [2.5, 4.5],
    "Exchange|Other": [2.5, 1.5],

    // Graduate level
    "Graduate|Computer Science & AI": [5.5, 8.0],
    "Graduate|Business & Economics": [5.5, 6.5],
    "Graduate|Engineering": [5.5, 5.0],
    "Graduate|Technology Management": [5.5, 3.5],
    "Graduate|Information Systems & HCI": [5.5, 2.5],
    "Graduate|Natural Sciences & Mathematics": [5.5, 1.5],
    "Graduate|Other": [5.5, 0.5],

    // Post-Graduate / PhD (rightmost)
    "Doctorate|Computer Science & AI": [7.5, 7.0],
    "Doctorate|Engineering": [7.5, 5.5],
    "Doctorate|Natural Sciences & Mathematics": [7.5, 4.0],
    "Doctorate|Business & Economics": [7.5, 2.5],
    "Doctorate|Other": [7.5, 1.0]
};

// CSV Parser
function parseCSV(text) {
    const lines = text.split('\n');
    const headers = parseCSVLine(lines[0]);
    const data = [];

    for (let i = 1; i < lines.length; i++) {
        if (lines[i].trim() === '') continue;
        const values = parseCSVLine(lines[i]);
        const row = {};
        headers.forEach((header, idx) => {
            row[header] = values[idx] || '';
        });
        data.push(row);
    }

    return data;
}

function parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            result.push(current.trim());
            current = '';
        } else {
            current += char;
        }
    }
    result.push(current.trim());

    return result;
}

// Normalize degree for station mapping
function mapDegreeToStation(normalizedDegree) {
    if (!normalizedDegree) return null;

    const degreeMap = {
        'Undergraduate': 'Undergraduate',
        'Graduate': 'Graduate',
        'High School / Secondary': 'High School',
        'Pre-University': 'High School',
        'Exchange & Summer Programs': 'Exchange',
        'Visiting scholar / student researcher': 'Exchange',
        'Honours & Elite Add-on Degrees': 'CDTM', // CDTM is typically this
        'Certificates & Professional Training': null, // Skip
        'Vocational & Apprenticeships': null, // Skip
        'other': null // Skip
    };

    return degreeMap[normalizedDegree] || null;
}

// Normalize field for station mapping
function mapFieldToStation(normalizedField) {
    if (!normalizedField) return 'Other';

    const fieldMap = {
        'Computer Science & AI': 'Computer Science & AI',
        'Business & Economics': 'Business & Economics',
        'Engineering': 'Engineering',
        'Technology Management': 'Technology Management',
        'Information Systems & HCI': 'Information Systems & HCI',
        'Natural Sciences & Mathematics': 'Natural Sciences & Mathematics',
        'Medicine & Health Sciences': 'Other',
        'Psychology & Social Sciences': 'Other',
        'Design, Architecture & Media': 'Other',
        'Law & Legal Studies': 'Other',
        'Education & Other': 'Other'
    };

    return fieldMap[normalizedField] || 'Other';
}

// Check if this is a CDTM entry
function isCDTM(row) {
    const school = (row.school || '').toUpperCase();
    return school.includes('CDTM') || school.includes('CENTER FOR DIGITAL TECHNOLOGY');
}

// Sigmoid curve for smooth path lines
function sigmoidCurve(x1, y1, x2, y2, nPoints = 30) {
    const xs = [];
    const ys = [];

    for (let i = 0; i < nPoints; i++) {
        const t = i / (nPoints - 1);
        const x = x1 + (x2 - x1) * t;
        const y = y1 + (y2 - y1) * (1 - Math.cos(Math.PI * t)) / 2;
        xs.push(x);
        ys.push(y);
    }

    return { xs, ys };
}

// Group education entries by alumni
function groupByAlumni(data) {
    const grouped = {};

    data.forEach(row => {
        const key = `${row.full_name}|${row.linkedin_url}`;
        if (!grouped[key]) {
            grouped[key] = {
                full_name: row.full_name,
                headline: row.headline,
                linkedin_url: row.linkedin_url,
                location: row.location,
                education: []
            };
        }
        grouped[key].education.push({
            school: row.school,
            degree: row.degree,
            field: row.field,
            start: row.start,
            end: row.end,
            normalized_degree: row.normalized_degree,
            normalized_field: row.normalized_field
        });
    });

    return grouped;
}

// Extract paths from alumni data
function extractPaths(filters = {}) {
    const paths = [];

    Object.values(groupedAlumni).forEach(person => {
        const education = person.education || [];
        if (education.length === 0) return;

        const nodes = [];
        let hasCDTM = false;
        let primaryField = 'Other';

        // Sort education by start date (chronological)
        const sortedEducation = [...education].sort((a, b) => {
            const aYear = parseInt(a.start?.split('/')[1] || a.start || '9999');
            const bYear = parseInt(b.start?.split('/')[1] || b.start || '9999');
            return aYear - bYear;
        });

        // Process each education entry
        sortedEducation.forEach(edu => {
            // Check for CDTM
            if (isCDTM(edu)) {
                hasCDTM = true;
                nodes.push({
                    degree: 'CDTM',
                    field: 'CDTM',
                    is_cdtm: true,
                    school: edu.school
                });
                return;
            }

            const stationDegree = mapDegreeToStation(edu.normalized_degree);
            if (!stationDegree) return; // Skip entries we can't map

            const stationField = mapFieldToStation(edu.normalized_field);

            // Apply filters
            if (filters.field && filters.field !== 'All' && stationField !== filters.field) return;
            if (filters.degree && filters.degree !== 'All' && stationDegree !== filters.degree) return;

            // Determine primary field
            if (primaryField === 'Other' && stationField !== 'Other') {
                primaryField = stationField;
            }

            nodes.push({
                degree: stationDegree,
                field: stationField,
                is_cdtm: false,
                school: edu.school,
                original_degree: edu.normalized_degree,
                original_field: edu.normalized_field
            });
        });

        if (nodes.length >= 2) {
            paths.push({
                nodes: nodes,
                primary_field: primaryField,
                name: person.full_name || 'Unknown',
                headline: person.headline || '',
                linkedin_url: person.linkedin_url || '',
                has_cdtm: hasCDTM
            });
        }
    });

    return paths;
}

// Create Plotly visualization
function createVisualization(paths) {
    const traces = [];
    const stationCounts = {};

    // Initialize station counts
    Object.keys(STATIONS).forEach(key => {
        stationCounts[key] = 0;
    });

    // Draw paths
    paths.forEach((pathData, pathIdx) => {
        const pathNodes = pathData.nodes;
        const primaryField = pathData.primary_field;
        const color = FIELD_COLORS[primaryField] || FIELD_COLORS["Other"];
        const pathId = `path_${pathIdx}`;

        const hoverText = `<b>${pathData.name}</b><br>${pathData.headline}${pathData.linkedin_url ? '<br><br>Click to open LinkedIn' : ''}`;

        // Draw each segment
        for (let i = 0; i < pathNodes.length - 1; i++) {
            const current = pathNodes[i];
            const next = pathNodes[i + 1];

            const currentKey = current.is_cdtm ? "CDTM" : `${current.degree}|${current.field}`;
            const nextKey = next.is_cdtm ? "CDTM" : `${next.degree}|${next.field}`;

            if (!STATIONS[currentKey] || !STATIONS[nextKey]) continue;

            const [x1, y1] = STATIONS[currentKey];
            const [x2, y2] = STATIONS[nextKey];

            // Add jitter to avoid overlapping lines
            const yJitterStart = (Math.random() - 0.5) * 0.3;
            const yJitterEnd = (Math.random() - 0.5) * 0.3;

            const curve = sigmoidCurve(x1, y1 + yJitterStart, x2, y2 + yJitterEnd);

            const lineColor = (current.is_cdtm || next.is_cdtm) ? FIELD_COLORS["CDTM"] : color;
            const lineAlpha = (current.is_cdtm || next.is_cdtm) ? 0.4 : 0.25;

            traces.push({
                x: curve.xs,
                y: curve.ys,
                mode: 'lines',
                line: { color: lineColor, width: 2.5 },
                opacity: lineAlpha,
                hovertemplate: hoverText + '<extra></extra>',
                hoverlabel: {
                    bgcolor: lineColor,
                    font: { size: 13, family: "Arial", color: "white" }
                },
                customdata: curve.xs.map(() => [pathId, lineColor, lineAlpha, pathData.linkedin_url]),
                showlegend: false,
                name: pathId
            });

            stationCounts[currentKey] = (stationCounts[currentKey] || 0) + 1;
            stationCounts[nextKey] = (stationCounts[nextKey] || 0) + 1;
        }
    });

    // Draw nodes
    Object.entries(STATIONS).forEach(([stationName, [sx, sy]]) => {
        const count = stationCounts[stationName] || 0;
        if (count === 0) return;

        const isCdtm = stationName === "CDTM";
        let nodeColor, label;

        if (isCdtm) {
            nodeColor = FIELD_COLORS["CDTM"];
            label = "CDTM";
        } else if (stationName.startsWith("High School")) {
            nodeColor = "#64748b";
            label = "High School";
        } else {
            const [degree, field] = stationName.split('|');
            nodeColor = FIELD_COLORS[field] || "#1e293b";
            label = `${degree}<br>${field}`;
        }

        const nodeSize = isCdtm ? Math.min(60, 20 + count * 0.05) : Math.min(40, 12 + count * 0.03);

        traces.push({
            x: [sx],
            y: [sy],
            mode: 'markers+text',
            marker: {
                size: nodeSize,
                color: nodeColor,
                line: { color: 'white', width: 2 }
            },
            text: label,
            textposition: sy > 4 ? "top center" : "bottom center",
            textfont: { size: isCdtm ? 11 : 9, color: nodeColor },
            hovertemplate: `<b>${stationName.replace('|', ' - ')}</b><br>${count} connections<extra></extra>`,
            showlegend: false
        });
    });

    const layout = {
        title: {
            text: "CDTM Alumni Education Pathways",
            x: 0.5,
            xanchor: 'center',
            font: { size: 24 }
        },
        xaxis: {
            range: [-0.5, 8.5],
            showgrid: false,
            showticklabels: false,
            zeroline: false
        },
        yaxis: {
            range: [-0.5, 9],
            showgrid: false,
            showticklabels: false,
            zeroline: false
        },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        height: 800,
        hovermode: 'closest',
        hoverdistance: 20,
        annotations: [
            {
                x: 0.5, y: -0.3,
                xref: 'x', yref: 'y',
                text: 'Pre-Undergrad',
                showarrow: false,
                font: { size: 10, color: '#666' }
            },
            {
                x: 1.5, y: -0.3,
                xref: 'x', yref: 'y',
                text: 'Undergraduate',
                showarrow: false,
                font: { size: 10, color: '#666' }
            },
            {
                x: 2.5, y: -0.3,
                xref: 'x', yref: 'y',
                text: 'Exchange',
                showarrow: false,
                font: { size: 10, color: '#666' }
            },
            {
                x: 4.0, y: -0.3,
                xref: 'x', yref: 'y',
                text: 'CDTM',
                showarrow: false,
                font: { size: 10, color: '#f59e0b', weight: 'bold' }
            },
            {
                x: 5.5, y: -0.3,
                xref: 'x', yref: 'y',
                text: 'Graduate',
                showarrow: false,
                font: { size: 10, color: '#666' }
            },
            {
                x: 7.5, y: -0.3,
                xref: 'x', yref: 'y',
                text: 'Doctorate',
                showarrow: false,
                font: { size: 10, color: '#666' }
            }
        ]
    };

    return { data: traces, layout };
}

// Update visualization
function updateVisualization() {
    console.log('Updating visualization with filters:', currentFilters);

    const filters = {
        field: currentFilters.field !== 'All' ? currentFilters.field : null,
        degree: currentFilters.degree !== 'All' ? currentFilters.degree : null
    };

    const paths = extractPaths(filters);
    console.log(`Extracted ${paths.length} paths`);

    const { data, layout } = createVisualization(paths);
    console.log(`Created ${data.length} traces`);

    const graphDiv = document.getElementById('graph');
    graphDiv.className = '';

    Plotly.newPlot(graphDiv, data, layout, { displayModeBar: true })
        .then(() => {
            console.log('Graph plotted successfully');

            // Update stats
            const total = paths.length;
            const withCdtm = paths.filter(p => p.has_cdtm).length;

            // Count fields
            const fieldCounts = {};
            paths.forEach(p => {
                fieldCounts[p.primary_field] = (fieldCounts[p.primary_field] || 0) + 1;
            });

            let fieldStats = Object.entries(fieldCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5)
                .map(([field, count]) => `${field}: ${count}`)
                .join(' | ');

            const statsHtml = total > 0
                ? `<strong>📊 Statistics:</strong> ${total} alumni paths shown (${withCdtm} include CDTM - ${Math.round(withCdtm/total*100)}%)<br><small>${fieldStats}</small>`
                : '<strong>📊 Statistics:</strong> No alumni paths match the selected filters';
            document.getElementById('stats').innerHTML = statsHtml;

            // Set up hover highlighting
            graphDiv.on('plotly_hover', handleHover);
            graphDiv.on('plotly_unhover', handleUnhover);
            graphDiv.on('plotly_click', handleClick);

            console.log('Event handlers attached');
        })
        .catch(err => {
            console.error('Error plotting:', err);
            document.getElementById('graph').innerHTML = `<div class="error">Error: ${err.message}</div>`;
        });
}

// Event handlers
function handleHover(eventData) {
    const point = eventData.points[0];
    if (!point.data.customdata || !point.data.customdata[0]) return;

    const pathId = point.data.customdata[0][0];
    console.log('Hover:', pathId);

    if (hoveredPath === pathId) return;
    hoveredPath = pathId;

    const graphDiv = document.getElementById('graph');
    const update = { opacity: [], 'line.width': [] };

    for (let i = 0; i < graphDiv.data.length; i++) {
        const trace = graphDiv.data[i];
        if (trace.mode === 'lines' && trace.customdata) {
            const tracePathId = trace.customdata[0][0];
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

    Plotly.restyle(graphDiv, update);
}

function handleUnhover() {
    if (hoveredPath === null) return;
    console.log('Unhover');
    hoveredPath = null;

    const graphDiv = document.getElementById('graph');
    const update = { opacity: [], 'line.width': [] };

    for (let i = 0; i < graphDiv.data.length; i++) {
        const trace = graphDiv.data[i];
        if (trace.mode === 'lines' && trace.customdata) {
            const originalAlpha = trace.customdata[0][2];
            update.opacity.push(originalAlpha);
            update['line.width'].push(2.5);
        } else {
            update.opacity.push(trace.opacity !== undefined ? trace.opacity : 1);
            update['line.width'].push(trace.marker ? trace.marker.size : 1);
        }
    }

    Plotly.restyle(graphDiv, update);
}

function handleClick(eventData) {
    const point = eventData.points[0];
    if (!point.data.customdata || !point.data.customdata[0]) return;

    const linkedinUrl = point.data.customdata[0][3];
    if (linkedinUrl) {
        console.log('Opening LinkedIn:', linkedinUrl);
        window.open(linkedinUrl, '_blank');
    }
}

// Filter handlers
function updateFilters() {
    currentFilters.field = document.getElementById('fieldFilter').value;
    currentFilters.degree = document.getElementById('degreeFilter').value;
    updateVisualization();
}

function resetFilters() {
    document.getElementById('fieldFilter').value = 'All';
    document.getElementById('degreeFilter').value = 'All';
    updateFilters();
}

// Initialize
async function init() {
    try {
        console.log('Loading data...');

        // Load CSV data
        const csvResponse = await fetch('data/educational_paths.csv');
        const csvText = await csvResponse.text();
        educationData = parseCSV(csvText);
        console.log(`Loaded ${educationData.length} education entries`);

        // Group by alumni
        groupedAlumni = groupByAlumni(educationData);
        const alumniCount = Object.keys(groupedAlumni).length;
        console.log(`Grouped into ${alumniCount} alumni profiles`);

        // Update subtitle
        document.getElementById('subtitle').textContent =
            `Interactive visualization of ${alumniCount} CDTM alumni education journeys`;

        // Set up event listeners
        document.getElementById('fieldFilter').addEventListener('change', updateFilters);
        document.getElementById('degreeFilter').addEventListener('change', updateFilters);

        // Create initial visualization
        updateVisualization();

    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('graph').innerHTML =
            `<div class="error"><strong>Error loading data:</strong> ${error.message}<br><br>Make sure you're serving this from a web server (not file://)</div>`;
        document.getElementById('stats').innerHTML =
            '<div class="error">Failed to load data. Please check the console for details.</div>';
    }
}

// Start the app
init();
