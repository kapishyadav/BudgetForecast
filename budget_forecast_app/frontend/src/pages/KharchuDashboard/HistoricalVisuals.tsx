import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from 'recharts';

interface HistoricalVisualsProps {
  data: {
    accounts?: { name: string; value: number }[];
    services?: { name: string; value: number }[];
  } | null;
}

// Colors derived from your theme/palette for the Pie Chart
const COLORS = [
  '#EAFF52', '#AFCC1D', '#826363', '#a47148', '#d8c3a5', '#6b5d5d', '#3b2f2f'
];

const formatCurrency = (value: number) => `$${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

export function HistoricalVisuals({ data }: HistoricalVisualsProps) {
  if (!data || !data.accounts || !data.services) {
     return (
        <div className="mb-8 bg-card border border-border shadow-sm rounded-[24px] p-6 flex items-center justify-center h-[200px]">
           <p className="text-muted-foreground font-medium">No historical visualization data available for this dataset.</p>
        </div>
     );
  }

  const safeAccounts = data.accounts || [];
  const safeServices = data.services || [];

  return (
    // Increased gap and changed lg:grid-cols-2 to xl:grid-cols-2 for better responsiveness
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-10 animate-in fade-in slide-in-from-bottom-4 duration-500">

      {/* Account Pie Chart */}
      {/* Increased min-height to 600px and padding to p-8 */}
      <div className="bg-card border border-border shadow-sm rounded-[24px] p-8 transition-colors duration-300 flex flex-col min-h-[600px]">
        <h3 className="text-xl font-bold text-foreground mb-6">Historical Spend by Account</h3>
        <div className="flex-1 w-full min-h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart margin={{ top: 20, right: 0, bottom: 0, left: 0 }}>
              <Pie
                data={safeAccounts}
                cx="50%"
                cy="45%" // Keeps it perfectly lifted above your new legend
                innerRadius={80} // Scaled down to maintain the donut thickness ratio
                outerRadius={120} // REDUCED from 140 to absolutely prevent top clipping
                paddingAngle={2}
                dataKey="value"
              >
                {safeAccounts.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                  formatter={(value: number) => formatCurrency(value)}
                  contentStyle={{
                    borderRadius: '12px',
                    borderColor: 'var(--border)',
                    backgroundColor: 'var(--card)',
                    padding: '12px'
                  }}
                  itemStyle={{ color: 'var(--foreground)' }} // OVERRIDES THE SLICE COLOR
                />
              <Legend
                  verticalAlign="bottom"
                  content={(props: any) => {
                    const { payload } = props;
                    return (
                      // Forces a neat 2-column grid with gap spacing
                      <ul className="grid grid-cols-2 gap-x-4 gap-y-3 pt-8 w-full px-2">
                        {payload?.map((entry: any, index: number) => (
                          <li
                            key={`item-${index}`}
                            className="flex items-center text-sm text-foreground overflow-hidden"
                          >
                            {/* The colored dot (shrink-0 prevents it from getting squished by long text) */}
                            <span
                              className="w-3 h-3 rounded-full mr-2 shrink-0"
                              style={{ backgroundColor: entry.color }}
                            />
                            {/* The account name (truncate adds the ellipsis, title shows full name on hover) */}
                            <span className="truncate font-medium" title={entry.value}>
                              {entry.value}
                            </span>
                          </li>
                        ))}
                      </ul>
                    );
                  }}
                />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Service Horizontal Bar Chart */}
      <div className="bg-card border border-border shadow-sm rounded-[24px] p-8 transition-colors duration-300 flex flex-col min-h-[600px]">
        <h3 className="text-xl font-bold text-foreground mb-6">Top Services Spend</h3>
        <div className="flex-1 w-full min-h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              layout="vertical"
              data={safeServices}
              // Removed the massive left margin, the YAxis width handles it now
              margin={{ top: 20, right: 40, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="var(--border)" />
              <XAxis
                type="number"
                tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                stroke="var(--muted-foreground)"
                fontSize={12}
              />
              <YAxis
                dataKey="name"
                type="category"
                // MASSIVELY EXPANDED WIDTH TO 220px FOR LONG SERVICE NAMES
                width={220}
                tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
                interval={0} // Forces every label to render
              />
              <Tooltip
                formatter={(value: number) => formatCurrency(value)}
                cursor={{ fill: 'var(--muted)', opacity: 0.2 }}
                contentStyle={{ borderRadius: '12px', borderColor: 'var(--border)', backgroundColor: 'var(--card)', color: 'var(--foreground)', padding: '12px' }}
              />
              {/* Made bars slightly thinner (16px) so 21 items don't feel crammed */}
              <Bar dataKey="value" fill="var(--foreground)" radius={[0, 4, 4, 0]} barSize={16} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  );
}