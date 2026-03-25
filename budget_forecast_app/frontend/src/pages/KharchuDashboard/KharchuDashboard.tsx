import { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, LogOut, Download } from 'lucide-react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { LeftSidebar } from './LeftSidebar';
import { TopHeader } from './TopHeader';
import { RightSidebar } from './RightSidebar';
import { TabNavigation } from './TabNavigation';
import { MetricCards } from './MetricCards';
import { StatisticsChart } from './StatisticsChart';
import { getCsrfToken } from '../../utils/csrf';

const FILTER_FIELD_MAP = {
  "By Account": "account_name",
  "By Service": "service_name",
  "By Segment": "segment_name",
  "By BU Code": "bu_code"
};

// We need a reverse map to translate the URL 'forecastType' directly into a Tab Name
const FORECAST_TYPE_TO_TAB: Record<string, string> = {
  'account': 'By Account',
  'service': 'By Service',
  'bu_code': 'By BU Code',
  'segment': 'By Segment'
};

export function KharchuDashboard() {
  const [forecastData, setForecastData] = useState([]);
  const [historicalData, setHistoricalData] = useState([]);
  const [metricsData, setMetricsData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [forecastMessage, setForecastMessage] = useState("Applying filters...");
  const [datasetId, setDatasetId] = useState(null);

  // Extract the URL parameters first
  const [searchParams, setSearchParams] = useSearchParams();
  const taskId = searchParams.get('taskId');
  const initialGranularity = searchParams.get('granularity') || 'monthly';
  const initialForecastType = searchParams.get('forecastType');

  // --- THE FIX: Rebuild Tabs AND Values from the URL ---
  const getInitialFilters = () => {
     const filters: string[] = [];
     const values: Record<string, any> = {};

     if (initialForecastType && initialForecastType !== 'overall_aggregate') {
         // Unconditionally activate the correct tab based on the forecastType URL parameter!
         const activeTab = FORECAST_TYPE_TO_TAB[initialForecastType];
         if (activeTab) {
             filters.push(activeTab);
         }

         // 2. Check if they ALSO passed specific dropdown text values
         Object.entries(FILTER_FIELD_MAP).forEach(([tabName, paramKey]) => {
             const urlVal = searchParams.get(paramKey);
             if (urlVal) {
                 // Ensure the tab is active if a value exists, just to be safe
                 if (!filters.includes(tabName)) {
                     filters.push(tabName);
                 }
                 // Reconstruct the react-select object so the UI looks perfect!
                 values[tabName] = { label: urlVal, value: urlVal };
             }
         });
     }

     return {
         filters: filters.length > 0 ? filters : ['Global View'],
         values: values
     };
  };

  const [granularity, setGranularity] = useState(initialGranularity);

  // Initialize with the data parsed from the URL
  const initialData = getInitialFilters();
  const [activeFilters, setActiveFilters] = useState<string[]>(initialData.filters);
  const [filterValues, setFilterValues] = useState(initialData.values);

  const navigate = useNavigate();

  // Sign out logic
  const handleSignOut = () => {
    //  Clear the tokens from the browser
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');

    //  Redirect to the home page
    navigate('/');
  };

  useEffect(() => {
    const urlGranularity = searchParams.get('granularity');
    if (urlGranularity) {
      setGranularity(urlGranularity);
    }

    // Stop if no task ID is present
    if (!taskId) {
      console.log("No taskId found in the URL. Waiting...");
      setIsLoading(false);
      return;
    }

    const fetchDashboardData = async () => {
      setIsLoading(true);

      try {
        const apiUrl = `/api/dashboard-data/?task_id=${taskId}`;
        const response = await axios.get(apiUrl, { withCredentials: true });

        setForecastData(response.data.forecast || []);
        setHistoricalData(response.data.historical || []);
        setMetricsData(response.data.metrics || null);

        if (response.data.dataset_id) {
            setDatasetId(response.data.dataset_id);
        }
      } catch (error) {
        console.error("Failed to load dashboard data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [taskId, searchParams]); // Added searchParams so it listens for the URL update

  // --- Async Suggestions Logic ---
  const loadOptions = async (inputValue, filterName) => {
    console.log(`Fetching options for ${filterName} | Query: "${inputValue}" | Dataset ID:`, datasetId);
    // ONLY abort if datasetId is missing. We WANT to allow empty inputValues.
    if (!datasetId) {
      console.warn("Suggestions aborted: datasetId is null. Check your Django Celery task return dictionary.");
      return [];
    }
    if (!inputValue || !datasetId) return [];

    // Map UI Tab Names to your backend field names
    const fieldMap = {
      "By Account": "account",
      "By Service": "service",
      "By Segment": "segment",
      "By BU Code": "bu_code"
    };

    // Map for the backend parameter names
    const paramMap: Record<string, string> = {
      "By Account": "account_name",
      "By Service": "service_name",
      "By Segment": "segment_name",
      "By BU Code": "bu_code"
    };

    const field = fieldMap[filterName];

    // Initialize URL parameters using the standard API
    const queryParams = new URLSearchParams({
      q: inputValue || "",
      field: field,
      dataset_id: datasetId
    });

    // Loop through the currently active filters and append them to the URL
    // so the backend knows to restrict the suggestions
    Object.keys(filterValues).forEach(key => {
      // If a value is selected AND it's not the box we are currently typing in
      if (filterValues[key] && key !== filterName) {
         queryParams.append(paramMap[key], filterValues[key].value);
      }
    });

    try {
      const response = await fetch(`/get_suggestions/?${queryParams.toString()}`);

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();
      return (data.suggestions || []).map((item) => ({ value: item, label: item }));
    } catch (error) {
      console.error("Error fetching suggestions:", error);
      return [];
    }
  };

  // --- Filter Handlers ---
  const handleToggleFilter = (filterName) => {
    if (filterName === 'Global View') {
      setActiveFilters(['Global View']);
      setFilterValues({});
    } else {
      setActiveFilters((prev) => {
        const activeWithoutGlobal = prev.filter(f => f !== 'Global View');
        if (activeWithoutGlobal.includes(filterName)) {
          const updated = activeWithoutGlobal.filter(f => f !== filterName);
          return updated.length === 0 ? ['Global View'] : updated;
        } else {
          return [...activeWithoutGlobal, filterName];
        }
      });
    }
  };

  // Note: 'value' here will now be the full object { value: '...', label: '...' } from AsyncSelect
  const handleUpdateFilterValue = (filterName, selectedOption) => {
    setFilterValues(prev => ({ ...prev, [filterName]: selectedOption }));
  };

  const handleApplyFilters = async (isGlobalReset = false, overrideGranularity = null) => {
    if (!datasetId) {
      alert("Dataset ID is missing. Cannot run localized forecast.");
      return;
    }

    setIsLoading(true);
    setForecastMessage("Initializing new forecast model...");

    // 1. Map your UI tab names to the exact field names your Django backend expects
    const fieldMap: Record<string, string> = {
      "By Account": "account_name",
      "By Service": "service_name",
      "By Segment": "segment_name",
      "By BU Code": "bu_code"
    };

    // 2. Determine the primary "forecast_type" based on the most granular filter selected
    // Your trigger_forecast view relies on this to know which kwargs to extract.
    let forecastType = "overall_aggregate";
    if (activeFilters.includes("By Segment")) forecastType = "segment";
    if (activeFilters.includes("By BU Code")) forecastType = "bu_code";
    if (activeFilters.includes("By Account")) forecastType = "account";
    if (activeFilters.includes("By Service")) forecastType = "service";


    // 3. Prepare the FormData payload for your existing Django view
    const formData = new FormData();
    formData.append('dataset_id', datasetId);

    const currentGranularity = overrideGranularity || granularity;


    if (isGlobalReset == true) {
        formData.append('forecast_type', 'overall_aggregate');
        formData.append('granularity', currentGranularity);
    }
    else {
        formData.append('forecast_type', forecastType);
        formData.append('granularity', currentGranularity);
        // Append the selected filter values
        Object.keys(filterValues).forEach(key => {
          if (filterValues[key]) {
             const backendKey = fieldMap[key];
             formData.append(backendKey, filterValues[key].value);
          }
        });
    }

    try {
      // 4. Hit your existing trigger_forecast endpoint
      const response = await fetch('/trigger-forecast/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
          headers: {
              'X-CSRFToken' : getCsrfToken(),
              }
      });

      const data = await response.json();

      if (data.task_id) {
        // 5. Start polling the new task
        pollTaskStatus(data.task_id);
      } else {
        alert(data.message || "Failed to trigger filtered forecast.");
        setIsLoading(false);
      }
    } catch (error) {
      console.error("Error applying filters:", error);
      setIsLoading(false);
    }
  };

  // --- DOWNLOAD LOGIC ---
  const handleDownloadCSV = () => {
    if (!forecastData || forecastData.length === 0) {
      alert("No forecast data available to download.");
      return;
    }

    // Set up Base CSV headers
    const headers = ['Date', 'Predicted Spend', 'Lower Bound', 'Upper Bound'];

    // Identify which filters are actually active (ignore Global View)
    const activeFilterKeys = activeFilters.filter(f => f !== 'Global View');

    // Dynamically add the filter names to the headers
    activeFilterKeys.forEach(filter => {
      headers.push(filter.replace('By ', '')); // Converts "By Account" to "Account"
    });

    const csvRows = [headers.join(',')];

    // Extract the exact values the user selected for those filters.
    // We wrap them in quotes `""` so that if an account name has a comma in it
    // (e.g., "Acme, Inc."), it doesn't accidentally break the CSV layout!
    const filterRowValues = activeFilterKeys.map(filter => {
       const val = filterValues[filter]?.value;
       return val ? `"${val}"` : '"All"'; // Default to "All" if they opened the tab but left it blank
    });

    // Loop through data and format rows
    forecastData.forEach(row => {
      // Safely format the date (extract YYYY-MM-DD from the timestamp)
      const date = row.ds ? new Date(row.ds).toISOString().split('T')[0] : '';
      // Round financial numbers to 2 decimal places
      const yhat = row.yhat ? row.yhat.toFixed(2) : '0.00';
      const lower = row.yhat_lower ? row.yhat_lower.toFixed(2) : '0.00';
      const upper = row.yhat_upper ? row.yhat_upper.toFixed(2) : '0.00';

      // Build the base row, then append the dynamic filter values
      const baseRow = [date, yhat, lower, upper];
      const fullRow = [...baseRow, ...filterRowValues];

      csvRows.push(fullRow.join(','));
    });

    // Create a Blob and trigger download
    const csvString = csvRows.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);

    // Generate a short 8-character UUID
    const uniqueId = crypto.randomUUID().split('-')[0];

    const link = document.createElement('a');
    link.href = url;
    // Inject the date and the unique UUID into the filename
    link.download = `forecast_results_${new Date().toISOString().split('T')[0]}_${uniqueId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // --- REUSED POLLING LOGIC FROM UPLOAD PAGE ---
  const pollTaskStatus = (newTaskId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/status/${newTaskId}/`);

        // 1. Catch HTTP errors before trying to parse JSON
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // 2. Define clear status states
        const isSuccess = data.status === 'SUCCESS' || data.state === 'SUCCESS';
        const isFailure = data.status === 'FAILURE' || data.state === 'FAILURE' || data.status === 'error';

        // 3. Handle Progress
        if (data.status === 'PROGRESS') {
          setForecastMessage(data.message || "Running ML models...");
          return; // Early return to keep logic flat
        }

        // 4. Handle Success
        if (isSuccess) {
          clearInterval(pollInterval);
          setForecastMessage("Complete!");

          // --- Determine current active tab and preserve it in URL ---
          let activeType = "overall_aggregate";
          if (activeFilters.includes("By Segment")) activeType = "segment";
          if (activeFilters.includes("By BU Code")) activeType = "bu_code";
          if (activeFilters.includes("By Account")) activeType = "account";
          if (activeFilters.includes("By Service")) activeType = "service";


          // Updating search params changes the URL and triggers the fetch useEffect
          setSearchParams({
              taskId: newTaskId,
              granularity,
              forecastType: activeType});
          return;
        }

        // 5. Handle Failure & Smart Error Interception
        if (isFailure) {
          clearInterval(pollInterval);
          setIsLoading(false);

          const errorMessage = (data.message || "").toLowerCase();

          // Intercept missing date column errors for daily forecasts
          if (errorMessage.includes("'date'") || errorMessage.includes("daily")) {
            alert("Daily data unavailable in the uploaded file. Please upload a new file with daily data.");
            setGranularity('monthly'); // Reset UI toggle to prevent a blocked state
          } else {
            alert(`The filtered forecast failed: ${data.message || "Unknown error"}`);
          }
          return;
        }

      } catch (err) {
        // 6. Handle Network/Parsing Exceptions
        console.error("Polling error:", err);
        clearInterval(pollInterval);
        setIsLoading(false);
        alert("A network error occurred while checking the forecast status.");
      }
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-[#E5E0D8] p-4 flex justify-center items-center">
      <div className="bg-[#F5F1EB] rounded-[40px] shadow-2xl w-full max-w-[1600px] h-[95vh] flex overflow-hidden border border-white/40">

        <LeftSidebar />

        <div className="flex-1 flex flex-col py-8 px-2 overflow-hidden">
          <TopHeader />
          <TabNavigation
            activeFilters={activeFilters}
            onToggleFilter={handleToggleFilter}
            filterValues={filterValues}
            onUpdateFilterValue={handleUpdateFilterValue}
            onApplyFilters={handleApplyFilters}
            loadOptions={loadOptions}
          />

          <div className="flex-1 overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-gray-300">
            <MetricCards metrics={metricsData} isLoading={isLoading} />

            {isLoading ? (
              <div className="h-[400px] flex flex-col items-center justify-center bg-white rounded-[24px] shadow-sm border border-gray-100 mt-6">
                <Loader2 className="animate-spin text-gray-400 mb-4" size={32} />
                <p className="text-gray-500 font-medium">Loading your forecast...</p>
              </div>
            ) : (
              <div className="mt-6">
                {/* Header Row with Toggle and Download Button */}
                {forecastData.length > 0 && (
                  <div className="flex justify-between items-end mb-4 px-2">

                    {/* Left Side: Title & Segmented Toggle */}
                    <div className="flex items-center gap-6">
                      <h3 className="text-lg font-bold text-[#1A1A1A]">Forecast Overview</h3>

                      <div className="flex bg-[#E5E0D8] rounded-xl p-1 shadow-inner border border-black/5">
                        <button
                          onClick={() => {
                              setGranularity('monthly');
                              handleApplyFilters(activeFilters.includes('Global View'), 'monthly');
                              }
                          }

                          className={`px-4 py-1.5 text-sm font-semibold rounded-lg transition-all duration-200 ${
                            granularity === 'monthly'
                              ? 'bg-white text-black shadow-sm'
                              : 'text-gray-500 hover:text-gray-800'
                          }`}
                        >
                          Monthly
                        </button>
                        <button
                          onClick={() => {
                              setGranularity('daily');
                              handleApplyFilters(activeFilters.includes('Global View'), 'daily');
                              }
                          }
                          className={`px-4 py-1.5 text-sm font-semibold rounded-lg transition-all duration-200 ${
                            granularity === 'daily'
                              ? 'bg-white text-black shadow-sm'
                              : 'text-gray-500 hover:text-gray-800'
                          }`}
                        >
                          Daily
                        </button>
                      </div>
                    </div>

                    {/* Right Side: Export Button */}
                    <button
                      onClick={handleDownloadCSV}
                      className="flex items-center gap-2 px-5 py-2.5 bg-[#D4FF00] text-black rounded-xl text-sm font-semibold hover:bg-[#bce600] transition-colors shadow-sm border border-transparent hover:border-black/10"
                    >
                      <Download size={16} />
                      Export to CSV
                    </button>
                  </div>
                )}

                {/* --- THE CHART --- */}
                <StatisticsChart
                  forecast={forecastData}
                  historical={historicalData}
                  granularity={granularity}
                />
                {/* --- ACTIVE FILTERS DISPLAY --- */}
                <div className="mt-4 flex flex-wrap items-center gap-2 px-2 animate-in fade-in duration-300">
                  <span className="text-sm font-semibold text-gray-400 mr-2">Currently Viewing:</span>

                  {activeFilters.includes('Global View') ? (
                    <span className="px-3 py-1 bg-gray-100 text-gray-500 text-xs font-bold rounded-full border border-gray-200">
                      Global Aggregate
                    </span>
                  ) : (
                    activeFilters.map(filter => {
                      // Grab the selected dropdown object
                      const valueObj = filterValues[filter];
                      // If they opened the tab but haven't picked a specific item yet, default to "All"
                      const displayValue = valueObj ? valueObj.label : 'All';
                      // Strip out the "By " text (e.g., "By Account" -> "Account")
                      const filterLabel = filter.replace('By ', '');

                      return (
                        <div key={filter} className="flex items-center bg-[#E5E0D8]/60 border border-[#E5E0D8] rounded-full px-3 py-1.5 shadow-sm">
                          <span className="text-xs font-bold text-gray-500 mr-1.5 uppercase tracking-wider">{filterLabel}:</span>
                          <span className="text-xs font-bold text-[#1A1A1A]">{displayValue}</span>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="py-8 pr-8 pl-4 border-l border-gray-200/50 bg-[#F5F1EB]">
          <RightSidebar />
        </div>
      </div>
    </div>
  );
}
