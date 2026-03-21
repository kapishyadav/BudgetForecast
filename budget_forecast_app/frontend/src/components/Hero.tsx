import { TrendingUp, BarChart3 } from 'lucide-react';

export function Hero() {
  return (
    <div className="relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-32">
        <div className="text-center relative z-10">
          <div className="flex justify-center mb-8">
            <div
              className="inline-flex items-center gap-3 px-8 py-4 relative group"
              style={{
                backgroundColor: 'var(--accent)',
                color: 'white',
                borderRadius: 'var(--radius)',
                boxShadow: '6px 6px 0 var(--primary)',
                transition: 'var(--transition)'
              }}
            >
              <BarChart3 className="w-7 h-7" />
              <span>Kharchu</span>
              <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full flex items-center justify-center animate-pulse"
                style={{
                  backgroundColor: 'var(--primary)',
                  boxShadow: '2px 2px 0 var(--accent)'
                }}>
                <TrendingUp className="w-3 h-3 text-white" />
              </div>
            </div>
          </div>

          <h1 className="max-w-4xl mx-auto mb-8 leading-tight" style={{
            color: 'var(--primary)',
            fontSize: 'clamp(2rem, 5vw, 3.5rem)'
          }}>
            Keep Your {' '}
            <span className="relative inline-block">
              <span className="relative z-10">Cloud Kharchu</span>
              <span
                className="absolute bottom-2 left-0 w-full h-3 -z-0"
                style={{ backgroundColor: 'var(--light-accent)', opacity: 0.5 }}
              ></span>
            </span>
            {' '}Under Control
          </h1>

          <p className="max-w-2xl mx-auto mb-12 text-lg" style={{ color: 'var(--primary)', opacity: 0.8 }}>
            Stop guessing your next invoice
          </p>

          <div className="flex flex-wrap justify-center gap-6">
            <button
              className="px-10 py-4 flex items-center gap-3 group"
              style={{
                backgroundColor: 'var(--accent)',
                color: 'white',
                borderRadius: 'var(--radius)',
                boxShadow: 'var(--shadow)',
                transition: 'var(--transition)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translate(8px, 8px)';
                e.currentTarget.style.boxShadow = '0px 0px 0 var(--accent)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translate(0, 0)';
                e.currentTarget.style.boxShadow = 'var(--shadow)';
              }}
              onClick={() => window.location.href = '/'}
            >
              Get Started
              <TrendingUp className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              className="px-10 py-4 group"
              style={{
                backgroundColor: 'transparent',
                color: 'var(--primary)',
                borderRadius: 'var(--radius)',
                border: '3px solid var(--primary)',
                boxShadow: '6px 6px 0 var(--light-accent)',
                transition: 'var(--transition)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translate(6px, 6px)';
                e.currentTarget.style.boxShadow = '0px 0px 0 var(--light-accent)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translate(0, 0)';
                e.currentTarget.style.boxShadow = '6px 6px 0 var(--light-accent)';
              }}
            >
              View Documentation
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20 max-w-3xl mx-auto">
            {[
              { value: '99.9%', label: 'Accuracy Rate' },
              { value: '50K+', label: 'Forecasts Generated' },
              { value: '$2M+', label: 'Saved in Costs' }
            ].map((stat, index) => (
              <div
                key={index}
                className="p-6 text-center"
                style={{
                  backgroundColor: 'white',
                  borderRadius: 'var(--radius)',
                  border: '2px solid var(--accent)',
                  boxShadow: '4px 4px 0 var(--accent)'
                }}
              >
                <div style={{
                  color: 'var(--accent)',
                  fontSize: '2rem',
                  marginBottom: '0.5rem'
                }}>{stat.value}</div>
                <div style={{ color: 'var(--primary)', opacity: 0.7 }}>{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Background decoration */}
      <div className="absolute top-0 left-0 w-full h-full -z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-32 h-32 rounded-full filter blur-2xl opacity-20" style={{ backgroundColor: 'var(--accent)' }}></div>
        <div className="absolute top-40 right-10 w-64 h-64 rounded-full filter blur-3xl opacity-15" style={{ backgroundColor: 'var(--light-accent)' }}></div>
        <div className="absolute bottom-20 left-1/3 w-48 h-48 rounded-full filter blur-3xl opacity-15" style={{ backgroundColor: 'var(--accent)' }}></div>

        {/* Coffee beans decoration */}
        <div className="absolute top-1/4 right-1/4 opacity-5 text-9xl rotate-12">☕</div>
        <div className="absolute bottom-1/3 left-1/4 opacity-5 text-7xl -rotate-12">☕</div>
      </div>
    </div>
  );
}