import { Settings, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';

export function TopHeader() {
  return (
    <div className="flex justify-between items-start mb-6">
      <div>
        <h1 className="text-4xl font-semibold text-[#1A1A1A] tracking-tight mb-1">
          KHARCHU
        </h1>
        <p className="text-lg text-gray-600">
          Interactive Budget & Spend Forecasting Dashboard
        </p>
      </div>
      <div className="flex items-center space-x-3">
        <button className="p-3 bg-white rounded-2xl shadow-sm hover:shadow-md transition-shadow">
          <Settings size={20} className="text-gray-600" />
        </button>
        {/* Make sure to import { Link } from 'react-router-dom' at the top of your file if it isn't already there! */}

        <Link
          to="/upload"
          className="flex items-center space-x-2 bg-[#1A1A1A] text-white px-6 py-3 rounded-2xl hover:bg-black transition-colors font-medium cursor-pointer"
        >
          <Plus size={18} />
          <span>Upload a New File</span>
        </Link>
      </div>
    </div>
  );
}
