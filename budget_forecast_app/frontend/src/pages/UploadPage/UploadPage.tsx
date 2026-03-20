import React from 'react';
import { LeftSidebar } from '../KharchuDashboard/LeftSidebar';
import { TopHeader } from '../KharchuDashboard/TopHeader';
import { RightSidebar } from '../KharchuDashboard/RightSidebar';
import { ForecastUpload } from './ForecastUpload'; // The component we just built

export function UploadPage() {
  return (
    <div className="min-h-screen bg-[#E5E0D8] p-4 flex justify-center items-center">
      {/* Main Container mimicking the design's rounded UI wrapper */}
      <div className="bg-[#F5F1EB] rounded-[40px] shadow-2xl w-full max-w-[1600px] h-[95vh] flex overflow-hidden border border-white/40">

        {/* Navigation Sidebar */}
        <LeftSidebar />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col py-8 px-2 overflow-hidden">

          <TopHeader />

          {/* Scrollable Main Area for the Upload Component */}
          <div className="flex-1 overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-gray-300">
            {/* We place the ForecastUpload component here.
              Because it has a max-w-2xl and mx-auto class, it will sit nicely centered
              in the middle of this large dashboard view.
            */}
            <div className="mt-4">
              <ForecastUpload />
            </div>
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