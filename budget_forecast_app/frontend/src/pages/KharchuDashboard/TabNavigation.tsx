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

  // Custom styles to make react-select match Tailwind design
  const customSelectStyles = {
    control: (base, state) => ({
      ...base,
      backgroundColor: state.isFocused ? '#ffffff' : 'rgba(245, 241, 235, 0.5)',
      borderColor: state.isFocused ? '#1A1A1A' : '#E5E7EB',
      borderRadius: '0.75rem', // Tailwind rounded-xl
      padding: '2px',
      boxShadow: state.isFocused ? '0 0 0 2px #1A1A1A' : 'none',
      '&:hover': {
        borderColor: '#1A1A1A'
      }
    }),
    placeholder: (base) => ({
      ...base,
      color: '#9CA3AF', // Tailwind text-gray-400
      fontSize: '0.875rem' // Tailwind text-sm
    }),
    singleValue: (base) => ({
      ...base,
      color: '#1F2937', // Tailwind text-gray-800
      fontSize: '0.875rem'
    }),
    menu: (base) => ({
      ...base,
      zIndex: 9999 // Forces the dropdown to always render on top
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
              onClick={() => onToggleFilter(tab)}
              className={`whitespace-nowrap px-6 py-2.5 rounded-full text-sm font-medium transition-colors border ${
                isActive
                  ? "bg-[#1A1A1A] text-white border-[#1A1A1A]"
                  : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
              }`}
            >
              {tab}
            </button>
          );
        })}
      </div>

      {/* Dynamic AsyncSelect Fields Section */}
      {!activeFilters?.includes("Global View") && activeFilters?.length > 0 && (
        <div className="mt-4 p-5 bg-white rounded-[20px] border border-gray-200 shadow-sm flex flex-wrap gap-4 items-end animate-in fade-in slide-in-from-top-2">

          {activeFilters?.map(filter => (
            <div key={filter} className="flex flex-col flex-1 min-w-[250px] z-10">
              <label className="text-xs font-bold text-gray-500 mb-1.5 ml-1 uppercase tracking-wider">
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

          <button
            onClick={onApplyFilters}
            className="px-6 py-2.5 bg-[#1A1A1A] text-white rounded-xl text-sm font-medium hover:bg-black transition-all shadow-sm h-[42px] whitespace-nowrap mb-[2px]"
          >
            Apply Filters
          </button>

        </div>
      )}
    </div>
  );
}
