export function TabNavigation() {
  const tabs = [
    "Global View",
    "By Account",
    "By Service",
    "By Segment",
    "By BU Code"
  ];

  return (
    <div className="flex items-center space-x-2 mb-8 overflow-x-auto pb-2 scrollbar-none">
      {tabs.map((tab, idx) => (
        <button
          key={idx}
          className={`whitespace-nowrap px-6 py-2.5 rounded-full text-sm font-medium transition-colors ${
            idx === 0
              ? "bg-[#1A1A1A] text-white"
              : "bg-white text-gray-600 hover:bg-gray-100"
          }`}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}
