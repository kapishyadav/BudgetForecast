import React, { useState } from 'react';
import {
  ArrowUpRight, MessageSquare, GraduationCap, HelpCircle,
  Users, BookMarked, BarChart3, ChevronLeft, ChevronRight
} from 'lucide-react';

export function RightSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div
      className={`relative h-full transition-all duration-300 ease-in-out border-l border-border bg-background
        ${isCollapsed ? 'w-12' : 'w-80'}
      `}
    >
      {/* Toggle Button: Floating on the border */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -left-3 top-30 z-10 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-card text-muted-foreground shadow-sm hover:text-foreground transition-all duration-200"
        aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {isCollapsed ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
      </button>

      {/* Content Wrapper: Controls visibility and prevents layout "jank" during animation */}
      <div className={`flex flex-col space-y-4 h-full p-4 overflow-hidden transition-opacity duration-200
        ${isCollapsed ? 'opacity-0 pointer-events-none' : 'opacity-100'}
      `}>

        {/* Top 2 buttons */}
        <div className="grid grid-cols-2 gap-4">
          <button className="bg-card rounded-[24px] p-4 flex flex-col items-center justify-center hover:bg-muted transition-colors duration-300 shadow-sm border border-border">
            <MessageSquare size={24} className="mb-2 text-muted-foreground transition-colors duration-300" />
            <span className="text-sm font-medium text-card-foreground text-center leading-tight transition-colors duration-300">Forecasting<br/>Forum</span>
          </button>
          <button className="bg-card rounded-[24px] p-4 flex flex-col items-center justify-center hover:bg-muted transition-colors duration-300 shadow-sm border border-border">
            <GraduationCap size={24} className="mb-2 text-muted-foreground transition-colors duration-300" />
            <span className="text-sm font-medium text-card-foreground text-center leading-tight transition-colors duration-300">Budgeting<br/>Workshops</span>
          </button>
        </div>

        {/* List items */}
        <div className="flex-1 overflow-y-auto space-y-3 pb-4">
          <ResourceItem
            icon={<HelpCircle size={20} />}
            title="Best Practices Guides"
            description="Explore our detailed documentation..."
          />
          <ResourceItem
            icon={<Users size={20} />}
            title="API Integrations"
            description="Find the perfect partner to support..."
          />
          <ResourceItem
            icon={<BookMarked size={20} />}
            title="Industry Spend Reports"
            description="Access popular guides & stories ab..."
          />
          <ResourceItem
            icon={<BarChart3 size={20} />}
            title="Client Case Studies"
            description="Get inspired by all the ways you ca..."
          />
        </div>
      </div>
    </div>
  );
}

function ResourceItem({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <button className="w-full text-left bg-transparent hover:bg-muted rounded-[20px] p-4 flex items-start space-x-4 transition-all duration-300 group">
      <div className="bg-card p-2 rounded-xl shadow-sm border border-border text-muted-foreground group-hover:text-foreground transition-colors duration-300">
        {icon}
      </div>
      <div className="flex-1">
        <div className="flex justify-between items-center mb-1">
          <h4 className="font-medium text-foreground text-sm transition-colors duration-300">{title}</h4>
          <ArrowUpRight size={16} className="text-muted-foreground group-hover:text-foreground transition-colors duration-300" />
        </div>
        <p className="text-xs text-muted-foreground line-clamp-1 transition-colors duration-300">{description}</p>
      </div>
    </button>
  );
}