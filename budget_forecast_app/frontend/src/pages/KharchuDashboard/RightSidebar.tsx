import { ArrowUpRight, MessageSquare, GraduationCap, HelpCircle, Users, BookMarked, BarChart3 } from 'lucide-react';

export function RightSidebar() {
  return (
    <div className="w-72 flex flex-col space-y-4">
      {/* Top 2 buttons */}
      <div className="grid grid-cols-2 gap-4">
        <button className="bg-white rounded-[24px] p-4 flex flex-col items-center justify-center hover:bg-gray-50 transition-colors shadow-sm">
          <MessageSquare size={24} className="mb-2 text-gray-700" />
          <span className="text-sm font-medium text-gray-800 text-center leading-tight">Forecasting<br/>Forum</span>
        </button>
        <button className="bg-white rounded-[24px] p-4 flex flex-col items-center justify-center hover:bg-gray-50 transition-colors shadow-sm">
          <GraduationCap size={24} className="mb-2 text-gray-700" />
          <span className="text-sm font-medium text-gray-800 text-center leading-tight">Budgeting<br/>Workshops</span>
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
    <button className="w-full text-left bg-transparent hover:bg-black/5 rounded-[20px] p-4 flex items-start space-x-4 transition-colors group">
      <div className="bg-white p-2 rounded-xl shadow-sm text-gray-600 group-hover:text-[#1A1A1A]">
        {icon}
      </div>
      <div className="flex-1">
        <div className="flex justify-between items-center mb-1">
          <h4 className="font-medium text-[#1A1A1A] text-sm">{title}</h4>
          <ArrowUpRight size={16} className="text-gray-400 group-hover:text-[#1A1A1A]" />
        </div>
        <p className="text-xs text-gray-500 line-clamp-1">{description}</p>
      </div>
    </button>
  );
}
