import { BarChart2, PieChart, ChevronDown } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
  ReferenceLine,
} from 'recharts';

const data = [
  { name: 'Jun 2025', opex: 9000000, capex: 4800000, isFuture: false },
  { name: 'Jul 2025', opex: 7500000, capex: 4200000, isFuture: false },
  { name: 'Aug 2025', opex: 5500000, capex: 2800000, isFuture: false },
  { name: 'Sep 2025', opex: 8200000, capex: 2200000, isFuture: false },
  { name: 'Oct 2025', opex: 6500000, capex: 4500000, isFuture: false },
  { name: 'Nov 2025', opex: 8700000, capex: 3200000, isFuture: false, isNow: true },
  { name: 'Dec 2025', opex: 5800000, capex: 2500000, isFuture: true },
  { name: 'Jan 2026', opex: 6800000, capex: 3800000, isFuture: true },
  { name: 'Feb 2026', opex: 7800000, capex: 4200000, isFuture: true },
  { name: 'Mar 2026', opex: 6000000, capex: 3000000, isFuture: true },
];

const formatYAxis = (tickItem: number) => {
  if (tickItem === 0) return '$0';
  return `$${tickItem / 1000000}M`;
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border-2 border-[#1A1A1A] rounded-xl p-4 shadow-xl translate-y-[-50px]">
        <p className="font-bold text-[#1A1A1A] mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            <span className="font-semibold">{entry.name}:</span> ${entry.value.toLocaleString()}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export function StatisticsChart() {
  return (
    <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 flex-1 flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-6 w-full">
          <div className="flex items-center space-x-2">
            <span className="p-2 bg-gray-50 rounded-xl"><BarChart2 size={20} className="text-gray-500"/></span>
            <h2 className="text-xl font-bold text-[#1A1A1A]">Statistics</h2>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-[#1A1A1A]"></div>
              <span className="text-sm font-medium text-gray-600">OpEx</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-[#C6D82F]"></div>
              <span className="text-sm font-medium text-gray-600">CapEx</span>
            </div>
          </div>
          
          <div className="flex-1"></div>
          
          <button className="flex items-center space-x-2 text-sm font-medium text-gray-700 bg-gray-50 px-4 py-2 rounded-xl hover:bg-gray-100 transition-colors border border-gray-100">
            <span>2025</span>
            <ChevronDown size={14} />
          </button>
        </div>
      </div>

      <div className="flex justify-between items-center mb-2 px-12 text-xs font-semibold text-gray-500 uppercase tracking-widest relative z-10 w-full">
        <div className="w-1/3 text-center">Previous Data</div>
        <div className="w-1/3 text-center">NOW</div>
        <div className="w-1/3 text-center text-gray-400">Future Predictions</div>
      </div>

      <div className="flex-1 w-full relative" style={{ minHeight: '350px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
            <defs>
              <pattern id="diagonalHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                <line x1="0" y1="0" x2="0" y2="8" stroke="#f3f4f6" strokeWidth="4" />
              </pattern>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} dy={10} />
            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} tickFormatter={formatYAxis} dx={-10} domain={[0, 10000000]} ticks={[0, 2000000, 4000000, 6000000, 8000000, 10000000]} />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#9CA3AF', strokeWidth: 1, strokeDasharray: '5 5' }} />
            
            <ReferenceArea x1="Nov 2025" x2="Mar 2026" fill="url(#diagonalHatch)" fillOpacity={1} />
            <ReferenceLine x="Nov 2025" stroke="#1A1A1A" strokeWidth={1} />

            {/* OpEx Lines */}
            <Line
              type="monotone"
              dataKey="opex"
              stroke="#1A1A1A"
              strokeWidth={3}
              dot={{ r: 4, fill: '#1A1A1A', strokeWidth: 2, stroke: 'white' }}
              activeDot={{ r: 8, fill: '#1A1A1A', strokeWidth: 0 }}
              name="OpEx"
            />

            {/* CapEx Lines */}
            <Line
              type="monotone"
              dataKey="capex"
              stroke="#C6D82F" // The yellow/green brand color
              strokeWidth={3}
              dot={{ r: 4, fill: '#C6D82F', strokeWidth: 2, stroke: 'white' }}
              activeDot={{ r: 8, fill: '#C6D82F', strokeWidth: 0 }}
              name="CapEx"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
