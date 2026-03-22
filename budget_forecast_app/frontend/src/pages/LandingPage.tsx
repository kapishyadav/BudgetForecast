import { Hero } from '../components/Hero';
import { Features } from '../components/Features';
import { ForecastDemo } from '../components/ForecastDemo';
import { CTA } from '../components/CTA';
import { Header } from '../components/Header';
import { LeftSidebar } from './KharchuDashboard/LeftSidebar';

export function LandingPage() {
  return (
    <div className="min-h-screen bg-[#E5E0D8] p-4 flex justify-center items-center">
      <div className="bg-[#F5F1EB] rounded-[40px] shadow-2xl w-full max-w-[1600px] h-[95vh] flex overflow-hidden border border-white/40">
        <LeftSidebar />

        <div className="flex-[3] flex flex-col overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-gray-300">
          <Header />
          <Hero />
          <Features />
          <ForecastDemo />
          <CTA />
        </div>
      </div>
    </div>
  );
}