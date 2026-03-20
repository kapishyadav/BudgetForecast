import { ArrowRight } from 'lucide-react';

export function CTA() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-32">
      <div 
        className="p-16 text-center text-white relative overflow-hidden"
        style={{ 
          backgroundColor: 'var(--primary)',
          borderRadius: 'var(--radius)',
          boxShadow: '16px 16px 0 var(--accent)'
        }}
      >
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
          <div className="absolute top-10 left-10 text-6xl">☕</div>
          <div className="absolute top-20 right-20 text-5xl rotate-45">📊</div>
          <div className="absolute bottom-10 left-1/4 text-4xl">💰</div>
          <div className="absolute bottom-20 right-10 text-5xl -rotate-12">📈</div>
        </div>

        <div className="relative z-10">
          <div className="inline-block mb-6 px-6 py-2" style={{
            backgroundColor: 'var(--accent)',
            color: 'white',
            borderRadius: 'var(--radius)',
            boxShadow: '3px 3px 0 rgba(255,255,255,0.2)'
          }}>
            Get Started Today
          </div>
          
          <h2 className="mb-6 text-white" style={{ fontSize: 'clamp(2rem, 4vw, 2.5rem)' }}>
            Ready to Optimize Your AWS Budget?
          </h2>
          <p className="max-w-2xl mx-auto mb-12 text-lg" style={{ color: 'var(--light-accent)' }}>
            Start forecasting your AWS spending today and gain the insights you need to make smarter financial decisions.
          </p>
          <div className="flex flex-wrap justify-center gap-6">
            <button 
              className="px-12 py-5 flex items-center gap-3 group"
              style={{ 
                backgroundColor: 'var(--accent)',
                color: 'white',
                borderRadius: 'var(--radius)',
                boxShadow: '6px 6px 0 rgba(255,255,255,0.3)',
                transition: 'var(--transition)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translate(6px, 6px)';
                e.currentTarget.style.boxShadow = '0px 0px 0 rgba(255,255,255,0.3)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translate(0, 0)';
                e.currentTarget.style.boxShadow = '6px 6px 0 rgba(255,255,255,0.3)';
              }}
            >
              Start Free Trial
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <button 
              className="px-12 py-5"
              style={{ 
                backgroundColor: 'transparent',
                color: 'white',
                borderRadius: 'var(--radius)',
                border: '3px solid white',
                boxShadow: '6px 6px 0 var(--light-accent)',
                transition: 'var(--transition)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translate(6px, 6px)';
                e.currentTarget.style.boxShadow = '0px 0px 0 var(--light-accent)';
                e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translate(0, 0)';
                e.currentTarget.style.boxShadow = '6px 6px 0 var(--light-accent)';
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              Schedule a Demo
            </button>
          </div>

          {/* Trust indicators */}
          <div className="mt-16 pt-8" style={{ borderTop: '2px solid rgba(255,255,255,0.2)' }}>
            <div className="flex flex-wrap justify-center items-center gap-8 text-sm" style={{ color: 'var(--light-accent)' }}>
              <div className="flex items-center gap-2">

                <span>SOC 2 Certified</span>
              </div>
              <div className="flex items-center gap-2">

                <span>No Credit Card Required</span>
              </div>
              <div className="flex items-center gap-2">

                <span>Setup in 5 Minutes</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}