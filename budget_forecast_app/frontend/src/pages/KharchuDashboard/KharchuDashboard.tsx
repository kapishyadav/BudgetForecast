import { LeftSidebar } from './LeftSidebar';
import { TopHeader } from './TopHeader';
import { RightSidebar } from './RightSidebar';
import { TabNavigation } from './TabNavigation';
import { MetricCards } from './MetricCards';
import { StatisticsChart } from './StatisticsChart';

export function KharchuDashboard() {
  return (
    <div className="min-h-screen bg-[#E5E0D8] p-4 flex justify-center items-center">
      {/* Main Container mimicking the design's rounded UI wrapper */}
      <div className="bg-[#F5F1EB] rounded-[40px] shadow-2xl w-full max-w-[1600px] h-[95vh] flex overflow-hidden border border-white/40">
        
        {/* Navigation Sidebar */}
        <LeftSidebar />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col py-8 px-2 overflow-hidden">
          
          <TopHeader />
          <TabNavigation />
          
          {/* Scrollable Main Area for Cards and Chart */}
          <div className="flex-1 overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-gray-300">
            <MetricCards />
            <StatisticsChart />
          </div>

        </div>

        {/* Resources Sidebar */}
        <div className="py-8 pr-8 pl-4 border-l border-gray-200/50 bg-[#F5F1EB]">
          <RightSidebar />
        </div>

      </div>
    </div>
  );
}
