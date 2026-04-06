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
    <div className="max-w-5xl mx-auto px-4 py-20">

      {/* Header Section */}
      <div className="mb-12 text-center">
        {/* Changed to text-foreground */}
        <h2 className="text-3xl font-bold text-foreground tracking-tight mb-3 transition-colors">
          Powerful Forecasting Features
        </h2>
        {/* Changed to text-muted-foreground */}
        <p className="text-muted-foreground text-sm max-w-xl mx-auto transition-colors">
          Everything you need to understand, predict, and optimize your cloud spending.
        </p>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {features.map((feature, index) => {
          const Icon = feature.icon;

          return (
            <div
              key={index}
              className="bg-card text-card-foreground rounded-[24px] p-6 border border-border shadow-sm hover:shadow-md transition-all"
            >
              {/* Changed to bg-card, text-card-foreground, and border-border */}

              {/* Icon */}
              <div className="flex items-center space-x-4 mb-4">
                {/* Changed to bg-muted and text-muted-foreground */}
                <div className="bg-muted p-3 rounded-full text-muted-foreground transition-colors">
                  <Icon size={20} />
                </div>

                {/* Color is inherited from text-card-foreground on the parent div */}
                <h3 className="text-lg font-semibold transition-colors">
                  {feature.title}
                </h3>
              </div>

              {/* Description */}
              {/* Changed to text-muted-foreground */}
              <p className="text-muted-foreground text-sm leading-relaxed pl-12 transition-colors">
                {feature.description}
              </p>
            </div>
          );
        })}

      </div>
    </div>
  );
}