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

      {/* Header Section (matches UploadPage tone) */}
      <div className="mb-12 text-center">
        <h2 className="text-3xl font-bold text-[#1A1A1A] tracking-tight mb-3">
          Powerful Forecasting Features
        </h2>
        <p className="text-gray-500 text-sm max-w-xl mx-auto">
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
              className="bg-white rounded-[24px] p-6 border border-gray-100 shadow-sm hover:shadow-md transition-all"
            >
              {/* Icon */}
              <div className="flex items-center space-x-4 mb-4">
                <div className="bg-gray-50 p-3 rounded-full text-gray-500">
                  <Icon size={20} />
                </div>

                <h3 className="text-lg font-semibold text-[#1A1A1A]">
                  {feature.title}
                </h3>
              </div>

              {/* Description */}
              <p className="text-gray-500 text-sm leading-relaxed pl-12">
                {feature.description}
              </p>
            </div>
          );
        })}

      </div>
    </div>
  );
}