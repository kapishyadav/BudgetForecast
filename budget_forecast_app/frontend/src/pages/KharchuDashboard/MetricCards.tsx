import { MoreVertical, Globe, Clock, TrendingUp, RefreshCcw, Sparkles } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';

interface MetricCardsProps {
  metrics: {
    total_forecasted_spend?: number;
    average_monthly_spend?: number;
    forecast_period?: string;
    mape?: number;
    rmse?: number;
    mse?: number;
    mae?: number;
  } | null;
  isLoading: boolean;
  datasetId: string | null;
}

export function MetricCards({ metrics, isLoading, datasetId }: MetricCardsProps) {

  const formatCurrency = (val: number) => {
    if (!val) return '$0';
    if (val >= 1000000) return `$${(val / 1000000).toFixed(2)}M`;
    return `$${val.toLocaleString()}`;
  };

  // Loading State - Updated to use bg-card, border-border, and bg-muted
  if (isLoading || !metrics) {
    return (
      <div className="flex flex-nowrap overflow-x-auto gap-6 pb-4 w-full custom-scrollbar mb-8 animate-pulse">
        <div className="min-w-[320px] flex-1 bg-card rounded-[24px] p-6 shadow-sm border border-border h-[220px] shrink-0 transition-colors duration-300">
          <div className="h-6 bg-muted rounded-full w-1/3 mb-10 transition-colors duration-300"></div>
          <div className="h-10 bg-muted rounded w-1/2 mb-4 transition-colors duration-300"></div>
          <div className="h-10 bg-muted rounded w-full transition-colors duration-300"></div>
        </div>
        <div className="min-w-[320px] flex-1 bg-card rounded-[24px] p-6 shadow-sm border border-border h-[220px] shrink-0 transition-colors duration-300">
          <div className="h-6 bg-muted rounded-full w-1/3 mb-10 transition-colors duration-300"></div>
          <div className="h-10 bg-muted rounded w-1/2 mb-4 transition-colors duration-300"></div>
          <div className="h-10 bg-muted rounded w-full transition-colors duration-300"></div>
        </div>
        <PromoCard datasetId={datasetId} />
      </div>
    );
  }

  // Calculations
  const totalSpend = metrics.total_forecasted_spend || 0;
  const dummyBudget = totalSpend * 1.2;
  const spendPercentage = dummyBudget > 0 ? (totalSpend / dummyBudget) * 100 : 0;

  const [searchParams] = useSearchParams();
  const urlModel = searchParams.get('model');

  const modelDisplayNames: Record<string, string> = {
    xgboost: 'XGBoost',
    prophet: 'Prophet',
    catboost: 'CatBoost',
  };
  const activeModelName = urlModel
    ? (modelDisplayNames[urlModel.toLowerCase()] || 'Model')
    : 'Prophet';

  const segmentsFilled = Math.floor((spendPercentage / 100) * 8);

  const mapeError = metrics.mape ? metrics.mape * 100 : 0;
  const accuracyPercentage = Math.max(0, 100 - mapeError);
  const accuracySegmentsFilled = Math.floor((accuracyPercentage / 100) * 8);

  return (
    <div className="flex flex-nowrap overflow-x-auto gap-6 pb-4 w-full custom-scrollbar mb-8">

      {/* Card 1: Total Forecasted Spend */}
      {/* Replaced bg-white and border-gray-50 with bg-card and border-border */}
      <div className="min-w-[320px] flex-1 bg-card rounded-[24px] p-6 shadow-sm border border-border flex flex-col justify-between shrink-0 transition-colors duration-300">
        <div className="flex justify-between items-start mb-6">
            <div className="flex items-center gap-2">
              {/* Replaced bg-[#F5F1EB] with bg-muted */}
              <div className="flex items-center gap-2 px-3 py-1.5 bg-muted text-muted-foreground rounded-full text-sm font-medium border border-border transition-colors duration-300">
                <Globe size={16} />
                <span>Predicted Future Spend</span>
              </div>
            </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-1">
            {metrics?.forecast_period ? (
              <div className="flex items-center gap-1.5 px-2 py-0.5 bg-muted text-muted-foreground rounded-full text-[10px] font-bold uppercase tracking-wider border border-border transition-colors duration-300">
                <Clock size={10} />
                <span>{metrics.forecast_period}</span>
              </div>
            ) : (
              <div></div>
            )}
            <span className="text-sm font-semibold text-foreground bg-muted border border-border px-2 py-0.5 rounded-full transition-colors duration-300">
              {spendPercentage.toFixed(1)}%
            </span>
          </div>
          {/* Replaced text-[#1A1A1A] with text-foreground */}
          <div className="text-4xl font-bold text-foreground mb-1 tracking-tight transition-colors duration-300">
            {formatCurrency(totalSpend)}
          </div>
          <div className="text-sm text-muted-foreground mb-6 transition-colors duration-300">/ {formatCurrency(dummyBudget)} Budget</div>

          <div className="flex space-x-1.5 h-10">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className={`flex-1 rounded-full transition-colors duration-300 ${
                  i < segmentsFilled
                    ? 'bg-foreground'
                    : i === segmentsFilled
                      ? 'bg-foreground opacity-50'
                      : 'bg-transparent border-2 border-dashed border-border'
                }`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Card 2: Average Monthly Spend */}
        <div className="min-w-[320px] flex-1 bg-card rounded-[24px] p-6 shadow-sm border border-border flex flex-col justify-between shrink-0 transition-colors duration-300">
          <div className="flex justify-between items-start mb-6">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-muted text-muted-foreground rounded-full text-sm font-medium border border-border transition-colors duration-300">
                  <TrendingUp size={16} />
                  <span>Average Monthly Spend</span>
                </div>
              </div>
          </div>

          <div>
            <div className="flex justify-end mb-1">
              <span className="text-sm font-semibold text-foreground bg-muted border border-border px-2 py-0.5 rounded-full transition-colors duration-300">
                {spendPercentage.toFixed(1)}%
              </span>
            </div>
            <div className="text-4xl font-bold text-foreground mb-1 tracking-tight transition-colors duration-300">
              {formatCurrency(metrics?.average_monthly_spend || 0)}
            </div>
            <div className="text-sm text-muted-foreground mb-6 transition-colors duration-300">
              / {formatCurrency((metrics?.average_monthly_spend || 0) * 1.2)} Limit
            </div>
            <div className="flex space-x-1.5 h-10">
              {Array.from({ length: 8 }).map((_, i) => (
                <div
                  key={i}
                  className={`flex-1 rounded-full transition-colors duration-300 ${
                    i < segmentsFilled
                      ? 'bg-foreground'
                      : i === segmentsFilled
                        ? 'bg-foreground opacity-50'
                        : 'bg-transparent border-2 border-dashed border-border'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>

      {/* Card 3: Model Accuracy */}
      <div className="min-w-[320px] flex-1 bg-card rounded-[24px] p-6 shadow-sm border border-border flex flex-col justify-between shrink-0 transition-colors duration-300">
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center space-x-2 text-muted-foreground font-medium text-sm bg-muted border border-border px-3 py-1.5 rounded-full transition-colors duration-300">
            <RefreshCcw size={16} />
            <span>{activeModelName} Confidence</span>
          </div>
          <button className="text-muted-foreground hover:text-foreground transition-colors duration-300">
            <MoreVertical size={20} />
          </button>
        </div>

        <div>
          <div className="flex justify-end mb-1">
            <span className="text-sm font-semibold text-foreground bg-muted border border-border px-2 py-0.5 rounded-full transition-colors duration-300">
              ± {formatCurrency(metrics.rmse || 0)}
            </span>
          </div>
          <div className="text-4xl font-bold text-foreground mb-1 tracking-tight transition-colors duration-300">
            {accuracyPercentage.toFixed(1)}%
          </div>
          <div className="text-sm text-muted-foreground mb-6 transition-colors duration-300">Overall Model Accuracy</div>
          <div className="flex space-x-1.5 h-10">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className={`flex-1 rounded-full transition-colors duration-300 ${
                  i < accuracySegmentsFilled
                    ? 'bg-foreground'
                    : 'bg-transparent border-2 border-dashed border-border'
                }`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Card 4 - Promotional */}
      <PromoCard datasetId={datasetId} />

    </div>
  );
}

// Extracted Promo card
function PromoCard({ datasetId }: { datasetId: string | null }) {
  const navigate = useNavigate();

  const handleNavigate = () => {
    if (!datasetId) {
      alert("Still loading dataset context. Please wait a moment!");
      return;
    }
    navigate(`/custom-scenario?datasetId=${datasetId}`);
  };

  return (
    // Uses bg-light-accent and forces text to be dark (#09090B) to maintain contrast against the neon
    <div className="min-w-[320px] flex-1 shrink-0 bg-light-accent text-[#09090B] rounded-[24px] p-6 shadow-md justify-between relative overflow-hidden group z-0 transition-colors duration-300 border border-light-accent">
      <div className="absolute top-0 right-0 w-48 h-48 bg-blue-500/20 rounded-full blur-3xl -mr-10 -mt-10 group-hover:bg-blue-500/30 transition-colors"></div>
      <div className="absolute bottom-0 left-0 w-32 h-32 bg-purple-500/20 rounded-full blur-3xl -ml-10 -mb-10 group-hover:bg-purple-500/30 transition-colors"></div>

      <div className="relative z-10 h-full flex flex-col">
        <h3 className="text-2xl font-semibold leading-tight mb-4 pr-12 text-[#09090B]">
          Optimize with AI Forecasting Scenarios
        </h3>
        <div className="mt-auto">
          {/* Button uses bg-card and text-card-foreground */}
          <button
            onClick={handleNavigate}
            className="bg-card text-card-foreground px-6 py-3 rounded-xl font-medium flex items-center space-x-2 hover:bg-muted transition-colors z-20 relative cursor-pointer shadow-sm border border-border"
          >
            <Sparkles size={16} className="text-blue-500" />
            <span>Run New Scenario</span>
          </button>
        </div>
      </div>
      <div className="absolute top-6 right-6 z-10 text-[#09090B]/20 pointer-events-none">
        <div className="w-24 h-24 border border-[#09090B]/20 rounded-full flex items-center justify-center">
          <div className="w-16 h-16 border border-[#09090B]/30 rounded-full"></div>
        </div>
      </div>
    </div>
  );
}