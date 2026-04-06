import { Settings, Plus, LogIn, LogOut, Sun, Moon } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';

export function Header() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();

  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  useEffect(() => {
    const scrollContainer = document.getElementById('main-scroll-area');

    if (!scrollContainer) return;

    const handleScroll = () => {
      const currentScrollY = scrollContainer.scrollTop;

      if (currentScrollY > lastScrollY && currentScrollY > 50) {
        setIsVisible(false);
      }
      else if (currentScrollY < lastScrollY) {
        setIsVisible(true);
      }

      setLastScrollY(currentScrollY);
    };

    scrollContainer.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      scrollContainer.removeEventListener('scroll', handleScroll);
    };
  }, [lastScrollY]);

  const isAuthenticated = localStorage.getItem('access_token') !== null;

  const handleAuthAction = () => {
    if (isAuthenticated) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      navigate(0);
    } else {
      navigate('/login');
    }
  };

  return (
    <header
      className={`sticky top-0 z-50 pt-8 pb-4 bg-background transition-all duration-300 ease-in-out ${
        isVisible ? 'translate-y-0' : '-translate-y-full'
      }`}
    >
      <div className="w-full px-8">
        <div className="flex justify-between items-center mb-6">

          {/* Titles */}
          <div>
            <h1 className="text-4xl font-semibold text-foreground tracking-tight mb-1 transition-colors">
              KHARCHU
            </h1>
            <p className="text-lg text-muted-foreground transition-colors">
              Interactive Budget Forecasting Dashboard
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-3">

            {/* Dynamic Dark Mode Toggle */}
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

            {/* Upload Button */}
            <Link
              to="/upload"
              className="flex items-center space-x-2 bg-primary text-primary-foreground px-6 py-3 rounded-2xl hover:opacity-90 transition-opacity font-medium cursor-pointer shadow-sm"
            >
              <Plus size={18} />
              <span>Upload a New File</span>
            </Link>

            {/* Dynamic Auth Button */}
            <button
              onClick={handleAuthAction}
              className={`flex items-center space-x-2 px-6 py-3 rounded-2xl transition-all font-medium cursor-pointer shadow-sm border border-border ${
                isAuthenticated
                  ? 'bg-card text-red-500 hover:bg-muted' // Standard Tailwind red works great for destructive actions
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
                  <span>Login / Sign up</span>
                </>
              )}
            </button>

          </div>
        </div>
      </div>
    </header>
  );
}