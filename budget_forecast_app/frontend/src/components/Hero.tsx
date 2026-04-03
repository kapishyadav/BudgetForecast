import { TrendingUp, BarChart3, ArrowRight } from 'lucide-react';

export function Hero() {
  return (
    <div className="relative overflow-hidden py-20 sm:py-32 shrink-0 w-full text-center"> {/* Added w-full text-center for global centering */}

      {/* Main Container - Ensuring mx-auto is active */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-4xl mx-auto flex flex-col items-center"> {/* Crucial: flex flex-col items-center */}

          {/* Top Badge - Ensuring justify-center is active */}
          <div className="flex justify-center mb-8 w-full"> {/* Ensure width is full for centering */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-gray-100 shadow-sm">
              <div className="bg-gray-50 p-1.5 rounded-full text-gray-500">
                <BarChart3 className="w-4 h-4" />
              </div>
              <span className="text-sm font-medium text-[#1A1A1A]">Introducing Kharchu Forecasting</span>
            </div>
          </div>

          {/* Main Heading - text-center is key */}
          <h1 className="text-5xl md:text-7xl font-bold text-[#1A1A1A] tracking-tight mb-6 leading-[1.1] text-center w-full">
            Keep Your Cloud <span className="text-[#7E6363]">Kharchu</span> <br className="hidden md:block" />
            Under Control
          </h1>

          {/* Subtitle - max-w-2xl with mx-auto and text-center */}
          <p className="text-lg md:text-xl text-gray-500 mb-10 max-w-2xl mx-auto leading-relaxed text-center">
            Stop guessing your next AWS invoice. Use advanced machine learning models to predict, track, and optimize your cloud costs accurately.
          </p>

          {/* Call to Action Buttons - justify-center on the parent flex container */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full"> {/* justify-center is critical here */}
            <button
              className="w-full sm:w-auto px-8 py-4 rounded-[16px] bg-[#1A1A1A] text-white font-medium flex items-center justify-center gap-2 hover:bg-black transition-all shadow-sm group"
              onClick={() => window.location.href = '/login'}
            >
              Get Started
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              className="w-full sm:w-auto px-8 py-4 rounded-[16px] bg-white text-[#1A1A1A] border border-gray-200 font-medium hover:bg-gray-50 transition-all shadow-sm flex items-center justify-center" // Ensure button content is centered
            >
              View Documentation
            </button>
          </div>

          {/* Stats - Grid itself is centered, but we add mx-auto to its container just in case */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20 max-w-4xl mx-auto w-full justify-items-center"> {/* added justify-items-center and w-full */}
            {[
              { value: '99.9%', label: 'Accuracy Rate', icon: TrendingUp },
              { value: '50K+', label: 'Forecasts Generated', icon: BarChart3 },
              { value: '$2M+', label: 'Saved in Costs', icon: TrendingUp }
            ].map((stat, index) => {
              const Icon = stat.icon;
              return (
                <div
                  key={index}
                  className="bg-white rounded-[24px] p-6 border border-gray-100 shadow-sm hover:shadow-md transition-all flex flex-col items-center text-center w-full max-w-[300px]" //items-center, text-center, and a max-w for small screens
                >
                  <div className="bg-gray-50 p-3 rounded-full text-gray-500 mb-4 flex items-center justify-center"> {/* justify-center on icon container */}
                    <Icon size={24} />
                  </div>
                  <div className="text-3xl font-bold text-[#1A1A1A] mb-1">{stat.value}</div>
                  <div className="text-sm text-gray-500">{stat.label}</div>
                </div>
              );
            })}
          </div>

        </div>
      </div>

      {/* Subtle Background Glows (No changes needed here) */}
      <div className="absolute top-0 left-0 w-full h-full -z-10 overflow-hidden pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-gray-200/50 blur-[120px]"></div>
        <div className="absolute top-[20%] -right-[10%] w-[50%] h-[50%] rounded-full bg-gray-200/50 blur-[120px]"></div>
      </div>

    </div>
  );
}