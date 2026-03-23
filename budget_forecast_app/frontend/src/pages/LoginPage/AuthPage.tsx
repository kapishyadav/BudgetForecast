import { useState } from 'react';
import { Mail, Lock, ArrowRight, BarChart3, User, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    // Grab values directly from the form
    const form = e.target as HTMLFormElement;
    const email = (form.elements.namedItem('email') as HTMLInputElement).value;
    const password = (form.elements.namedItem('password') as HTMLInputElement).value;

    try {
      if (isLogin) {
        // --- LOGIN LOGIC ---
        const response = await fetch('http://localhost:8001/api/token/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          // Note: Django's default auth expects "username", so we map email to it
          body: JSON.stringify({ username: email, password: password }),
        });

        if (response.ok) {
          const data = await response.json();
          // Save tokens to local storage
          localStorage.setItem('access_token', data.access);
          localStorage.setItem('refresh_token', data.refresh);

          // Send user to the protected dashboard
          navigate('/kharchu');
        } else {
          setErrorMessage("Invalid email or password. Please try again.");
        }

      } else {
        // --- SIGN UP LOGIC ---
        const fullName = (form.elements.namedItem('fullName') as HTMLInputElement).value;

        // Assuming you make an endpoint called /api/register/ in Django
        const response = await fetch('http://localhost:8001/api/register/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email, password, name: fullName }),
        });

        if (response.ok) {
          setSuccessMessage("Account created successfully! Please log in.");
          setIsLogin(true); // Switch to login view
          form.reset(); // Clear the form
        } else {
          setErrorMessage("Registration failed. That email might already be in use.");
        }
      }
    } catch (error) {
      console.error("Auth error:", error);
      setErrorMessage("Network error. Please check if the server is running.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#E5E0D8] p-4 flex justify-center items-center">
      <div className="bg-white rounded-[32px] shadow-xl w-full max-w-md p-8 border border-gray-100 relative overflow-hidden">
        <div className="absolute -top-[20%] -right-[20%] w-[50%] h-[50%] rounded-full bg-gray-100 blur-[80px] pointer-events-none"></div>

        <div className="relative z-10">
          <div className="flex justify-center mb-6">
            <div className="bg-gray-50 p-3 rounded-full text-gray-500 border border-gray-100 shadow-sm">
              <BarChart3 size={28} className="text-[#1A1A1A]" />
            </div>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-[#1A1A1A] tracking-tight mb-2">
              {isLogin ? 'Welcome back' : 'Create an account'}
            </h2>
            <p className="text-gray-500 text-sm">
              {isLogin ? "Don't have an account? " : "Already have an account? "}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setErrorMessage(null);
                  setSuccessMessage(null);
                }}
                className="font-semibold text-[#1A1A1A] hover:text-gray-600 transition-colors"
              >
                {isLogin ? 'Sign up' : 'Log in'}
              </button>
            </p>
          </div>

          {/* Error and Success Messages */}
          {errorMessage && (
            <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-xl border border-red-100 text-center">
              {errorMessage}
            </div>
          )}
          {successMessage && (
            <div className="mb-4 p-3 bg-green-50 text-green-700 text-sm rounded-xl border border-green-100 text-center">
              {successMessage}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-[#1A1A1A] mb-1.5 ml-1">
                  Full Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-gray-400" />
                  </div>
                  {/* ADDED name="fullName" HERE */}
                  <input
                    name="fullName"
                    type="text"
                    required
                    className="block w-full pl-11 pr-4 py-3.5 bg-gray-50 border border-gray-200 rounded-[16px] focus:bg-white focus:ring-2 focus:ring-[#1A1A1A] focus:border-transparent sm:text-sm transition-all outline-none"
                    placeholder="Jane Doe"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-[#1A1A1A] mb-1.5 ml-1">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  name="email"
                  type="email"
                  required
                  className="block w-full pl-11 pr-4 py-3.5 bg-gray-50 border border-gray-200 rounded-[16px] focus:bg-white focus:ring-2 focus:ring-[#1A1A1A] focus:border-transparent sm:text-sm transition-all outline-none"
                  placeholder="you@company.com"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5 ml-1 mr-1">
                <label className="block text-sm font-medium text-[#1A1A1A]">
                  Password
                </label>
                {isLogin && (
                  <a href="#" className="text-xs font-medium text-gray-500 hover:text-[#1A1A1A] transition-colors">
                    Forgot password?
                  </a>
                )}
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  name="password"
                  type="password"
                  required
                  className="block w-full pl-11 pr-4 py-3.5 bg-gray-50 border border-gray-200 rounded-[16px] focus:bg-white focus:ring-2 focus:ring-[#1A1A1A] focus:border-transparent sm:text-sm transition-all outline-none"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 flex justify-center items-center gap-2 py-4 px-4 rounded-[16px] text-sm font-medium text-white bg-[#1A1A1A] hover:bg-black focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#1A1A1A] transition-all shadow-sm group disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  {isLogin ? 'Sign In' : 'Create Account'}
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}