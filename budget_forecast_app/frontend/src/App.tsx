import { Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { LandingPage } from './pages/LandingPage';
import { KharchuDashboard } from './pages/KharchuDashboard/KharchuDashboard';

export default function App() {
  return (
    <ThemeProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/kharchu" element={<KharchuDashboard />} />
      </Routes>
    </ThemeProvider>
  );
}