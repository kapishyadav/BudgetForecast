import { BarChart2 } from 'lucide-react';
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
  Brush, // 1. Added Brush import
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

// Formatter function extracted to handle both XAxis and Tooltips
const formatTimestamp = (unixTime: number | string, granularity: string) => {
  const date = new Date(unixTime);
  if (granularity === 'daily') {
    return date.toLocaleDateString('en-GB', {
        month: 'short',
        day: '2-digit',
        year: 'numeric'
    }).replace(/ /g, '-');
  }
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
};

// 2. Updated Tooltip to handle numeric timestamp labels
const CustomTooltip = ({ active, payload, label, granularity }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-card border border-border rounded-xl p-4 shadow-xl z-50 transition-colors duration-300">
        <p className="font-bold text-foreground mb-2 transition-colors duration-300">
          {formatTimestamp(label, granularity)}
        </p>
        {payload.map((entry: any, index: number) => {
          if (entry.dataKey === 'confidenceBand') return null;

          return (
            <p key={index} className="text-sm flex justify-between space-x-4" style={{ color: entry.color }}>
              <span className="font-semibold">{entry.name}:</span>
              <span className="text-foreground transition-colors duration-300">
                ${Math.round(entry.value || 0).toLocaleString()}
              </span>
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
  let splitTimestamp: number | null = null; // Changed to hold numeric timestamp

  // 3. Map data using UNIX timestamps instead of string categories
  historicalArray.forEach((item: any) => {
    if (!item.ds) return;
    const timestamp = new Date(item.ds).getTime();

    formattedData.push({
      timestamp,
      actual: Number(item.y) || 0,
      predicted: null,
      confidenceBand: null,
    });
    splitTimestamp = timestamp; // Track the last historical point
  });

  forecastArray.forEach((item: any) => {
    if (!item.ds || !item.yhat) return;
    const timestamp = new Date(item.ds).getTime();

    const existingPoint = formattedData.find(d => d.timestamp === timestamp);

    if (existingPoint) {
      existingPoint.predicted = Number(item.yhat) || 0;
    } else {
      formattedData.push({
        timestamp,
        actual: null,
        predicted: Number(item.yhat) || 0,
        confidenceBand: item.yhat_lower ? [Number(item.yhat_lower), Number(item.yhat_upper)] : null,
      });
    }
  });

  // Sort data by timestamp just to be safe for continuous scaling
  formattedData.sort((a, b) => a.timestamp - b.timestamp);

  if (formattedData.length === 0) {
    return (
      <div className="bg-card rounded-[24px] p-6 shadow-sm border border-border flex-1 flex items-center justify-center min-h-[400px] transition-colors duration-300">
        <p className="text-muted-foreground font-medium transition-colors duration-300">Waiting for forecast data...</p>
      </div>
    );
  }

  // 4. Calculate default zoom for Brush (e.g., zoom in on the last 60 points if daily)
  const dataLength = formattedData.length;
  const brushStartIndex = granularity === 'daily' ? Math.max(0, dataLength - 60) : 0;

  return (
    <div className="bg-card rounded-[24px] p-6 shadow-sm border border-border flex-1 flex flex-col transition-colors duration-300">

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
              <div className="w-2.5 h-2.5 rounded-full bg-light-accent transition-colors duration-300"></div>
              <span className="text-sm font-medium text-muted-foreground transition-colors duration-300">Predicted</span>
            </div>
          </div>
        </div>
      </div>

      <div style={{ width: '100%', height: 400, position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={formattedData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>

            <defs>
              <pattern id="diagonalHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                <line x1="0" y1="0" x2="0" y2="8" stroke="var(--muted)" strokeWidth="4" />
              </pattern>
              <linearGradient id="colorBand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--light-accent)" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="var(--light-accent)" stopOpacity={0.05}/>
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />

            {/* 5. Update XAxis to scale continuously over time */}
            <XAxis
              dataKey="timestamp"
              type="number"
              scale="time"
              domain={['dataMin', 'dataMax']}
              minTickGap={40}
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
              dy={10}
              tickFormatter={(unixTime) => formatTimestamp(unixTime, granularity)}
            />

            <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }} tickFormatter={formatYAxis} dx={-10} />

            <Tooltip
              content={<CustomTooltip granularity={granularity} />}
              cursor={{ stroke: 'var(--muted-foreground)', strokeWidth: 1, strokeDasharray: '5 5' }}
            />

            {/* 6. Update References to use the numeric timestamp */}
            {splitTimestamp && (
              <>
                <ReferenceArea
                  x1={splitTimestamp}
                  fill="var(--muted)"
                  fillOpacity={0.10}
                  strokeOpacity={0.3}
                />
                <ReferenceLine x={splitTimestamp} stroke="var(--foreground)" strokeWidth={1} strokeDasharray="3 3" />
              </>
            )}

            <Area type="monotone" dataKey="confidenceBand" stroke="none" fill="url(#colorBand)" />

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

            {/* 7. Added the Brush component for zooming/panning */}
            <Brush
              dataKey="timestamp"
              height={30}
              stroke="var(--foreground)"
              fill="var(--card)"
              tickFormatter={(unixTime) => formatTimestamp(unixTime, granularity)}
              startIndex={brushStartIndex}
            />

          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}