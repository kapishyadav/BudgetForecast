import { Hero } from '../components/Hero';
import { Features } from '../components/Features';
import { ForecastDemo } from '../components/ForecastDemo';
import { CTA } from '../components/CTA';
import { Header } from '../components/Header';
import { LeftSidebar } from './KharchuDashboard/LeftSidebar';

export function LandingPage() {
  return (
    <div className="h-screen w-screen bg-background flex overflow-hidden transition-colors duration-300">

        <LeftSidebar />

        <div id="main-scroll-area" className="flex-[3] flex flex-col overflow-y-auto overflow-x-hidden custom-scrollbar">
          <Header />
          <Hero />
          <Features />
          <ForecastDemo />
          <CTA />
        </div>
      </div>
  );
}