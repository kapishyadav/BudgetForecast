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
    <div className="flex justify-between items-start mb-6 transition-colors duration-300">

      {/* Title Section */}
      <div className="-mt-0">
        {/* Replaced text-[#1A1A1A] and dark:text-white with text-foreground */}
        <h1 className="text-4xl font-semibold text-foreground tracking-tight mb-1 transition-colors duration-300">
          KHARCHU
        </h1>
        {/* Replaced text-gray-600 and dark:text-gray-400 with text-muted-foreground */}
        <p className="text-lg text-muted-foreground transition-colors duration-300">
          Interactive Budget Forecasting Dashboard
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center space-x-3">

        {/* Dynamic Dark Mode Toggle: Replaced hardcoded backgrounds with bg-card and border-border */}
        <button
          onClick={toggleTheme}
          className="p-3 bg-card text-foreground rounded-2xl shadow-sm hover:shadow-md transition-all cursor-pointer border border-border"
          aria-label="Toggle Dark Mode"
        >
          {theme === 'dark' ? (
            <Sun size={20} className="text-foreground transition-colors" />
          ) : (
            <Moon size={20} className="text-foreground transition-colors" />
          )}
        </button>

        {/* Upload Button: Uses primary theme variables for automatic black/white flip */}
        <Link
          to="/upload"
          className="flex items-center space-x-2 bg-primary text-primary-foreground px-6 py-3 rounded-2xl hover:opacity-90 transition-opacity font-medium cursor-pointer shadow-sm"
        >
          <Plus size={18} />
          <span>Upload a New File</span>
        </Link>

        {/* Dynamic Auth Button: Unified using bg-card and border-border */}
        <button
          onClick={handleAuthAction}
          className={`flex items-center space-x-2 px-6 py-3 rounded-2xl transition-all font-medium cursor-pointer shadow-sm border border-border ${
            isAuthenticated
              ? 'bg-card text-red-500 hover:bg-muted'
              : 'bg-card text-foreground hover:bg-muted'
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