import { ArrowRight } from 'lucide-react';

export function CTA() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-20">
      <div className="bg-white rounded-[24px] p-10 shadow-sm border border-gray-50 text-center">

        {/* Header */}
        <div className="mb-6">
          <h2 className="text-3xl font-bold text-[#1A1A1A] tracking-tight mb-3">
            Ready to Run Your Forecast?
          </h2>
          <p className="text-gray-500 text-sm max-w-md mx-auto">
            Upload your dataset and start generating accurate time series forecasts in minutes.
          </p>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row justify-center gap-4 mt-8">

          {/* Primary CTA (matches UploadPage button) */}
          <button
            className="bg-[#1A1A1A] text-white hover:bg-black rounded-xl px-6 py-4 font-semibold text-lg flex items-center justify-center space-x-2 transition-all shadow-sm"
          >
            <span>Start Forecast</span>
            <ArrowRight size={20} />
          </button>

          {/* Secondary CTA */}
          <button
            className="bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 rounded-xl px-6 py-4 font-semibold text-lg transition-all shadow-sm"
          >
            Learn More
          </button>

        </div>

        {/* Divider */}
        <div className="mt-10 pt-6 border-t border-gray-100">

          {/* Trust Indicators */}
          <div className="flex flex-wrap justify-center items-center gap-6 text-sm text-gray-400">
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