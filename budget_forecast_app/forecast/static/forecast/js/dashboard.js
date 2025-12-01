const forecastData = window.forecastData || [];
const historicalData = window.historicalData || [];
console.log("DEBUG forecastData:", forecastData);
console.log("DEBUG historicalData:", historicalData);

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

// --- Determine forecast start for shading + vertical line ---
const forecastStartDate = forecastDates[0];

// --- Chart.js Plugins ---
const forecastLinePlugin = {
    id: "forecastLine",
    afterDraw(chart) {
        const xScale = chart.scales.x;
        const ctx = chart.ctx;

        if (!xScale.getPixelForValue(forecastStartDate)) return;

        const x = xScale.getPixelForValue(forecastStartDate);

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

Chart.register(forecastLinePlugin);
Chart.register(forecastRegionPlugin);

const ctx = document.getElementById('forecastChart').getContext('2d');

new Chart(ctx, {
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
                fill: "+1",  // Fill area between lower and upper
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