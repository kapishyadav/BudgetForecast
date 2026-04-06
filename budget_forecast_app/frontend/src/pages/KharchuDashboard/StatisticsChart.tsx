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
  granularity?: string;
}

const formatYAxis = (value: number) => {
  if (!value) return '$0';
  if (value >= 1000000000) return `$${(value / 1000000000).toFixed(1)}B`;
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}k`;
  return `$${value}`;
};

// 1. Tooltip Theme Fixed
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-card border border-border rounded-xl p-4 shadow-xl z-50 transition-colors duration-300">
        <p className="font-bold text-foreground mb-2 transition-colors duration-300">{label}</p>
        {payload.map((entry: any, index: number) => {
          if (entry.dataKey === 'confidenceBand') return null;

          // Note: entry.color comes from the Line stroke prop, which we dynamically set below!
          return (
            <p key={index} className="text-sm flex justify-between space-x-4" style={{ color: entry.color }}>
              <span className="font-semibold">{entry.name}:</span>
              <span className="text-foreground transition-colors duration-300">${Math.round(entry.value || 0).toLocaleString()}</span>
            </p>
          );
        })}
      </div>
    );
  }
  return null;
};

export function StatisticsChart({ forecast = [], historical = [], granularity = 'monthly' }: ChartProps) {

  const safeForecast = typeof forecast === 'string' ? JSON.parse(forecast) : forecast;
  const safeHistorical = typeof historical === 'string' ? JSON.parse(historical) : historical;

  const forecastArray = Array.isArray(safeForecast) ? safeForecast : [];
  const historicalArray = Array.isArray(safeHistorical) ? safeHistorical : [];

  const formattedData: any[] = [];
  let splitDateName = "";

  const formatDateKey = (ds: string) => {
    const date = new Date(ds);
    if (granularity === 'daily') {
      return date.toLocaleDateString('en-GB', {
          month: 'short',
          day: '2-digit',
          year: 'numeric'
      }).replace(/ /g, '-');
    }
    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  };

  historicalArray.forEach((item: any) => {
    if (!item.ds) return;
    const dateString = formatDateKey(item.ds);

    formattedData.push({
      name: dateString,
      actual: Number(item.y) || 0,
      predicted: null,
      confidenceBand: null,
    });
    splitDateName = dateString;
  });

  forecastArray.forEach((item: any) => {
    if (!item.ds || !item.yhat) return;
    const dateString = formatDateKey(item.ds);

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

  // 2. Empty State Theme Fixed
  if (formattedData.length === 0) {
    return (
      <div className="bg-card rounded-[24px] p-6 shadow-sm border border-border flex-1 flex items-center justify-center min-h-[400px] transition-colors duration-300">
        <p className="text-muted-foreground font-medium transition-colors duration-300">Waiting for forecast data...</p>
      </div>
    );
  }

  // 3. Main Chart Theme Fixed
  return (
    <div className="bg-card rounded-[24px] p-6 shadow-sm border border-border flex-1 flex flex-col transition-colors duration-300">

      {/* Chart Header & Legend */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-6 w-full">
          <div className="flex items-center space-x-2">
            <span className="p-2 bg-muted rounded-xl transition-colors duration-300">
              <BarChart2 size={20} className="text-muted-foreground transition-colors duration-300"/>
            </span>
            <h2 className="text-xl font-bold text-foreground transition-colors duration-300">Forecast Overview</h2>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-foreground transition-colors duration-300"></div>
              <span className="text-sm font-medium text-muted-foreground transition-colors duration-300">Historical</span>
            </div>
            <div className="flex items-center space-x-1.5">
              {/* Uses your lime green accent natively */}
              <div className="w-2.5 h-2.5 rounded-full bg-light-accent transition-colors duration-300"></div>
              <span className="text-sm font-medium text-muted-foreground transition-colors duration-300">Predicted</span>
            </div>
          </div>
        </div>
      </div>

      <div style={{ width: '100%', height: 400, position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={formattedData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>

            {/* 4. Chart SVG Gradients & Definitions */}
            <defs>
              <pattern id="diagonalHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                {/* Changed stroke to var(--muted) so the shading matches the theme */}
                <line x1="0" y1="0" x2="0" y2="8" stroke="var(--muted)" strokeWidth="4" />
              </pattern>
              <linearGradient id="colorBand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--light-accent)" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="var(--light-accent)" stopOpacity={0.05}/>
              </linearGradient>
            </defs>

            {/* 5. Chart Grid & Axes using CSS Variables */}
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />

            <XAxis dataKey="name" minTickGap={40} axisLine={false} tickLine={false} tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }} dy={10} />
            <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }} tickFormatter={formatYAxis} dx={-10} />

            <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--muted-foreground)', strokeWidth: 1, strokeDasharray: '5 5' }} />

            {splitDateName && (
              <>
                <ReferenceArea x1={splitDateName} fill="url(#diagonalHatch)" fillOpacity={1} />
                <ReferenceLine x={splitDateName} stroke="var(--foreground)" strokeWidth={1} strokeDasharray="3 3" />
              </>
            )}

            <Area type="monotone" dataKey="confidenceBand" stroke="none" fill="url(#colorBand)" />

            {/* 6. The Chart Lines! */}
            {/* Historical Line: Uses var(--foreground), with dots that match the card background to punch holes out! */}
            <Line
              type="monotone"
              dataKey="actual"
              stroke="var(--foreground)"
              strokeWidth={3}
              dot={{ r: 3, fill: 'var(--foreground)', strokeWidth: 2, stroke: 'var(--card)' }}
              activeDot={{ r: 6, fill: 'var(--foreground)', strokeWidth: 0 }}
              name="Actual"
              connectNulls
            />

            {/* Forecast Line: Uses var(--light-accent) */}
            <Line
              type="monotone"
              dataKey="predicted"
              stroke="var(--light-accent)"
              strokeWidth={3}
              strokeDasharray="5 5"
              dot={{ r: 3, fill: 'var(--light-accent)', strokeWidth: 2, stroke: 'var(--card)' }}
              activeDot={{ r: 6, fill: 'var(--light-accent)', strokeWidth: 0 }}
              name="Forecast"
              connectNulls
            />

          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}