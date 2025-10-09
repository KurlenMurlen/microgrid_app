interface RangeSliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
  formatter: (value: number) => string;
  className?: string;
}

export function RangeSlider({
  label,
  value,
  onChange,
  min,
  max,
  step,
  formatter,
  className = '',
}: RangeSliderProps) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="text-text-dim text-sm">{label}</span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-20 h-1.5 bg-muted rounded-full appearance-none cursor-pointer accent-accent-2"
      />
      <span className="inline-flex items-center gap-2 px-2.5 py-1 border border-border rounded-full bg-muted text-text-dim text-xs min-w-[60px] justify-center">
        {formatter(value)}
      </span>
    </div>
  );
}
