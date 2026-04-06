import AsyncSelect from 'react-select/async';

export function TabNavigation({
  activeFilters = ['Global View'],
  onToggleFilter,
  filterValues = {},
  onUpdateFilterValue,
  onApplyFilters,
  loadOptions
}) {
  const tabs = [
    "Global View",
    "By Account",
    "By Service",
    "By Segment",
    "By BU Code"
  ];

  // Custom styles dynamically reading your CSS variables!
  const customSelectStyles = {
    control: (base, state) => ({
      ...base,
      backgroundColor: 'var(--background)',
      borderColor: state.isFocused ? 'var(--ring)' : 'var(--border)',
      borderRadius: '0.75rem',
      padding: '2px',
      boxShadow: state.isFocused ? '0 0 0 1px var(--ring)' : 'none',
      transition: 'all 0.3s ease',
      '&:hover': {
        borderColor: 'var(--ring)'
      }
    }),
    placeholder: (base) => ({
      ...base,
      color: 'var(--muted-foreground)',
      fontSize: '0.875rem'
    }),
    singleValue: (base) => ({
      ...base,
      color: 'var(--foreground)',
      fontSize: '0.875rem'
    }),
    input: (base) => ({
      ...base,
      color: 'var(--foreground)' // Ensures typing text is visible in dark mode
    }),
    menu: (base) => ({
      ...base,
      zIndex: 9999,
      backgroundColor: 'var(--card)',
      border: '1px solid var(--border)',
      borderRadius: '0.75rem',
      boxShadow: 'var(--shadow)',
      overflow: 'hidden'
    }),
    option: (base, state) => ({
      ...base,
      backgroundColor: state.isFocused ? 'var(--muted)' : 'transparent',
      color: state.isSelected ? 'var(--foreground)' : 'var(--muted-foreground)',
      cursor: 'pointer',
      transition: 'background-color 0.2s ease',
      '&:active': {
        backgroundColor: 'var(--muted)'
      }
    })
  };

  return (
    <div className="mb-6">
      {/* Filter Buttons */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-2 scrollbar-none">
        {tabs.map((tab, idx) => {
          const isActive = activeFilters?.includes(tab);

          return (
            <button
              key={idx}
              onClick={() => {
                  onToggleFilter(tab);
                  if (tab == "Global View") {
                      onApplyFilters(true)
                  }
              }}
              className={`whitespace-nowrap px-6 py-2.5 rounded-full text-sm font-medium transition-all duration-300 border ${
                isActive
                  // Swapped to primary theme variables for active state
                  ? "bg-primary text-primary-foreground border-primary"
                  // Swapped to card/muted variables for inactive state
                  : "bg-card text-muted-foreground border-border hover:bg-muted hover:text-foreground"
              }`}
            >
              {tab}
            </button>
          );
        })}
      </div>

      {/* Dynamic AsyncSelect Fields Section */}
      {!activeFilters?.includes("Global View") && activeFilters?.length > 0 && (
        <div className="mt-4 p-5 bg-card rounded-[20px] border border-border shadow-sm flex flex-wrap gap-4 items-end animate-in fade-in slide-in-from-top-2 transition-colors duration-300">

          {activeFilters?.map(filter => (
            <div key={filter} className="flex flex-col flex-1 min-w-[250px] z-10">
              {/* Swapped text-gray-500 to text-muted-foreground */}
              <label className="text-xs font-bold text-muted-foreground mb-1.5 ml-1 uppercase tracking-wider transition-colors duration-300">
                {filter.replace('By ', '')}
              </label>

              <AsyncSelect
                cacheOptions
                defaultOptions
                loadOptions={(inputValue) => loadOptions(inputValue, filter)}
                onChange={(selectedOption) => onUpdateFilterValue(filter, selectedOption)}
                value={filterValues[filter] || null}
                placeholder={`Search ${filter.replace('By ', '')}...`}
                styles={customSelectStyles}
                isClearable
              />
            </div>
          ))}

          {/* Apply Filters Button */}
          <button
            type="button"
            onClick={() => onApplyFilters(false)}
            className="px-6 py-2.5 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:opacity-90 transition-opacity shadow-sm h-[42px] whitespace-nowrap mb-[2px] cursor-pointer"
          >
            Apply Filters
          </button>

        </div>
      )}
    </div>
  );
}