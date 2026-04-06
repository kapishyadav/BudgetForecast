import { ArrowUpRight, MessageSquare, GraduationCap, HelpCircle, Users, BookMarked, BarChart3 } from 'lucide-react';

export function RightSidebar() {
  return (
    <div className="w-72 flex flex-col space-y-4">
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
          description="Explore our detailed documentatio..."
        />
        <ResourceItem
          icon={<Users size={20} />}
          title="API Integrations"
          description="Find the perfect partner to suppor..."
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
  );
}

function ResourceItem({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    // Replaced hover:bg-black/5 with hover:bg-muted
    <button className="w-full text-left bg-transparent hover:bg-muted rounded-[20px] p-4 flex items-start space-x-4 transition-all duration-300 group">

      {/* Icon Container: Replaced bg-white/dark:bg-gray-800 with bg-card and added border */}
      <div className="bg-card p-2 rounded-xl shadow-sm border border-border text-muted-foreground group-hover:text-foreground transition-colors duration-300">
        {icon}
      </div>

      <div className="flex-1">
        <div className="flex justify-between items-center mb-1">
          {/* Title: Replaced text-[#1A1A1A] with text-foreground */}
          <h4 className="font-medium text-foreground text-sm transition-colors duration-300">{title}</h4>
          {/* Arrow Icon: Swaps to text-foreground on hover */}
          <ArrowUpRight size={16} className="text-muted-foreground group-hover:text-foreground transition-colors duration-300" />
        </div>
        {/* Description: Replaced text-gray-500 with text-muted-foreground */}
        <p className="text-xs text-muted-foreground line-clamp-1 transition-colors duration-300">{description}</p>
      </div>
    </button>
  );
}