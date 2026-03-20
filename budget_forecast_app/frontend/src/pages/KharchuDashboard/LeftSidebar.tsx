import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  Share2,
  UploadCloud,
  Link as LinkIcon,
  Globe,
  MoreHorizontal,
  BookOpen,
  Rocket,
  HelpCircle
} from 'lucide-react';

export function LeftSidebar() {
  const location = useLocation();
  const isHome = location.pathname === '/';
  const isDashboard = location.pathname === '/kharchu';

  return (
    <div className="w-14 bg-[#1D1B1B] h-[90vh] rounded-[40px] flex flex-col items-center py-6 mx-4 my-auto justify-between shadow-lg">
      <div className="flex flex-col items-center space-y-6">
        {/* Logo */}
        <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center mb-4">
          <span className="text-white font-bold text-xl">K</span>
        </div>

        {/* Navigation Icons */}
        <Link
          to="/"
          className={`transition-colors ${isHome ? 'text-white bg-white/20 p-2 rounded-xl' : 'text-gray-400 hover:text-white'}`}
        >
          <Home size={20} />
        </Link>
        <button className="text-gray-400 hover:text-white transition-colors">
          <Share2 size={20} />
        </button>
        <Link
          to="/kharchu"
          className={`transition-colors ${isDashboard ? 'text-white bg-white/20 p-2 rounded-xl' : 'text-gray-400 hover:text-white'}`}
        >
          <UploadCloud size={20} />
        </Link>
        <button className="text-gray-400 hover:text-white transition-colors">
          <LinkIcon size={20} />
        </button>
        <button className="text-gray-400 hover:text-white transition-colors">
          <Globe size={20} />
        </button>
        <button className="text-gray-400 hover:text-white transition-colors">
          <MoreHorizontal size={20} />
        </button>
      </div>

      <div className="flex flex-col items-center space-y-6">
        <button className="text-gray-400 hover:text-white transition-colors">
          <BookOpen size={20} />
        </button>
        <button className="text-gray-400 hover:text-white transition-colors">
          <Rocket size={20} />
        </button>
        <button className="text-gray-400 hover:text-white transition-colors">
          <HelpCircle size={20} />
        </button>

        {/* Avatar */}
        <div className="mt-4">
          <img
            src={`https://api.dicebear.com/7.x/notionists/svg?seed=Felix`}
            alt="User avatar"
            className="w-10 h-10 rounded-full border border-gray-600 bg-gray-800"
          />
        </div>
      </div>
    </div>
  );
}
