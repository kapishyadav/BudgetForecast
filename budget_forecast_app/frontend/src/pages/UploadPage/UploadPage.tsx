import React from 'react';
import { LeftSidebar } from '../KharchuDashboard/LeftSidebar';
import { TopHeader } from '../KharchuDashboard/TopHeader';
import { RightSidebar } from '../KharchuDashboard/RightSidebar';
import { ForecastUpload } from './ForecastUpload';

export function UploadPage() {
  return (
    <div className="h-screen w-screen bg-background flex overflow-hidden transition-colors duration-300">

        {/* Navigation Sidebar */}
        <LeftSidebar />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col py-8 px-2 overflow-hidden">

          <TopHeader />

          {/* Scrollable Main Area for the Upload Component */}
          {/* Swapped inline tailwind scrollbar classes for your custom-scrollbar class from index.css */}
          <div className="flex-1 overflow-y-auto pr-4 custom-scrollbar">
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
        <RightSidebar />

      </div>
  );
}