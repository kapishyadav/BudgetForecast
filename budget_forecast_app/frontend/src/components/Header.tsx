import { Settings, Plus, LogIn, LogOut } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export function Header() {
  const navigate = useNavigate();

  // Check if the user is logged in by looking for the token
  const isAuthenticated = localStorage.getItem('access_token') !== null;

  const handleAuthAction = () => {
    if (isAuthenticated) {
      // --- SIGN OUT LOGIC ---
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      // Force a re-render of the page to instantly update the button UI
      navigate(0);
    } else {
      // --- LOGIN LOGIC ---
      navigate('/login');
    }
  };

  return (
    <header className="sticky top-0 z-50 pt-4 pb-2" style={{
      transition: 'var(--transition)'
    }}>
      {/* Added the exact same container classes here as your Hero component
        to guarantee perfect edge-to-edge alignment.
      */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        <div className="flex justify-between items-center mb-6">

          {/* Titles */}
          <div>
            <h1 className="text-4xl font-semibold text-[#1A1A1A] tracking-tight mb-1">
              KHARCHU
            </h1>
            <p className="text-lg text-gray-600">
              Keep Your Cloud Kharchu Under Control
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-3">

            {/* Settings */}
            <button className="p-3 bg-white rounded-2xl shadow-sm hover:shadow-md transition-shadow">
              <Settings size={20} className="text-gray-600" />
            </button>

            {/* Upload */}
            <Link
              to="/upload"
              className="flex items-center space-x-2 bg-[#1A1A1A] text-white px-6 py-3 rounded-2xl hover:bg-black transition-colors font-medium cursor-pointer"
            >
              <Plus size={18} />
              <span>Upload a New File</span>
            </Link>

            {/* NEW: Dynamic Auth Button */}
            <button
              onClick={handleAuthAction}
              className={`flex items-center space-x-2 px-6 py-3 rounded-2xl transition-colors font-medium cursor-pointer shadow-sm border ${
                isAuthenticated
                  ? 'bg-red-50 text-red-600 hover:bg-red-100 border-red-100' // Logged In Style
                  : 'bg-white text-[#1A1A1A] hover:bg-gray-50 border-gray-200' // Logged Out Style
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