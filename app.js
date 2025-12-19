// CDTM Alumni Education Path Visualization
// Pure JavaScript implementation

// Global state
let alumniData = [];
let schoolsData = {};
let currentFilters = { field: 'All', degree: 'All' };
let hoveredPath = null;

// Field colors
const FIELD_COLORS = {
    "Engineering/Tech": "#3b82f6",
    "Business": "#ef4444",
    "Sciences": "#10b981",
    "Other": "#94a3b8",
    "CDTM": "#f59e0b"
};

// Station positions
const STATIONS = {
    "CDTM": [3.0, 4.0],
    "Bachelor's|Engineering/Tech": [0.5, 6.5],
    "Bachelor's|Business": [0.5, 5.0],
    "Bachelor's|Sciences": [0.5, 3.5],
    "Bachelor's|Other": [0.5, 2.0],
    "Diploma|Engineering/Tech": [1.5, 6.0],
    "Diploma|Business": [1.5, 4.5],
    "Diploma|Other": [1.5, 3.0],
    "Master's|Engineering/Tech": [5.0, 6.5],
    "Master's|Business": [5.0, 5.0],
    "Master's|Sciences": [5.0, 3.5],
    "Master's|Other": [5.0, 2.0],
    "Doctorate|Engineering/Tech": [7.0, 6.0],
    "Doctorate|Business": [7.0, 4.5],
    "Doctorate|Sciences": [7.0, 3.0],
    "Doctorate|Other": [7.0, 1.5]
};

// Utility functions
function categorizeDegree(degree, field) {
    if (!degree) return "Other";
    const degreeLower = degree.toLowerCase();

    if (/(bachelor|b\.sc|b\.a|b\.eng|bsc)/i.test(degreeLower)) return "Bachelor's";
    if (/(master|m\.sc|m\.a|m\.eng|msc|mba)/i.test(degreeLower)) return "Master's";
    if (/(phd|ph\.d|doctor|doctorate)/i.test(degreeLower)) return "Doctorate";
    if (/(dipl|diploma)/i.test(degreeLower)) return "Diploma";

    return "Other";
}

function categorizeField(field) {
    if (!field) return "Other";
    const fieldLower = field.toLowerCase();

    const engineeringKeywords = ['engineering', 'computer science', 'informatics', 'technology', 'cs', 'electrical', 'mechanical'];
    const businessKeywords = ['business', 'management', 'economics', 'mba', 'finance', 'marketing'];
    const scienceKeywords = ['science', 'physics', 'chemistry', 'biology', 'mathematics', 'math'];

    if (engineeringKeywords.some(kw => fieldLower.includes(kw))) return "Engineering/Tech";
    if (businessKeywords.some(kw => fieldLower.includes(kw))) return "Business";
    if (scienceKeywords.some(kw => fieldLower.includes(kw))) return "Sciences";

    return "Other";
}

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

// Extract paths from alumni data
function extractPaths(filters = {}) {
    const paths = [];

    alumniData.forEach(person => {
        const educationPath = person.education_path || [];
        if (educationPath.length === 0) return;

        const allEntries = [];
        let cdtmLevel = null;

        // Process education entries
        educationPath.forEach((entry, idx) => {
            const institution = entry.institution || '';
            const degree = entry.degree_name || '';
            const field = entry.field_of_study || '';

            // Check for CDTM
            if (institution.toUpperCase().includes('CDTM') ||
                institution.toUpperCase().includes('CENTER FOR DIGITAL TECHNOLOGY')) {
                cdtmLevel = idx;
                return;
            }

            const categorizedDegree = categorizeDegree(degree, field);
            const categorizedField = categorizeField(field);

            // Apply filters
            if (filters.field && categorizedField !== filters.field) return;
            if (filters.degree && categorizedDegree !== filters.degree) return;

            allEntries.push({
                degree: categorizedDegree,
                field: categorizedField,
                institution: institution,
                is_cdtm: false
            });
        });

        if (allEntries.length === 0) return;

        // Insert CDTM node
        if (cdtmLevel !== null) {
            const bachelorIdx = allEntries.findIndex(e =>
                e.degree === "Bachelor's" || e.degree === "Diploma"
            );

            let insertIdx;
            if (bachelorIdx !== -1) {
                insertIdx = bachelorIdx + 1;
            } else {
                const masterIdx = allEntries.findIndex(e => e.degree === "Master's");
                insertIdx = masterIdx !== -1 ? masterIdx + 1 : 1;
            }

            allEntries.splice(Math.min(insertIdx, allEntries.length), 0, {
                degree: 'CDTM',
                field: 'CDTM',
                institution: 'CDTM',
                is_cdtm: true,
                cdtm_level: cdtmLevel
            });
        }

        // Determine primary field
        let primaryField = "Other";
        for (const entry of allEntries) {
            if (entry.field !== "Other" && !entry.is_cdtm) {
                primaryField = entry.field;
                break;
            }
        }

        if (allEntries.length >= 2) {
            paths.push({
                nodes: allEntries,
                primary_field: primaryField,
                name: person.full_name || 'Unknown',
                headline: person.headline || '',
                linkedin_url: person.linkedin_url || ''
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

            // Add jitter
            const yJitterStart = (Math.random() - 0.5) * 0.2;
            const yJitterEnd = (Math.random() - 0.5) * 0.2;

            const curve = sigmoidCurve(x1, y1 + yJitterStart, x2, y2 + yJitterEnd);

            const lineColor = (current.is_cdtm || next.is_cdtm) ? FIELD_COLORS["CDTM"] : color;
            const lineAlpha = (current.is_cdtm || next.is_cdtm) ? 0.3 : 0.2;

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

            stationCounts[currentKey]++;
            stationCounts[nextKey]++;
        }
    });

    // Draw nodes
    Object.entries(STATIONS).forEach(([stationName, [sx, sy]]) => {
        const count = stationCounts[stationName] || 0;
        if (count === 0) return;

        const isCdtm = stationName === "CDTM";
        const nodeColor = isCdtm ? FIELD_COLORS["CDTM"] : "#1e293b";
        const nodeSize = isCdtm ? Math.min(50, 15 + count * 0.03) : Math.min(30, 10 + count * 0.02);
        const label = isCdtm ? "CDTM" : stationName.split('|').join('<br>');

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
            textposition: sy > 3.5 ? "top center" : "bottom center",
            textfont: { size: isCdtm ? 10 : 8, color: nodeColor },
            hovertemplate: `<b>${label}</b><br>${count} alumni<extra></extra>`,
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
            range: [-0.5, 8],
            showgrid: false,
            showticklabels: false,
            zeroline: false
        },
        yaxis: {
            range: [-0.5, 8],
            showgrid: false,
            showticklabels: false,
            zeroline: false
        },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        height: 800,
        hovermode: 'closest',
        hoverdistance: 20
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
            const withCdtm = paths.filter(p => p.nodes.some(n => n.is_cdtm)).length;
            const statsHtml = total > 0
                ? `<strong>📊 Statistics:</strong> ${total} alumni paths shown (${withCdtm} include CDTM - ${Math.round(withCdtm/total*100)}%)`
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

        // Load alumni data
        const alumniResponse = await fetch('data/cdtm_alumni_consolidated.json');
        alumniData = await alumniResponse.json();
        console.log(`Loaded ${alumniData.length} alumni profiles`);

        // Load schools data
        const schoolsResponse = await fetch('data/unique_schools_normalized.json');
        schoolsData = await schoolsResponse.json();
        console.log(`Loaded ${Object.keys(schoolsData).length} schools`);

        // Update subtitle
        document.getElementById('subtitle').textContent =
            `Interactive visualization of ${alumniData.length} CDTM alumni education journeys`;

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
