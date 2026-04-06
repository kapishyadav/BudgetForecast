import { Plus, LogOut, LogIn, Sun, Moon } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext'; // Ensure this path matches your project structure

export function TopHeader() {
  const navigate = useNavigate();
  // Consume the theme context
  const { theme, toggleTheme } = useTheme();

  // Check if the user is logged in by looking for the token
  const isAuthenticated = localStorage.getItem('access_token') !== null;

  const handleAuthAction = () => {
    if (isAuthenticated) {
      // --- SIGN OUT LOGIC ---
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      navigate('/'); // Kick them back to the landing page
    } else {
      // --- LOGIN LOGIC ---
      navigate('/login'); // Send them to the auth page
    }
  };

  return (
    <div className="flex justify-between items-start mb-6 transition-colors">

      {/* Title Section */}
      <div className="-mt-0">
        {/* Added dark:text-white */}
        <h1 className="text-4xl font-semibold text-[#1A1A1A] dark:text-white tracking-tight mb-1 transition-colors">
          KHARCHU
        </h1>
        {/* Added dark:text-gray-400 */}
        <p className="text-lg text-gray-600 dark:text-gray-400 transition-colors">
          Interactive Budget Forecasting Dashboard
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center space-x-3">

        {/* NEW: Dynamic Dark Mode Toggle */}
        <button
          onClick={toggleTheme}
          className="p-3 bg-white dark:bg-gray-800 rounded-2xl shadow-sm hover:shadow-md transition-all cursor-pointer border border-transparent dark:border-gray-700"
          aria-label="Toggle Dark Mode"
        >
          {theme === 'dark' ? (
            <Sun size={20} className="text-yellow-500" />
          ) : (
            <Moon size={20} className="text-gray-600" />
          )}
        </button>

        {/* Upload Button: Matched to landing page dark mode styling */}
        <Link
          to="/upload"
          className="flex items-center space-x-2 bg-[#1A1A1A] dark:bg-blue-600 text-white px-6 py-3 rounded-2xl hover:bg-black dark:hover:bg-blue-700 transition-colors font-medium cursor-pointer"
        >
          <Plus size={18} />
          <span>Upload a New File</span>
        </Link>

        {/* Dynamic Auth Button */}
        <button
          onClick={handleAuthAction}
          className={`flex items-center space-x-2 px-6 py-3 rounded-2xl transition-colors font-medium cursor-pointer shadow-sm border ${
            isAuthenticated
              ? 'bg-red-50 text-red-600 hover:bg-red-100 border-red-100 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800' // Logged In Style (Dark mode supported)
              : 'bg-white text-[#1A1A1A] hover:bg-gray-50 border-gray-200 dark:bg-gray-800 dark:text-white dark:border-gray-700 dark:hover:bg-gray-700' // Logged Out Style (Dark mode supported)
          }`}
        >
          {isAuthenticated ? (
            <>
              <LogOut size={18} />
              <span>Sign Out</span>
            </>
          ) : (
            <>
              <LogIn size={18} />
              <span>Login / Signup</span>
            </>
          )}
        </button>

      </div>
    </div>
  );
}