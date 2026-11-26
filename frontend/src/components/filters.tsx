interface FilterOption {
  label: string;
  value: string;
}

interface FiltersProps {
  options: FilterOption[];
  selectedType: string;
  setSelectedType: (value: string) => void;
}

export default function Filters({
  options,
  selectedType,
  setSelectedType,
}: FiltersProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => setSelectedType(option.value)}
          className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
            selectedType === option.value
              ? "bg-secondary text-foreground"
              : "text-muted-foreground hover:bg-accent hover:text-foreground"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
