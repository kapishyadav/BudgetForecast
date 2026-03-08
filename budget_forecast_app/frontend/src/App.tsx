import { Hero } from './components/Hero';
import { Features } from './components/Features';
import { ForecastDemo } from './components/ForecastDemo';
import { CTA } from './components/CTA';
import { Header } from './components/Header';
import { ThemeProvider } from './contexts/ThemeContext';

export default function App() {
  return (
    <ThemeProvider>
      <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-color)' }}>
        <Header />
        <Hero />
        <Features />
        <ForecastDemo />
        <CTA />
      </div>
    </ThemeProvider>
  );
}