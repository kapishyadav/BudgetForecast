import { useState, useEffect, useRef } from 'react';
import { XAxis, YAxis, CartesianGrid, Tooltip, Legend, Area, AreaChart } from 'recharts';

const historicalData = [
  { month: 'Jan', actual: 4500, forecast: null },
  { month: 'Feb', actual: 4800, forecast: null },
  { month: 'Mar', actual: 5200, forecast: null },
  { month: 'Apr', actual: 4900, forecast: null },
  { month: 'May', actual: 5400, forecast: null },
  { month: 'Jun', actual: 5800, forecast: null },
  { month: 'Jul', actual: 6200, forecast: 6200 },
  { month: 'Aug', actual: null, forecast: 6500 },
  { month: 'Sep', actual: null, forecast: 6800 },
  { month: 'Oct', actual: null, forecast: 7100 },
  { month: 'Nov', actual: null, forecast: 7400 },
  { month: 'Dec', actual: null, forecast: 7600 },
];

export function ForecastDemo() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [chartWidth, setChartWidth] = useState(800);

  useEffect(() => {
    function updateWidth() {
      if (chartContainerRef.current) {
        setChartWidth(chartContainerRef.current.offsetWidth);
      }
    }
    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-20">

      {/* Header */}
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-foreground tracking-tight mb-3 transition-colors">
          Forecast Preview
        </h2>
        <p className="text-muted-foreground text-sm max-w-xl mx-auto transition-colors">
          Visualize historical spending alongside predicted future trends.
        </p>
      </div>

      {/* Main Card */}
      <div className="bg-card rounded-[24px] p-8 shadow-sm border border-border transition-colors">

        {/* Top Section */}
        <div className="mb-8 flex justify-between items-center flex-wrap gap-4">
          <div>
            <h3 className="text-lg font-semibold text-card-foreground transition-colors">
              AWS Budget Forecast - 2024
            </h3>
            <p className="text-sm text-muted-foreground transition-colors">
              Historical vs forecasted spending
            </p>
          </div>

          {/* Using your custom light-accent (Lime Green) for the badge! */}
          <div className="text-sm font-semibold text-[#09090B] bg-light-accent px-4 py-2 rounded-full transition-colors">
            Real-time
          </div>
        </div>

        {/* Chart */}
        <div ref={chartContainerRef} className="w-full min-h-[400px]">
          <AreaChart width={chartWidth} height={400} data={historicalData}>
            <defs>
              <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                {/* Removed hsl(), using var() directly since your variables are hex codes */}
                <stop offset="5%" stopColor="var(--foreground)" stopOpacity={0.4} />
                <stop offset="95%" stopColor="var(--foreground)" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--muted-foreground)" stopOpacity={0.4} />
                <stop offset="95%" stopColor="var(--muted-foreground)" stopOpacity={0.05} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="month" stroke="var(--muted-foreground)" />
            <YAxis stroke="var(--muted-foreground)" />

            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--card)',
                border: '1px solid var(--border)',
                borderRadius: '12px',
                color: 'var(--card-foreground)'
              }}
              formatter={(value: number) => `$${value}`}
            />

            <Legend wrapperStyle={{ color: 'var(--foreground)' }} />

            <Area
              type="monotone"
              dataKey="actual"
              stroke="var(--foreground)"
              fill="url(#colorActual)"
              strokeWidth={2}
              name="Actual"
              dot={{ r: 3, fill: 'var(--background)', stroke: 'var(--foreground)', strokeWidth: 2 }}
            />

            <Area
              type="monotone"
              dataKey="forecast"
              stroke="var(--muted-foreground)"
              fill="url(#colorForecast)"
              strokeWidth={2}
              strokeDasharray="5 5"
              name="Forecast"
              dot={{ r: 3, fill: 'var(--background)', stroke: 'var(--muted-foreground)', strokeWidth: 2 }}
            />
          </AreaChart>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">

          <div className="bg-muted p-5 rounded-xl border border-border transition-colors">
            <p className="text-xs font-semibold text-muted-foreground mb-1 uppercase transition-colors">
              Current Month
            </p>
            <p className="text-xl font-bold text-foreground transition-colors">
              $6,200
            </p>
            <p className="text-xs text-muted-foreground mt-1 transition-colors">
              ↓ 5% vs last month
            </p>
          </div>

          <div className="bg-muted p-5 rounded-xl border border-border transition-colors">
            <p className="text-xs font-semibold text-muted-foreground mb-1 uppercase transition-colors">
              Next Month
            </p>
            <p className="text-xl font-bold text-foreground transition-colors">
              $6,500
            </p>
            <p className="text-xs text-muted-foreground mt-1 transition-colors">
              ↑ 4.8% predicted
            </p>
          </div>

          <div className="bg-muted p-5 rounded-xl border border-border transition-colors">
            <p className="text-xs font-semibold text-muted-foreground mb-1 uppercase transition-colors">
              6-Month Forecast
            </p>
            <p className="text-xl font-bold text-foreground transition-colors">
              $7,600
            </p>
            <p className="text-xs text-muted-foreground mt-1 transition-colors">
              95% confidence interval
            </p>
          </div>

        </div>

      </div>
    </div>
  );
}