interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'ml' | 'live';
  className?: string;
}

export function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  const variants = {
    default: 'bg-muted border-border text-text-dim',
    ml: 'bg-gradient-to-b from-[color-mix(in_oklab,var(--accent-2)_18%,var(--muted))] to-muted border-[color-mix(in_oklab,var(--accent-2)_35%,var(--border))] text-[color-mix(in_oklab,var(--text)_85%,var(--text-dim))] font-semibold',
    live: 'bg-gradient-to-br from-accent-3 to-accent-2 text-white border-transparent font-semibold shadow-md',
  };

  return (
    <span
      className={`inline-flex items-center gap-2 px-2.5 py-1.5 border rounded-full text-sm ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
