// 1. Global variable to track the chart instance across HTMX loads
let forecastChartInstance = null;

// --- Chart.js Plugins (Defined globally) ---
const forecastLinePlugin = {
    id: "forecastLine",
    afterDraw(chart) {
        // Find the forecast start date dynamically from the datasets
        const forecastDates = window.forecastData ? window.forecastData.map(d => d.ds) : [];
        if (forecastDates.length === 0) return;

        const forecastStartDate = forecastDates[0];
        const xScale = chart.scales.x;
        const ctx = chart.ctx;

        const x = xScale.getPixelForValue(forecastStartDate);
        if (!x) return;

        ctx.save();
        ctx.strokeStyle = "red";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(x, chart.chartArea.top);
        ctx.lineTo(x, chart.chartArea.bottom);
        ctx.stroke();
        ctx.restore();
    }
};

const forecastRegionPlugin = {
    id: "forecastRegion",
    beforeDraw(chart) {
        const forecastDates = window.forecastData ? window.forecastData.map(d => d.ds) : [];
        if (forecastDates.length === 0) return;

        const forecastStartDate = forecastDates[0];
        const xScale = chart.scales.x;
        const ctx = chart.ctx;

        const startX = xScale.getPixelForValue(forecastStartDate);
        if (!startX) return;

        const chartArea = chart.chartArea;
        const endX = chartArea.right;

        ctx.save();
        ctx.fillStyle = "rgba(200, 200, 200, 0.15)";
        ctx.fillRect(startX, chartArea.top, endX - startX, chartArea.bottom - chartArea.top);
        ctx.restore();
    }
};

// Register plugins once
Chart.register(forecastLinePlugin);
Chart.register(forecastRegionPlugin);


// 2. Wrap the chart creation in a function so HTMX can trigger it
function initializeForecastChart() {
    const forecastData = window.forecastData || [];
    const historicalData = window.historicalData || [];
    console.log("DEBUG forecastData:", forecastData);
    console.log("DEBUG historicalData:", historicalData);

    if (forecastData.length === 0 && historicalData.length === 0) {
        console.warn("No data available to render chart.");
        return;
    }

    // --- Extract Historical Data ---
    const historyDates = historicalData.map(d => d.ds);
    const historyValues = historicalData.map(d => d.y);

    const forecastDates = forecastData.map(d => d.ds);
    const yhat = forecastData.map(d => d.yhat);
    const yhatLower = forecastData.map(d => d.yhat_lower);
    const yhatUpper = forecastData.map(d => d.yhat_upper);

    // --- Unified X-axis Labels ---
    const labels = [...historyDates, ...forecastDates];

    // --- Align forecast to start after history ---
    const emptyHistoryPad = Array(historyDates.length).fill(null);

    // Get the canvas element safely
    const canvas = document.getElementById('forecastChart');
    if (!canvas) {
        console.error("Canvas element #forecastChart not found.");
        return;
    }

    const ctx = canvas.getContext('2d');

    // 3. CRITICAL FIX FOR HTMX: Destroy the old chart if it exists
    if (forecastChartInstance !== null) {
        forecastChartInstance.destroy();
    }

    // 4. Create the new chart and assign it to the global tracker
    forecastChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                // --- Historical Actuals ---
                {
                    label: 'Historical (Actual)',
                    data: historyValues,
                    borderColor: '#6b4a2b',
                    backgroundColor: 'rgba(107, 74, 43, 0.1)',
                    tension: 0.3,
                    pointRadius: 2
                },

                // --- Forecast (yhat) ---
                {
                    label: 'Forecast (yhat)',
                    data: [...emptyHistoryPad, ...yhat],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.3,
                    pointRadius: 2,
                    fill: false
                },

                // --- Confidence Band (Lower) ---
                {
                    label: 'Lower Bound (yhat_lower)',
                    data: [...emptyHistoryPad, ...yhatLower],
                    borderColor: 'rgba(255, 99, 132, 0.6)',
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0
                },

                // --- Confidence Band (Upper) ---
                {
                    label: 'Upper Bound (yhat_upper)',
                    data: [...emptyHistoryPad, ...yhatUpper],
                    borderColor: 'rgba(75, 192, 192, 0.6)',
                    borderDash: [5, 5],
                    backgroundColor: 'rgba(0, 200, 0, 0.1)',
                    fill: "-1",  // FIXED: Fills down to the Lower Bound dataset
                    tension: 0.3,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Historical + Forecast Plot',
                    font: { size: 18 }
                },
                legend: {
                    position: 'bottom',
                },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.dataset.label}: ${context.parsed.y.toFixed(2)}`
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    },
                    ticks: {
                        maxTicksLimit: 12,
                        autoSkip: true
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Forecast Value'
                    },
                    beginAtZero: false
                }
            }
        }
    });
}

// 5. Execute immediately upon script load
// When HTMX injects the dashboard partial, this script tag runs and fires this function.
initializeForecastChart();