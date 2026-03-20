import { Brain, TrendingUp, Bell, BarChart2, DollarSign, Shield } from 'lucide-react';

const features = [
  {
    icon: Brain,
    title: 'ML-Powered Predictions',
    description: 'Advanced machine learning models trained on historical AWS spending patterns to deliver accurate forecasts.'
  },
  {
    icon: TrendingUp,
    title: 'Trend Analysis',
    description: 'Identify spending trends and seasonal patterns to make informed decisions about resource allocation.'
  },
  {
    icon: Bell,
    title: 'Proactive Alerts',
    description: 'Get notified when spending is predicted to exceed budgets, allowing you to take action early.'
  },
  {
    icon: BarChart2,
    title: 'Visual Insights',
    description: 'Interactive dashboards and charts that make complex forecasting data easy to understand.'
  },
  {
    icon: DollarSign,
    title: 'Cost Optimization',
    description: 'Discover opportunities to reduce costs based on predicted usage patterns and historical data.'
  },
  {
    icon: Shield,
    title: 'Budget Protection',
    description: 'Prevent budget overruns with confidence intervals and risk assessments for your forecasts.'
  }
];

export function Features() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
      <div className="text-center mb-20">
        <h2 className="max-w-2xl mx-auto text-lg" style={{ color: 'var(--primary)', opacity: 0.8 }}>
          Features
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          const isHighlighted = index === 0 || index === 3;
          return (
            <div
              key={index}
              className="p-8 group cursor-pointer relative"
              style={{
                backgroundColor: isHighlighted ? 'var(--accent)' : 'white',
                borderRadius: 'var(--radius)',
                border: isHighlighted ? '3px solid var(--primary)' : '3px solid var(--light-accent)',
                boxShadow: isHighlighted ? '6px 6px 0 var(--primary)' : '6px 6px 0 var(--light-accent)',
                transition: 'var(--transition)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translate(-4px, -4px)';
                if (isHighlighted) {
                  e.currentTarget.style.boxShadow = '10px 10px 0 var(--primary)';
                } else {
                  e.currentTarget.style.boxShadow = '10px 10px 0 var(--accent)';
                  e.currentTarget.style.borderColor = 'var(--accent)';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translate(0, 0)';
                if (isHighlighted) {
                  e.currentTarget.style.boxShadow = '6px 6px 0 var(--primary)';
                } else {
                  e.currentTarget.style.boxShadow = '6px 6px 0 var(--light-accent)';
                  e.currentTarget.style.borderColor = 'var(--light-accent)';
                }
              }}
            >
              <div
                className="w-14 h-14 flex items-center justify-center mb-6 relative"
                style={{
                  backgroundColor: isHighlighted ? 'rgba(255,255,255,0.2)' : 'var(--light-accent)',
                  borderRadius: 'calc(var(--radius) - 4px)',
                  boxShadow: '3px 3px 0 rgba(0,0,0,0.1)'
                }}
              >
                <Icon className="w-7 h-7" style={{ color: isHighlighted ? 'white' : 'var(--accent)' }} />
              </div>
              <h3 className="mb-3" style={{ color: isHighlighted ? 'white' : 'var(--primary)' }}>
                {feature.title}
              </h3>
              <p style={{ color: isHighlighted ? 'rgba(255,255,255,0.9)' : 'var(--primary)', opacity: isHighlighted ? 1 : 0.8 }}>
                {feature.description}
              </p>

              {/* Corner accent */}
              <div
                className="absolute top-3 right-3 w-2 h-2 rounded-full"
                style={{ backgroundColor: isHighlighted ? 'white' : 'var(--accent)' }}
              ></div>
            </div>
          );
        })}
      </div>
    </div>
  );
}