import { MoreVertical, Globe, RefreshCcw, Sparkles } from 'lucide-react';

interface MetricCardsProps {
  metrics: {
    total_forecasted_spend?: number;
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 animate-pulse">
        {/* Placeholder Card 1 */}
        <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 h-[220px]">
          <div className="h-6 bg-gray-200 rounded-full w-1/3 mb-10"></div>
          <div className="h-10 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-10 bg-gray-100 rounded w-full"></div>
        </div>
        {/* Placeholder Card 2 */}
        <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 h-[220px]">
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
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">

      {/* Card 1: Total Forecasted Spend */}
      <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 flex flex-col justify-between">
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center space-x-2 text-gray-500 font-medium text-sm bg-gray-50 px-3 py-1.5 rounded-full">
            <Globe size={16} />
            <span>Predicted Future Spend</span>
          </div>
          <button className="text-gray-400 hover:text-gray-800">
            <MoreVertical size={20} />
          </button>
        </div>

        <div>
          <div className="flex justify-end mb-1">
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

      {/* Card 2: Model Accuracy */}
      <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 flex flex-col justify-between">
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

      {/* Card 3 - Promotional (Kept exactly as you designed it) */}
      <PromoCard />

    </div>
  );
}

// Extracted Promo card to keep the main component clean
function PromoCard() {
  return (
    <div className="bg-[#EAFF52] rounded-[24px] p-6 shadow-md text-gray-500 justify-between relative overflow-hidden group z-0">
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