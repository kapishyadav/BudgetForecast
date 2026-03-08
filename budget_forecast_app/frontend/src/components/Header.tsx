import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

export function Header() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 backdrop-blur-sm" style={{ 
      backgroundColor: theme === 'light' ? 'rgba(247, 243, 238, 0.95)' : 'rgba(42, 33, 32, 0.95)',
      borderBottom: '3px solid var(--accent)',
      transition: 'var(--transition)'
    }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-lg flex items-center justify-center relative overflow-hidden" 
              style={{ 
                backgroundColor: 'var(--accent)',
                boxShadow: '3px 3px 0 var(--primary)'
              }}
            >
              <div className="absolute inset-0 opacity-20" style={{
                background: 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,0.1) 10px, rgba(255,255,255,0.1) 20px)'
              }}></div>
              <span className="text-white relative z-10">☕</span>
            </div>
            <div>
              <div style={{ color: 'var(--primary)' }}>AWS Budget Forecast</div>
              <div style={{ color: 'var(--accent)', fontSize: '12px', opacity: 0.8 }}>Powered by ML</div>
            </div>
          </div>
          
          <button
            onClick={toggleTheme}
            className="p-3 rounded-lg relative group"
            style={{ 
              backgroundColor: 'var(--light-accent)',
              boxShadow: '3px 3px 0 var(--accent)',
              transition: 'var(--transition)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translate(3px, 3px)';
              e.currentTarget.style.boxShadow = '0px 0px 0 var(--accent)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translate(0, 0)';
              e.currentTarget.style.boxShadow = '3px 3px 0 var(--accent)';
            }}
            aria-label="Toggle theme"
          >
            {theme === 'light' ? (
              <Moon className="w-5 h-5" style={{ color: 'var(--primary)' }} />
            ) : (
              <Sun className="w-5 h-5" style={{ color: 'var(--primary)' }} />
            )}
          </button>
        </div>
      </div>
    </header>
  );
}