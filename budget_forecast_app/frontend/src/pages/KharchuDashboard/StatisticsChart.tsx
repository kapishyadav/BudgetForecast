import { BarChart2, ChevronDown } from 'lucide-react';
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
  ReferenceLine,
} from 'recharts';

interface ChartProps {
  forecast: any[];
  historical: any[];
}

const formatYAxis = (value: number) => {
  if (!value) return '$0';
  if (value >= 1000000000) return `$${(value / 1000000000).toFixed(1)}B`;
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}k`;
  return `$${value}`;
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border-2 border-[#1A1A1A] rounded-xl p-4 shadow-xl z-50">
        <p className="font-bold text-[#1A1A1A] mb-2">{label}</p>
        {payload.map((entry: any, index: number) => {
          if (entry.dataKey === 'confidenceBand') return null;
          return (
            <p key={index} className="text-sm flex justify-between space-x-4" style={{ color: entry.color }}>
              <span className="font-semibold">{entry.name}:</span>
              <span>${Math.round(entry.value || 0).toLocaleString()}</span>
            </p>
          );
        })}
      </div>
    );
  }
  return null;
};

export function StatisticsChart({ forecast = [], historical = [] }: ChartProps) {

  // Safely parse data
  const safeForecast = typeof forecast === 'string' ? JSON.parse(forecast) : forecast;
  const safeHistorical = typeof historical === 'string' ? JSON.parse(historical) : historical;

  const forecastArray = Array.isArray(safeForecast) ? safeForecast : [];
  const historicalArray = Array.isArray(safeHistorical) ? safeHistorical : [];

  const formattedData: any[] = [];
  let splitDateName = "";

  // Format Historical
  historicalArray.forEach((item: any) => {
    if (!item.ds) return;
    const dateString = new Date(item.ds).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

    formattedData.push({
      name: dateString,
      actual: Number(item.y) || 0, // Force to be a number
      predicted: null,
      confidenceBand: null,
    });
    splitDateName = dateString;
  });

  // Format Forecast
  forecastArray.forEach((item: any) => {
    if (!item.ds || !item.yhat) return;
    const dateString = new Date(item.ds).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

    const existingPoint = formattedData.find(d => d.name === dateString);

    if (existingPoint) {
      existingPoint.predicted = Number(item.yhat) || 0;
    } else {
      formattedData.push({
        name: dateString,
        actual: null,
        predicted: Number(item.yhat) || 0,
        confidenceBand: item.yhat_lower ? [Number(item.yhat_lower), Number(item.yhat_upper)] : null,
      });
    }
  });

  // Show a loading/empty state if data isn't mapped properly
  if (formattedData.length === 0) {
    return (
      <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 flex-1 flex items-center justify-center min-h-[400px]">
        <p className="text-gray-400 font-medium">Waiting for forecast data...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 flex-1 flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-6 w-full">
          <div className="flex items-center space-x-2">
            <span className="p-2 bg-gray-50 rounded-xl"><BarChart2 size={20} className="text-gray-500"/></span>
            <h2 className="text-xl font-bold text-[#1A1A1A]">Forecast Overview</h2>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-[#1A1A1A]"></div>
              <span className="text-sm font-medium text-gray-600">Historical</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-[#C6D82F]"></div>
              <span className="text-sm font-medium text-gray-600">Predicted</span>
            </div>
          </div>
        </div>
      </div>

      {/* CRITICAL FIX: The wrapper div MUST have a strict height, otherwise ResponsiveContainer collapses */}
      <div style={{ width: '100%', height: 400, position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={formattedData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <defs>
              <pattern id="diagonalHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                <line x1="0" y1="0" x2="0" y2="8" stroke="#f9fafb" strokeWidth="4" />
              </pattern>
              <linearGradient id="colorBand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#C6D82F" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#C6D82F" stopOpacity={0.05}/>
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />

            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} dy={10} />
            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} tickFormatter={formatYAxis} dx={-10} />

            <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#9CA3AF', strokeWidth: 1, strokeDasharray: '5 5' }} />

            {splitDateName && (
              <>
                <ReferenceArea x1={splitDateName} fill="url(#diagonalHatch)" fillOpacity={1} />
                <ReferenceLine x={splitDateName} stroke="#1A1A1A" strokeWidth={1} strokeDasharray="3 3" />
              </>
            )}

            <Area type="monotone" dataKey="confidenceBand" stroke="none" fill="url(#colorBand)" />

            <Line type="monotone" dataKey="actual" stroke="#1A1A1A" strokeWidth={3} dot={{ r: 3, fill: '#1A1A1A', strokeWidth: 2, stroke: 'white' }} activeDot={{ r: 6, fill: '#1A1A1A', strokeWidth: 0 }} name="Actual" connectNulls />
            <Line type="monotone" dataKey="predicted" stroke="#C6D82F" strokeWidth={3} strokeDasharray="5 5" dot={{ r: 3, fill: '#C6D82F', strokeWidth: 2, stroke: 'white' }} activeDot={{ r: 6, fill: '#C6D82F', strokeWidth: 0 }} name="Forecast" connectNulls />

          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}