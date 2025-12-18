// Hover highlighting for education path visualization
(function() {
    'use strict';

    var hoveredPath = null;
    var unhoverTimeout = null;

    function setupHoverListeners() {
        var graphDiv = document.getElementById('flow-diagram');

        if (!graphDiv) {
            // Graph not loaded yet, try again
            setTimeout(setupHoverListeners, 100);
            return;
        }

        var plotlyGraph = graphDiv._fullLayout ? graphDiv : null;

        if (!plotlyGraph) {
            // Plotly not fully initialized, try again
            setTimeout(setupHoverListeners, 100);
            return;
        }

        console.log('Setting up hover listeners for path highlighting');

        graphDiv.on('plotly_hover', function(data) {
            // Clear any pending unhover timeout
            if (unhoverTimeout) {
                clearTimeout(unhoverTimeout);
                unhoverTimeout = null;
            }

            var point = data.points[0];
            if (!point.data.customdata || !point.data.customdata[0]) return;

            var pathId = point.data.customdata[0][0];
            if (hoveredPath === pathId) return;

            hoveredPath = pathId;

            var update = {opacity: [], 'line.width': []};
            for (var i = 0; i < graphDiv.data.length; i++) {
                var trace = graphDiv.data[i];
                if (trace.mode === 'lines' && trace.customdata) {
                    var tracePathId = trace.customdata[0][0];
                    if (tracePathId === pathId) {
                        update.opacity.push(0.9);
                        update['line.width'].push(4);
                    } else {
                        update.opacity.push(0.05);
                        update['line.width'].push(1.5);
                    }
                } else {
                    update.opacity.push(trace.opacity !== undefined ? trace.opacity : 1);
                    update['line.width'].push(trace.line ? trace.line.width : 1);
                }
            }
            Plotly.restyle(graphDiv, update);
        });

        graphDiv.on('plotly_unhover', function(data) {
            // Add delay before unhover to allow clicking on LinkedIn links
            if (unhoverTimeout) {
                clearTimeout(unhoverTimeout);
            }

            unhoverTimeout = setTimeout(function() {
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
                        update['line.width'].push(trace.line ? trace.line.width : 1);
                    }
                }
                Plotly.restyle(graphDiv, update);
                unhoverTimeout = null;
            }, 300); // 300ms delay allows clicking on LinkedIn links
        });
    }

    // Start trying to set up listeners once DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupHoverListeners);
    } else {
        setupHoverListeners();
    }

    // Also set up after any Dash callback (graph might be re-rendered)
    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                setupHoverListeners();
            }
        });
    });

    // Observe the entire document for changes
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();
