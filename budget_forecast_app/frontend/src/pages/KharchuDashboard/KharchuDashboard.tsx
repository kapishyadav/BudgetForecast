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

export function KharchuDashboard() {
  const [forecastData, setForecastData] = useState([]);
  const [historicalData, setHistoricalData] = useState([]);
  const [metricsData, setMetricsData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // --- Filter & Suggestion State ---
  const [activeFilters, setActiveFilters] = useState(['Global View']);
  const [filterValues, setFilterValues] = useState({});
  const [datasetId, setDatasetId] = useState(null); // Required for suggestions

  // Extract the Celery task ID from the URL (e.g., /kharchu?taskId=123-abc)
  const [searchParams, setSearchParams] = useSearchParams();
  const taskId = searchParams.get('taskId');

  const [forecastMessage, setForecastMessage] = useState("Applying filters...");

  // Initialize navigate for the sign-out redirect
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
    // If someone visits the dashboard directly without a task ID, stop loading
    if (!taskId) {
      console.log("No taskId found in the URL. Waiting...");
      setIsLoading(false);
      return;
    }

    const fetchDashboardData = async () => {
      try {
        // Build the URL strictly using string concatenation
        const apiUrl = "/api/dashboard-data/?task_id=" + taskId;

        // DEBUGGING: This will prove what React is actually sending
        console.log("Requesting data from:", apiUrl);

        // Request the data using the specific task ID
        const response = await axios.get(apiUrl, {
          withCredentials: true
        });
        setForecastData(response.data.forecast);
        setHistoricalData(response.data.historical);
        setMetricsData(response.data.metrics);
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
  }, [taskId]); // Add taskId as a dependency

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

  const handleApplyFilters = async (isGlobalReset = false) => {
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
    if (activeFilters.includes("By Service")) forecastType = "service";
    if (activeFilters.includes("By Account")) forecastType = "account";

    // 3. Prepare the FormData payload for your existing Django view
    const formData = new FormData();
    formData.append('dataset_id', datasetId);
    if (isGlobalReset == true) {
        formData.append('forecast_type', 'overall_aggregate');
        formData.append('granularity', 'monthly');
    }
    else {
        formData.append('forecast_type', forecastType);
        formData.append('granularity', 'monthly');
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
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/status/${newTaskId}/`);
        const data = await response.json();

        if (data.status === 'PROGRESS') {
          setForecastMessage(data.message || "Running ML models...");
        }
        else if (data.status === 'SUCCESS' || data.state === 'SUCCESS') {
          clearInterval(interval);
          setForecastMessage("Complete!");

          // Updating the search params changes the URL (e.g., ?taskId=NEW_ID)
          // This automatically triggers your existing useEffect to fetch the new data!
          setSearchParams({ taskId: newTaskId });
        }
        else if (data.status === 'FAILURE' || data.state === 'FAILURE' || data.status === 'error') {
          clearInterval(interval);
          setIsLoading(false);
          alert("The filtered forecast failed: " + (data.message || "Unknown error"));
        }
      } catch (err) {
        console.error("Polling error:", err);
        clearInterval(interval);
        setIsLoading(false);
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
                {/* Header Row with Download Button */}
                {forecastData.length > 0 && (
                  <div className="flex justify-between items-end mb-4 px-2">
                    <h3 className="text-lg font-bold text-[#1A1A1A]">Forecast Overview</h3>
                    <button
                      onClick={handleDownloadCSV}
                      className="flex items-center gap-2 px-5 py-2.5 bg-[#EAFF52] text-black rounded-xl text-sm font-semibold hover:bg-[#bce600] transition-colors shadow-sm border border-transparent hover:border-black/10"
                    >
                      <Download size={16} />
                      Export to CSV
                    </button>
                  </div>
                )}

                {/* The Chart */}
                <StatisticsChart forecast={forecastData} historical={historicalData} />
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
