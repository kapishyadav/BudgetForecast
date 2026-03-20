import { MoreVertical, Globe, RefreshCcw, Sparkles } from 'lucide-react';

export function MetricCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {/* Card 1 */}
      <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 flex flex-col justify-between">
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center space-x-2 text-gray-500 font-medium text-sm bg-gray-50 px-3 py-1.5 rounded-full">
            <Globe size={16} />
            <span>Total Q3 Forecast</span>
          </div>
          <button className="text-gray-400 hover:text-gray-800">
            <MoreVertical size={20} />
          </button>
        </div>
        
        <div>
          <div className="flex justify-end mb-1">
            <span className="text-sm font-semibold text-gray-700 bg-gray-100 px-2 py-0.5 rounded-full">83%</span>
          </div>
          <div className="text-4xl font-bold text-[#1A1A1A] mb-1 tracking-tight">$12,450,000</div>
          <div className="text-sm text-gray-500 mb-6">/ $15,000,000 Budget</div>
          
          <div className="flex space-x-1.5 h-10">
            {Array.from({ length: 8 }).map((_, i) => (
              <div 
                key={i} 
                className={`flex-1 rounded-full ${i < 6 ? 'bg-[#1A1A1A]' : i === 6 ? 'bg-[#1A1A1A] w-[50%] rounded-r-none border-r border-r-white/20' : 'bg-transparent border-2 border-dashed border-gray-300'}`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Card 2 */}
      <div className="bg-white rounded-[24px] p-6 shadow-sm border border-gray-50 flex flex-col justify-between">
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center space-x-2 text-gray-500 font-medium text-sm bg-gray-50 px-3 py-1.5 rounded-full">
            <RefreshCcw size={16} />
            <span>SaaS Platform Spend</span>
          </div>
          <button className="text-gray-400 hover:text-gray-800">
            <MoreVertical size={20} />
          </button>
        </div>
        
        <div>
          <div className="flex justify-end mb-1">
            <span className="text-sm font-semibold text-gray-700 bg-gray-100 px-2 py-0.5 rounded-full">65.8%</span>
          </div>
          <div className="text-4xl font-bold text-[#1A1A1A] mb-1 tracking-tight">$3,620,000</div>
          <div className="text-sm text-gray-500 mb-6">/ $5,500,000 Cap</div>
          
          <div className="flex space-x-1.5 h-10">
            {Array.from({ length: 8 }).map((_, i) => (
              <div 
                key={i} 
                className={`flex-1 rounded-full ${i < 5 ? 'bg-[#1A1A1A]' : 'bg-transparent border-2 border-dashed border-gray-300'}`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Card 3 - Promotional */}
      <div className="bg-[#EAFF52] rounded-[24px] p-6 shadow-md text-gray-500 justify-between relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-48 h-48 bg-blue-500/20 rounded-full blur-3xl -mr-10 -mt-10 group-hover:bg-blue-500/30 transition-colors"></div>
        <div className="absolute bottom-0 left-0 w-32 h-32 bg-purple-500/20 rounded-full blur-3xl -ml-10 -mb-10 group-hover:bg-purple-500/30 transition-colors"></div>
        
        <div className="relative z-10 h-full flex flex-col">
          <h3 className="text-2xl font-semibold leading-tight mb-4 pr-12">
            Optimize with AI Forecasting Scenarios
          </h3>
          <div className="mt-auto">
            <button className="bg-white text-[#1A1A1A] px-6 py-3 rounded-xl font-medium flex items-center space-x-2 hover:bg-gray-100 transition-colors">
              <Sparkles size={16} className="text-blue-600" />
              <span>Run New Scenario</span>
            </button>
          </div>
        </div>
        <div className="absolute top-6 right-6 z-10 text-white/20">
          <div className="w-24 h-24 border border-white/20 rounded-full flex items-center justify-center">
            <div className="w-16 h-16 border border-white/30 rounded-full"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
