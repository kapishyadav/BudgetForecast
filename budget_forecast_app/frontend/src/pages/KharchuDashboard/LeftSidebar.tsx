import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard } from 'lucide-react';
import {
  Home,
  Share2, // Note: You imported this but aren't using it yet!
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
  const isUpload = location.pathname === '/upload';
  const isIntegrations = location.pathname === '/integrations';

  // FIX: Replaced dark:text-black with dark:text-sidebar-foreground and dark:text-muted-foreground
  const activeClass = "text-white bg-white/20 dark:text-sidebar-foreground dark:bg-white/10 p-2 rounded-xl transition-colors duration-300";
  const inactiveClass = "text-gray-400 hover:text-white dark:text-muted-foreground dark:hover:text-sidebar-foreground transition-colors duration-300";

  return (
    <div className="w-20 bg-[#1D1B1B] dark:bg-background h-[92vh] rounded-[30px] flex flex-col items-center py-6 mx-4 my-auto justify-between transition-colors duration-300">
      <div className="flex flex-col items-center space-y-6">

        {/* Logo FIX: Changed dark:bg-black/10 and dark:text-black to light/transparent versions */}
        <Link
          to="/"
          className="w-10 h-10 bg-white/10 dark:bg-white/5 rounded-xl flex items-center justify-center mb-4 hover:bg-white/20 dark:hover:bg-white/10 transition-colors duration-300 cursor-pointer"
          title="Go to Home"
        >
          <span className="text-white dark:text-sidebar-foreground font-bold text-xl transition-colors duration-300">K</span>
        </Link>

        {/* Navigation Icons */}
        <Link
          to="/"
          className={isHome ? activeClass : inactiveClass}
        >
          <Home size={20} />
        </Link>

        <Link
          to="/upload"
          className={isUpload ? activeClass : inactiveClass}
          title="Upload File"
        >
          <UploadCloud size={20} />
        </Link>

        <Link
          to="/kharchu"
          className={isDashboard ? activeClass : inactiveClass}
          title="Go to Dashboard"
        >
          <LayoutDashboard size={20} />
        </Link>

        <Link
          to="/integrations"
          className={isIntegrations ? activeClass : inactiveClass}
          title="Cloud Integrations"
        >
          <LinkIcon size={20} />
        </Link>
        <button className={inactiveClass}>
          <Globe size={20} />
        </button>
        <button className={inactiveClass}>
          <MoreHorizontal size={20} />
        </button>
      </div>

      <div className="flex flex-col items-center space-y-6">
        <button className={inactiveClass}>
          <BookOpen size={20} />
        </button>
        <button className={inactiveClass}>
          <Rocket size={20} />
        </button>
        <button className={inactiveClass}>
          <HelpCircle size={20} />
        </button>

        {/* Avatar FIX: Replaced dark:border-black/20 with dark:border-border */}
        <div className="mt-4">
          <img
            src={`https://api.dicebear.com/7.x/notionists/svg?seed=Felix`}
            alt="User avatar"
            className="w-10 h-10 rounded-full border border-gray-600 dark:border-border bg-gray-800 transition-colors duration-300"
          />
        </div>
      </div>
    </div>
  );
}