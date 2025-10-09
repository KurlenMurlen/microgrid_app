interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <article
      className={`bg-surface border border-border rounded-card-sm p-gap shadow-card-sm transition-smooth hover:shadow-card-md ${className}`}
    >
      {children}
    </article>
  );
}
