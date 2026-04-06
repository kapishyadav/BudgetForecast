import { ArrowRight } from 'lucide-react';

export function CTA() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-20">
      {/* 1. Main Card Surface */}
      <div className="bg-card text-card-foreground rounded-[24px] p-10 shadow-sm border border-border text-center transition-colors">

        {/* Header */}
        <div className="mb-6">
          {/* Inherits text-card-foreground from parent */}
          <h2 className="text-3xl font-bold tracking-tight mb-3 transition-colors">
            Ready to Run Your Forecast?
          </h2>
          {/* 2. Muted Text */}
          <p className="text-muted-foreground text-sm max-w-md mx-auto transition-colors">
            Upload your dataset and start generating accurate time series forecasts in minutes.
          </p>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row justify-center gap-4 mt-8">

          {/* 3. Primary Button */}
          <button
            className="bg-primary text-primary-foreground hover:opacity-90 rounded-xl px-6 py-4 font-semibold text-lg flex items-center justify-center space-x-2 transition-all shadow-sm cursor-pointer"
          >
            <span>Start Forecast</span>
            <ArrowRight size={20} />
          </button>

          {/* 4. Secondary (Outline) Button */}
          <button
            className="bg-transparent border border-border text-foreground hover:bg-muted rounded-xl px-6 py-4 font-semibold text-lg transition-all shadow-sm cursor-pointer"
          >
            Learn More
          </button>

        </div>

        {/* 5. Divider */}
        <div className="mt-10 pt-6 border-t border-border transition-colors">

          {/* Trust Indicators */}
          <div className="flex flex-wrap justify-center items-center gap-6 text-sm text-muted-foreground transition-colors">
            <span>SOC 2 Certified</span>
            <span>•</span>
            <span>No Credit Card Required</span>
            <span>•</span>
            <span>Setup in Minutes</span>
          </div>

        </div>
      </div>
    </div>
  );
}