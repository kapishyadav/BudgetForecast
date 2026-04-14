import { TrendingUp, BarChart3, ArrowRight } from 'lucide-react';

export function Hero() {
  return (
    <div className="relative overflow-hidden py-20 sm:py-32 shrink-0 w-full text-center">

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-4xl mx-auto flex flex-col items-center">

            <div className="flex justify-center mb-8 w-full">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-card border border-border shadow-sm transition-colors">

                <div className="bg-muted p-1.5 rounded-full text-muted-foreground transition-colors">
                  <BarChart3 className="w-4 h-4" />
                </div>

                <span className="text-sm font-medium text-foreground transition-colors">
                  Introducing Kharchu Forecasting
                </span>
              </div>
            </div>

          <h1 className="text-5xl md:text-7xl font-bold text-[#1A1A1A] dark:text-white tracking-tight mb-6 leading-[1.1] text-center w-full transition-colors">
            Keep Your Cloud <span className="text-[#826363] dark:text-light-accent transition-colors">Kharchu</span> <br className="hidden md:block" />
            Under Control
          </h1>

          <p className="text-lg md:text-xl text-gray-500 dark:text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed text-center transition-colors">
            Stop guessing your next AWS invoice. Use advanced machine learning models to predict, track, and optimize your cloud costs accurately.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full">
          <button
            className="w-full sm:w-auto px-8 py-4 rounded-[16px] bg-primary text-primary-foreground font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-all shadow-sm group cursor-pointer"
            onClick={() => window.location.href = '/login'}
          >
            Get Started
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            className="w-full sm:w-auto px-8 py-4 rounded-[16px] bg-card text-foreground border border-border font-medium hover:bg-muted transition-all shadow-sm flex items-center justify-center cursor-pointer"
          >
            View Documentation
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20 max-w-4xl mx-auto w-full justify-items-center">
          {[
            { value: '99.9%', label: 'Accuracy Rate', icon: TrendingUp },
            { value: '50K+', label: 'Forecasts Generated', icon: BarChart3 },
            { value: '$2M+', label: 'Saved in Costs', icon: TrendingUp }
          ].map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div
                key={index}
                className="bg-card text-card-foreground rounded-[24px] p-6 border border-border shadow-sm hover:shadow-md transition-all flex flex-col items-center text-center w-full max-w-[300px]"
              >
                {/* FIX APPLIED HERE:
                  Swapped 'text-light-accent' to 'text-[#826363] dark:text-light-accent'
                */}
                <div className="bg-muted p-3 rounded-full text-[#826363] dark:text-light-accent mb-4 flex items-center justify-center transition-colors">
                  <Icon size={24} />
                </div>

                <div className="text-3xl font-bold text-foreground mb-1 transition-colors">
                  {stat.value}
                </div>

                <div className="text-sm text-muted-foreground transition-colors">
                  {stat.label}
                </div>
              </div>
            );
          })}
        </div>

        </div>
      </div>

      <div className="absolute top-0 left-0 w-full h-full -z-10 overflow-hidden pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-gray-200/50 dark:bg-blue-900/20 blur-[120px] transition-colors duration-500"></div>
        <div className="absolute top-[20%] -right-[10%] w-[50%] h-[50%] rounded-full bg-gray-200/50 dark:bg-blue-900/20 blur-[120px] transition-colors duration-500"></div>
      </div>

    </div>
  );
}