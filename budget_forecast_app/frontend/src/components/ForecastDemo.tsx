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
        <h2 className="text-3xl font-bold text-[#1A1A1A] tracking-tight mb-3">
          Forecast Preview
        </h2>
        <p className="text-gray-500 text-sm max-w-xl mx-auto">
          Visualize historical spending alongside predicted future trends.
        </p>
      </div>

      {/* Main Card */}
      <div className="bg-white rounded-[24px] p-8 shadow-sm border border-gray-50">

        {/* Top Section */}
        <div className="mb-8 flex justify-between items-center flex-wrap gap-4">
          <div>
            <h3 className="text-lg font-semibold text-[#1A1A1A]">
              AWS Budget Forecast - 2024
            </h3>
            <p className="text-sm text-gray-500">
              Historical vs forecasted spending
            </p>
          </div>

          <div className="text-sm font-semibold text-gray-400 bg-gray-50 px-4 py-2 rounded-full">
            Real-time
          </div>
        </div>

        {/* Chart */}
        <div ref={chartContainerRef} className="w-full min-h-[400px]">
          <AreaChart width={chartWidth} height={400} data={historicalData}>
            <defs>
              <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#1A1A1A" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#1A1A1A" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#9CA3AF" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#9CA3AF" stopOpacity={0.05} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
            <XAxis dataKey="month" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />

            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #E5E7EB',
                borderRadius: '12px',
              }}
              formatter={(value: number) => `$${value}`}
            />

            <Legend />

            <Area
              type="monotone"
              dataKey="actual"
              stroke="#1A1A1A"
              fill="url(#colorActual)"
              strokeWidth={2}
              name="Actual"
              dot={{ r: 3 }}
            />

            <Area
              type="monotone"
              dataKey="forecast"
              stroke="#9CA3AF"
              fill="url(#colorForecast)"
              strokeWidth={2}
              strokeDasharray="5 5"
              name="Forecast"
              dot={{ r: 3 }}
            />
          </AreaChart>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">

          <div className="bg-gray-50 p-5 rounded-xl border border-gray-100">
            <p className="text-xs font-semibold text-gray-500 mb-1 uppercase">
              Current Month
            </p>
            <p className="text-xl font-bold text-[#1A1A1A]">
              $6,200
            </p>
            <p className="text-xs text-gray-400 mt-1">
              ↓ 5% vs last month
            </p>
          </div>

          <div className="bg-gray-50 p-5 rounded-xl border border-gray-100">
            <p className="text-xs font-semibold text-gray-500 mb-1 uppercase">
              Next Month
            </p>
            <p className="text-xl font-bold text-[#1A1A1A]">
              $6,500
            </p>
            <p className="text-xs text-gray-400 mt-1">
              ↑ 4.8% predicted
            </p>
          </div>

          <div className="bg-gray-50 p-5 rounded-xl border border-gray-100">
            <p className="text-xs font-semibold text-gray-500 mb-1 uppercase">
              6-Month Forecast
            </p>
            <p className="text-xl font-bold text-[#1A1A1A]">
              $7,600
            </p>
            <p className="text-xs text-gray-400 mt-1">
              95% confidence interval
            </p>
          </div>

        </div>

      </div>
    </div>
  );
}