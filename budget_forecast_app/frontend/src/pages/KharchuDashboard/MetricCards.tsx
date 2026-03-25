import { MoreVertical, Globe, Clock, TrendingUp, RefreshCcw, Sparkles } from 'lucide-react';

interface MetricCardsProps {
  metrics: {
    total_forecasted_spend?: number;
    average_monthly_spend?: number; // Added for TS
    forecast_period?: string;       // Added for TS
    mape?: number;
    rmse?: number;
    mse?: number;
    mae?: number;
  } | null;
  isLoading: boolean;
}

export function MetricCards({ metrics, isLoading }: MetricCardsProps) {

  // A helper to format large numbers nicely (e.g. $12.45M)
  const formatCurrency = (val: number) => {
    if (!val) return '$0';
    if (val >= 1000000) return `$${(val / 1000000).toFixed(2)}M`;
    return `$${val.toLocaleString()}`;
  };

  // If loading, render the exact same structure but with pulse animations
  if (isLoading || !metrics) {
    return (
      <div className="flex flex-nowrap overflow-x-auto gap-6 pb-4 w-full custom-scrollbar mb-8 animate-pulse">
        {/* Placeholder Card 1 */}
        <div className="min-w-[320px] flex-1 bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 h-[220px] shrink-0">
          <div className="h-6 bg-gray-200 rounded-full w-1/3 mb-10"></div>
          <div className="h-10 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-10 bg-gray-100 rounded w-full"></div>
        </div>
        {/* Placeholder Card 2 */}
        <div className="min-w-[320px] flex-1 bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 h-[220px] shrink-0">
          <div className="h-6 bg-gray-200 rounded-full w-1/3 mb-10"></div>
          <div className="h-10 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-10 bg-gray-100 rounded w-full"></div>
        </div>
        {/* The Promo card doesn't need to load, it's static */}
        <PromoCard />
      </div>
    );
  }

  // --- Calculations for Card 1: Total Forecasted Spend ---
  // We need a dummy "budget" to show the progress bar working.
  // Let's assume the budget is 20% higher than whatever Prophet predicted.
  const totalSpend = metrics.total_forecasted_spend || 0;
  const dummyBudget = totalSpend * 1.2;
  const spendPercentage = dummyBudget > 0 ? (totalSpend / dummyBudget) * 100 : 0;

  // Calculate how many of the 8 segments should be fully black
  const segmentsFilled = Math.floor((spendPercentage / 100) * 8);

  // --- Calculations for Card 2: Model Accuracy (MAPE) ---
  // MAPE is an error rate. So Accuracy = 100% - Error%.
  const mapeError = metrics.mape ? metrics.mape * 100 : 0;
  const accuracyPercentage = Math.max(0, 100 - mapeError);

  // Calculate segments for Accuracy (out of 8)
  const accuracySegmentsFilled = Math.floor((accuracyPercentage / 100) * 8);

  return (
    <div className="flex flex-nowrap overflow-x-auto gap-6 pb-4 w-full custom-scrollbar mb-8">

      {/* Card 1: Total Forecasted Spend */}
      <div className="min-w-[320px] flex-1 bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 flex flex-col justify-between shrink-0">
        <div className="flex justify-between items-start mb-6">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-[#F5F1EB]/50 text-gray-600 rounded-full text-sm font-medium border border-gray-100">
                <Globe size={16} />
                <span>Predicted Future Spend</span>
              </div>
            </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-1">

            {/* Left Side: Period Pill */}
            {metrics?.forecast_period ? (
              <div className="flex items-center gap-1.5 px-2 py-0.5 bg-gray-50 text-gray-400 rounded-full text-[10px] font-bold uppercase tracking-wider border border-gray-100">
                <Clock size={10} />
                <span>{metrics.forecast_period}</span>
              </div>
            ) : (
              /* Add an empty div as a fallback so 'justify-between' doesn't push the percentage to the left if the period is missing */
              <div></div>
            )}

            {/* Right Side: Percentage Pill */}
            <span className="text-sm font-semibold text-gray-700 bg-gray-100 px-2 py-0.5 rounded-full">
              {spendPercentage.toFixed(1)}%
            </span>

          </div>
          <div className="text-4xl font-bold text-[#1A1A1A] mb-1 tracking-tight">
            {formatCurrency(totalSpend)}
          </div>
          <div className="text-sm text-gray-500 mb-6">/ {formatCurrency(dummyBudget)} Budget</div>

          <div className="flex space-x-1.5 h-10">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className={`flex-1 rounded-full ${
                  i < segmentsFilled
                    ? 'bg-[#1A1A1A]'
                    : i === segmentsFilled
                      ? 'bg-[#1A1A1A] opacity-50' // Partial fill for the current segment
                      : 'bg-transparent border-2 border-dashed border-gray-300'
                }`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Card 2: Average Monthly Spend */}
        <div className="min-w-[320px] flex-1 bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 flex flex-col justify-between shrink-0">
          <div className="flex justify-between items-start mb-6">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 text-gray-500 rounded-full text-sm font-medium border border-gray-100">
                  <TrendingUp size={16} />
                  <span>Average Monthly Spend</span>
                </div>
              </div>
          </div>

          <div>
            <div className="flex justify-end mb-1">
              {/* Moved the percentage here to match Card 1 perfectly */}
              <span className="text-sm font-semibold text-gray-700 bg-gray-100 px-2 py-0.5 rounded-full">
                {spendPercentage.toFixed(1)}%
              </span>
            </div>

            <div className="text-4xl font-bold text-[#1A1A1A] mb-1 tracking-tight">
              {formatCurrency(metrics?.average_monthly_spend || 0)}
            </div>

            {/* Moved the Limit down here, mimicking the "/ Budget" placement of Card 1 */}
            <div className="text-sm text-gray-500 mb-6">
              / {formatCurrency((metrics?.average_monthly_spend || 0) * 1.2)} Limit
            </div>

            <div className="flex space-x-1.5 h-10">
              {Array.from({ length: 8 }).map((_, i) => (
                <div
                  key={i}
                  className={`flex-1 rounded-full ${
                    i < segmentsFilled
                      ? 'bg-[#1A1A1A]'
                      : i === segmentsFilled
                        ? 'bg-[#1A1A1A] opacity-50'
                        : 'bg-transparent border-2 border-dashed border-gray-300'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>



      {/* Card 3: Model Accuracy */}
      <div className="min-w-[320px] flex-1 bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 flex flex-col justify-between shrink-0">
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center space-x-2 text-gray-500 font-medium text-sm bg-gray-50 px-3 py-1.5 rounded-full">
            <RefreshCcw size={16} />
            <span>Prophet Confidence</span>
          </div>
          <button className="text-gray-400 hover:text-gray-800">
            <MoreVertical size={20} />
          </button>
        </div>

        <div>
          <div className="flex justify-end mb-1">
            {/* Show the actual Error Margin (RMSE) up top */}
            <span className="text-sm font-semibold text-gray-700 bg-gray-100 px-2 py-0.5 rounded-full">
              ± {formatCurrency(metrics.rmse || 0)}
            </span>
          </div>
          <div className="text-4xl font-bold text-[#1A1A1A] mb-1 tracking-tight">
            {accuracyPercentage.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500 mb-6">Overall Model Accuracy</div>

          <div className="flex space-x-1.5 h-10">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className={`flex-1 rounded-full ${
                  i < accuracySegmentsFilled
                    ? 'bg-[#1A1A1A]'
                    : 'bg-transparent border-2 border-dashed border-gray-300'
                }`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Card 4 - Promotional */}
      <PromoCard />

    </div>
  );
}

// Extracted Promo card to keep the main component clean
function PromoCard() {
  return (
    // Added shrink-0 and min-w here so it behaves inside the horizontal scroller
    <div className="min-w-[320px] flex-1 shrink-0 bg-[#EAFF52] rounded-[24px] p-6 shadow-md text-gray-500 justify-between relative overflow-hidden group z-0">
      <div className="absolute top-0 right-0 w-48 h-48 bg-blue-500/20 rounded-full blur-3xl -mr-10 -mt-10 group-hover:bg-blue-500/30 transition-colors"></div>
      <div className="absolute bottom-0 left-0 w-32 h-32 bg-purple-500/20 rounded-full blur-3xl -ml-10 -mb-10 group-hover:bg-purple-500/30 transition-colors"></div>

      <div className="relative z-10 h-full flex flex-col">
        <h3 className="text-2xl font-semibold leading-tight mb-4 pr-12 text-[#1A1A1A]">
          Optimize with AI Forecasting Scenarios
        </h3>
        <div className="mt-auto">
          <button className="bg-white text-[#1A1A1A] px-6 py-3 rounded-xl font-medium flex items-center space-x-2 hover:bg-gray-100 transition-colors">
            <Sparkles size={16} className="text-blue-600" />
            <span>Run New Scenario</span>
          </button>
        </div>
      </div>
      <div className="absolute top-6 right-6 z-10 text-[#1A1A1A]/20">
        <div className="w-24 h-24 border border-[#1A1A1A]/20 rounded-full flex items-center justify-center">
          <div className="w-16 h-16 border border-[#1A1A1A]/30 rounded-full"></div>
        </div>
      </div>
    </div>
  );
}