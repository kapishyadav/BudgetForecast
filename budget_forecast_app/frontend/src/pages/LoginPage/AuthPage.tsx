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

    const form = e.target as HTMLFormElement;
    const email = (form.elements.namedItem('email') as HTMLInputElement).value;
    const password = (form.elements.namedItem('password') as HTMLInputElement).value;

    try {
      if (isLogin) {
        const response = await fetch('http://localhost:8001/api/token/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: email, password: password }),
        });

        if (response.ok) {
          const data = await response.json();
          localStorage.setItem('access_token', data.access);
          localStorage.setItem('refresh_token', data.refresh);
          navigate('/kharchu');
        } else {
          setErrorMessage("Invalid email or password. Please try again.");
        }
      } else {
        const fullName = (form.elements.namedItem('fullName') as HTMLInputElement).value;
        const response = await fetch('http://localhost:8001/api/register/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, name: fullName }),
        });

        if (response.ok) {
          setSuccessMessage("Account created successfully! Please log in.");
          setIsLogin(true);
          form.reset();
        } else {
          setErrorMessage("Registration failed. That email might already be in use.");
        }
      }
    } catch (error) {
      setErrorMessage("Network error. Please check if the server is running.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    // Changed: bg-[#E5E0D8] -> bg-background
    <div className="min-h-screen bg-background p-4 flex justify-center items-center transition-colors duration-500">

      {/* Changed: bg-white -> bg-card | border-gray-100 -> border-border */}
      <div className="bg-card rounded-[32px] shadow-xl w-full max-w-md p-8 border border-border relative overflow-hidden transition-colors duration-500">

        {/* Decorative Blur - updated to be more subtle in dark mode */}
        <div className="absolute -top-[20%] -right-[20%] w-[50%] h-[50%] rounded-full bg-muted blur-[80px] pointer-events-none opacity-50"></div>

        <div className="relative z-10">
          <div className="flex justify-center mb-6">
            {/* Changed: bg-gray-50 -> bg-muted | text-gray-500 -> text-muted-foreground */}
            <div className="bg-muted p-3 rounded-full text-muted-foreground border border-border shadow-sm">
              <BarChart3 size={28} className="text-foreground" />
            </div>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-foreground tracking-tight mb-2">
              {isLogin ? 'Welcome back' : 'Create an account'}
            </h2>
            <p className="text-muted-foreground text-sm">
              {isLogin ? "Don't have an account? " : "Already have an account? "}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setErrorMessage(null);
                  setSuccessMessage(null);
                }}
                className="font-semibold text-foreground hover:opacity-70 transition-all underline-offset-4 hover:underline"
              >
                {isLogin ? 'Sign up' : 'Log in'}
              </button>
            </p>
          </div>

          {/* Error and Success Messages */}
          {errorMessage && (
            <div className="mb-4 p-3 bg-red-500/10 text-red-500 text-sm rounded-xl border border-red-500/20 text-center">
              {errorMessage}
            </div>
          )}
          {successMessage && (
            <div className="mb-4 p-3 bg-green-500/10 text-green-500 text-sm rounded-xl border border-green-500/20 text-center">
              {successMessage}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5 ml-1">
                  Full Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <input
                    name="fullName"
                    type="text"
                    required
                    className="block w-full pl-11 pr-4 py-3.5 bg-muted border border-border rounded-[16px] text-foreground focus:ring-2 focus:ring-foreground focus:border-transparent sm:text-sm transition-all outline-none placeholder:text-muted-foreground/50"
                    placeholder="Jane Doe"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5 ml-1">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-muted-foreground" />
                </div>
                <input
                  name="email"
                  type="email"
                  required
                  className="block w-full pl-11 pr-4 py-3.5 bg-muted border border-border rounded-[16px] text-foreground focus:ring-2 focus:ring-foreground focus:border-transparent sm:text-sm transition-all outline-none placeholder:text-muted-foreground/50"
                  placeholder="you@company.com"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5 ml-1 mr-1">
                <label className="block text-sm font-medium text-foreground">
                  Password
                </label>
                {isLogin && (
                  <a href="#" className="text-xs font-medium text-muted-foreground hover:text-foreground transition-colors">
                    Forgot password?
                  </a>
                )}
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-muted-foreground" />
                </div>
                <input
                  name="password"
                  type="password"
                  required
                  className="block w-full pl-11 pr-4 py-3.5 bg-muted border border-border rounded-[16px] text-foreground focus:ring-2 focus:ring-foreground focus:border-transparent sm:text-sm transition-all outline-none placeholder:text-muted-foreground/50"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {/* Submit Button - Uses inverse colors for high contrast */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 flex justify-center items-center gap-2 py-4 px-4 rounded-[16px] text-sm font-semibold transition-all shadow-sm group disabled:opacity-70 disabled:cursor-not-allowed
                bg-foreground text-background hover:opacity-90 active:scale-[0.98]"
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