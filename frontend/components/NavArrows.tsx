interface NavArrowsProps {
  currentView: 'home' | 'technical';
  onNavigateToHome: () => void;
  onNavigateToTechnical: () => void;
}

export function NavArrows({ currentView, onNavigateToHome, onNavigateToTechnical }: NavArrowsProps) {
  return (
    <>
      {currentView === 'technical' && (
        <button
          onClick={onNavigateToHome}
          className="nav-arrow left fixed left-4 top-1/2 -translate-y-1/2 z-50 w-12 h-12 flex items-center justify-center bg-surface/90 backdrop-blur-sm border border-border rounded-full shadow-card-md hover:shadow-card-lg hover:bg-accent-2/10 hover:border-accent-2 transition-smooth"
          aria-label="Previous view"
        >
          <svg
            width="24"
            height="24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>
      )}
      {currentView === 'home' && (
        <button
          onClick={onNavigateToTechnical}
          className="nav-arrow right fixed right-4 top-1/2 -translate-y-1/2 z-50 w-12 h-12 flex items-center justify-center bg-surface/90 backdrop-blur-sm border border-border rounded-full shadow-card-md hover:shadow-card-lg hover:bg-accent-2/10 hover:border-accent-2 transition-smooth"
          aria-label="Next view"
        >
          <svg
            width="24"
            height="24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
        </button>
      )}
    </>
  );
}
