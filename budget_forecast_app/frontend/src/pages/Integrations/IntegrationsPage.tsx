import React from 'react';
import { LeftSidebar } from '../KharchuDashboard/LeftSidebar';
import { TopHeader } from '../KharchuDashboard/TopHeader';
import { RightSidebar } from '../KharchuDashboard/RightSidebar';
import { IntegrationsManager } from './IntegrationsManager';

export function IntegrationsPage() {
  return (
    <div className="h-screen w-screen bg-background flex overflow-hidden transition-colors duration-300">
      <LeftSidebar />

      <div className="flex-1 flex flex-col py-8 px-2 overflow-hidden">
        <TopHeader />

        <div className="flex-1 overflow-y-auto pr-4 custom-scrollbar">
          <div className="mt-4">
            <IntegrationsManager />
          </div>
        </div>
      </div>

      <RightSidebar />
    </div>
  );
}