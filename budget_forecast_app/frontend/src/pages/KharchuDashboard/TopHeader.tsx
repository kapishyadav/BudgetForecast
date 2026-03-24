import { Settings, Plus, LogOut, LogIn } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export function TopHeader() {
  const navigate = useNavigate();

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
    <div className="flex justify-between items-start mb-6">

      {/* Title Section */}
      <div>
        <h1 className="text-4xl font-semibold text-[#1A1A1A] tracking-tight mb-1">
          KHARCHU
        </h1>
        <p className="text-lg text-gray-600">
          Interactive Budget Forecasting Dashboard
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center space-x-3">

        {/* Settings Button */}
        <button className="p-3 bg-white rounded-2xl shadow-sm hover:shadow-md transition-shadow">
          <Settings size={20} className="text-gray-600" />
        </button>

        {/* Upload Button */}
        <Link
          to="/upload"
          className="flex items-center space-x-2 bg-[#1A1A1A] text-white px-6 py-3 rounded-2xl hover:bg-black transition-colors font-medium cursor-pointer"
        >
          <Plus size={18} />
          <span>Upload a New File</span>
        </Link>

        {/* Dynamic Auth Button */}
        <button
          onClick={handleAuthAction}
          className={`flex items-center space-x-2 px-6 py-3 rounded-2xl transition-colors font-medium cursor-pointer shadow-sm border ${
            isAuthenticated
              ? 'bg-red-20 text-red-60 hover:bg-red-100 border-red-100' // Logged In Style
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
              <span>Login / Signup</span>
            </>
          )}
        </button>

      </div>
    </div>
  );
}