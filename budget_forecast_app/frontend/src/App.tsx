import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { LandingPage } from './pages/LandingPage';
import { KharchuDashboard } from './pages/KharchuDashboard/KharchuDashboard';
import { UploadPage } from './pages/UploadPage/UploadPage';
import { AuthPage } from './pages/LoginPage/AuthPage';

// The Bouncer: Protects routes from unauthenticated users
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  // Check if the user has a token stored from a successful Django login
  const isAuthenticated = localStorage.getItem('access_token') !== null;

  if (!isAuthenticated) {
    // If no token is found, kick them back to the login page
    return <Navigate to="/login" replace />;
  }

  // If they have a token, let them through!
  return <>{children}</>;
}

export default function App() {
  return (
    <ThemeProvider>
      <Routes>
        {/* Public Routes (Anyone can see these) */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<AuthPage />} />

        {/* Protected Routes (Requires Login) */}
        <Route
          path="/kharchu"
          element={
            <ProtectedRoute>
              <KharchuDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/upload"
          element={
            <ProtectedRoute>
              <UploadPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </ThemeProvider>
  );
}