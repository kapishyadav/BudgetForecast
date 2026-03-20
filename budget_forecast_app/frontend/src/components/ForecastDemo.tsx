import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';

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
  return (
    <div className="py-24 relative overflow-hidden" style={{ backgroundColor: 'var(-light--accent)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center mb-16">
          <div className="inline-block mb-4 px-6 py-2" style={{
            backgroundColor: 'var(--accent)',
            color: 'white',
            borderRadius: 'var(--radius)',
            boxShadow: '3px 3px 0 var(--primary)'
          }}>
            Live Demo
          </div>
          <h2 className="mb-6" style={{ color: 'var(--primary)' }}>
            See Your Future Spending
          </h2>
          <p className="max-w-2xl mx-auto text-lg" style={{ color: 'var(--primary)', opacity: 0.8 }}>
            Visualize historical spending and predicted future costs with interactive forecasting charts.
          </p>
        </div>
        
        <div 
          className="p-10 relative"
          style={{ 
            backgroundColor: 'white',
            borderRadius: 'var(--radius)',
            border: '4px solid var(--accent)',
            boxShadow: '12px 12px 0 var(--accent)'
          }}
        >
          <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
            <div>
              <h3 className="mb-2" style={{ color: 'var(--primary)' }}>AWS Budget Forecast - 2024</h3>
              <p style={{ color: 'var(--primary)', opacity: 0.7 }}>Historical data vs. predicted spending</p>
            </div>
            <div className="flex gap-2">
              <div className="px-4 py-2 rounded-lg" style={{ backgroundColor: 'var(--light-accent)' }}>
                <span style={{ color: 'var(--primary)', fontSize: '14px' }}>⚡ Real-time</span>
              </div>
            </div>
          </div>
          
          <div className="relative">
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={historicalData}>
                <defs>
                  <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a47148" stopOpacity={0.5}/>
                    <stop offset="95%" stopColor="#a47148" stopOpacity={0.05}/>
                  </linearGradient>
                  <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b2f2f" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b2f2f" stopOpacity={0.05}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#d8c3a5" strokeWidth={1.5} />
                <XAxis dataKey="month" stroke="#3b2f2f" strokeWidth={2} />
                <YAxis stroke="#3b2f2f" strokeWidth={2} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '3px solid #a47148',
                    borderRadius: '14px',
                    boxShadow: '4px 4px 0 #d8c3a5'
                  }}
                  formatter={(value) => `$${value}`}
                />
                <Legend 
                  wrapperStyle={{ 
                    paddingTop: '20px'
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="actual" 
                  stroke="#a47148" 
                  fill="url(#colorActual)"
                  strokeWidth={4}
                  name="Actual Spending"
                  dot={{ fill: '#a47148', strokeWidth: 2, r: 5 }}
                />
                <Area 
                  type="monotone" 
                  dataKey="forecast" 
                  stroke="#3b2f2f" 
                  fill="url(#colorForecast)"
                  strokeWidth={4}
                  strokeDasharray="8 8"
                  name="Forecasted Spending"
                  dot={{ fill: '#3b2f2f', strokeWidth: 2, r: 5 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-10">
            <div 
              className="p-6 relative overflow-hidden"
              style={{ 
                backgroundColor: 'var(--light-accent)',
                borderRadius: 'var(--radius)',
                border: '3px solid var(--accent)',
                boxShadow: '4px 4px 0 var(--accent)'
              }}
            >
              <div className="absolute top-2 right-2 text-2xl opacity-20">📅</div>
              <p className="mb-2 text-sm" style={{ color: 'var(--primary)', opacity: 0.8 }}>Current Month</p>
              <p className="text-3xl" style={{ color: 'var(--accent)' }}>$6,200</p>
              <div className="mt-2 text-sm" style={{ color: 'var(--primary)', opacity: 0.6 }}>
                <span className="text-green-600">↓ 5%</span> vs last month
              </div>
            </div>
            <div 
              className="p-6 relative overflow-hidden"
              style={{ 
                backgroundColor: 'var(--accent)',
                borderRadius: 'var(--radius)',
                border: '3px solid var(--primary)',
                boxShadow: '5px 5px 0 var(--primary)',
                color: 'white'
              }}
            >
              <div className="absolute top-2 right-2 text-2xl opacity-20">🔮</div>
              <p className="mb-2 text-sm" style={{ opacity: 0.9 }}>Predicted Next Month</p>
              <p className="text-3xl">$6,500</p>
              <div className="mt-2 text-sm" style={{ opacity: 0.8 }}>
                <span style={{ color: '#d8c3a5' }}>↑ 4.8%</span> predicted growth
              </div>
            </div>
            <div 
              className="p-6 relative overflow-hidden"
              style={{ 
                backgroundColor: 'transparent',
                borderRadius: 'var(--radius)',
                border: '3px solid var(--primary)',
                boxShadow: '4px 4px 0 var(--light-accent)'
              }}
            >
              <div className="absolute top-2 right-2 text-2xl opacity-20">📈</div>
              <p className="mb-2 text-sm" style={{ color: 'var(--primary)', opacity: 0.8 }}>6-Month Forecast</p>
              <p className="text-3xl" style={{ color: 'var(--primary)' }}>$7,600</p>
              <div className="mt-2 text-sm" style={{ color: 'var(--primary)', opacity: 0.6 }}>
                95% confidence interval
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Background decoration */}
      <div className="absolute bottom-10 right-10 opacity-5 text-9xl rotate-12 pointer-events-none">📊</div>
    </div>
  );
}