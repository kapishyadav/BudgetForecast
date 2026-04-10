import { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, LogOut, Download, Sparkles } from 'lucide-react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { LeftSidebar } from './LeftSidebar';
import { TopHeader } from './TopHeader';
import { RightSidebar } from './RightSidebar';
import { TabNavigation } from './TabNavigation';
import { MetricCards } from './MetricCards';
import { StatisticsChart } from './StatisticsChart';
import { getCsrfToken } from '../../utils/csrf';

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

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

  // ---> NEW STATE FOR AI INSIGHT <---
  const [aiInsight, setAiInsight] = useState<string | null>(null);

  // Extract the URL parameters first
  const [searchParams, setSearchParams] = useSearchParams();
  const taskId = searchParams.get('taskId');
  const initialGranularity = searchParams.get('granularity') || 'monthly';
  const initialForecastType = searchParams.get('forecastType');

  // --- Rebuild Tabs AND Values from the URL ---
  const getInitialFilters = () => {
     const filters: string[] = [];
     const values: Record<string, any> = {};

     if (initialForecastType && initialForecastType !== 'overall_aggregate') {
         const activeTab = FORECAST_TYPE_TO_TAB[initialForecastType];
         if (activeTab) {
             filters.push(activeTab);
         }

         Object.entries(FILTER_FIELD_MAP).forEach(([tabName, paramKey]) => {
             const urlVal = searchParams.get(paramKey);
             if (urlVal) {
                 if (!filters.includes(tabName)) {
                     filters.push(tabName);
                 }
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

  const initialData = getInitialFilters();
  const [activeFilters, setActiveFilters] = useState<string[]>(initialData.filters);
  const [filterValues, setFilterValues] = useState(initialData.values);

  const navigate = useNavigate();

  const handleSignOut = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    navigate('/');
  };

  useEffect(() => {
    const urlGranularity = searchParams.get('granularity');
    if (urlGranularity) setGranularity(urlGranularity);

    if (!taskId) {
      setIsLoading(false);
      return;
    }

    const fetchDashboardData = async () => {
      setIsLoading(true);
      try {
        const apiUrl = `/api/dashboard-data/?task_id=${taskId}`;
        const response = await axios.get(apiUrl, { withCredentials: true });
        const payload = response.data.data ? response.data.data : response.data;

        // --- THE DATA ADAPTER (NORMALIZER) ---

        // 1. Extract and Parse Forecast
        const rawForecast = typeof payload.forecast_json === 'string'
            ? JSON.parse(payload.forecast_json)
            : payload.forecast || [];

        // 2. Extract and Parse Historical
        const rawHistorical = typeof payload.historical_json === 'string'
            ? JSON.parse(payload.historical_json)
            : payload.historical || [];

        // 3. Normalize Keys (date -> ds, forecast -> yhat)
        const normalizedForecast = rawForecast.map((item: any) => ({
          ds: item.ds || item.date || item.Month,
          yhat: item.yhat !== undefined ? item.yhat : item.forecast,
          yhat_lower: item.yhat_lower !== undefined ? item.yhat_lower : (item.forecast ? item.forecast * 0.9 : 0),
          yhat_upper: item.yhat_upper !== undefined ? item.yhat_upper : (item.forecast ? item.forecast * 1.1 : 0),
        }));

        const normalizedHistorical = rawHistorical.map((item: any) => ({
          ds: item.ds || item.date || item.Month,
          y: item.y !== undefined ? item.y : (item.spend || item.Cost || 0),
        }));

        setForecastData(normalizedForecast);
        setHistoricalData(normalizedHistorical);

        // 4. Map Metrics Safely
        if (payload.metrics) {
            setMetricsData({
                total_forecasted_spend: payload.metrics.total_forecasted_spend || normalizedForecast.reduce((acc: number, curr: any) => acc + (curr.yhat || 0), 0),
                average_monthly_spend: payload.metrics.average_monthly_spend || 0,
                rmse: payload.metrics.rmse || 0,
                mape: payload.metrics.mape || 0,
                forecast_period: payload.metrics.forecast_period || "Next 12 Months"
            });
        }

        // ---> GRAB AI INSIGHT FROM BACKEND <---
        setAiInsight(payload.ai_insight || null);

        if (payload.dataset_id) setDatasetId(payload.dataset_id);
      } catch (error) {
        console.error("Failed to load dashboard data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [taskId, searchParams]);

  const loadOptions = async (inputValue, filterName) => {
    if (!datasetId) {
      return [];
    }
    if (!inputValue || !datasetId) return [];

    const fieldMap = {
      "By Account": "account",
      "By Service": "service",
      "By Segment": "segment",
      "By BU Code": "bu_code"
    };

    const paramMap: Record<string, string> = {
      "By Account": "account_name",
      "By Service": "service_name",
      "By Segment": "segment_name",
      "By BU Code": "bu_code"
    };

    const field = fieldMap[filterName];

    const queryParams = new URLSearchParams({
      q: inputValue || "",
      field: field,
      dataset_id: datasetId
    });

    Object.keys(filterValues).forEach(key => {
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

  const handleUpdateFilterValue = (filterName, selectedOption) => {
    setFilterValues(prev => ({ ...prev, [filterName]: selectedOption }));
  };

  const handleApplyFilters = async (eOrIsGlobalReset, overrideGranularity = null) => {
    // 1. Catch the event and stop the browser from doing a native GET request
    if (eOrIsGlobalReset && typeof eOrIsGlobalReset.preventDefault === 'function') {
      eOrIsGlobalReset.preventDefault();
    }

    // 2. Safely determine if this was a global reset or an event
    const isReset = eOrIsGlobalReset === true;

    if (!datasetId) {
      alert("Dataset ID is missing. Cannot run localized forecast.");
      return;
    }

    setIsLoading(true);
    setForecastMessage("Initializing new forecast model...");

    const fieldMap = {
      "By Account": "account_name",
      "By Service": "service_name",
      "By Segment": "segment_name",
      "By BU Code": "bu_code"
    };

    let forecastType = "overall_aggregate";
    if (activeFilters.includes("By Segment")) forecastType = "segment";
    if (activeFilters.includes("By BU Code")) forecastType = "bu_code";
    if (activeFilters.includes("By Account")) forecastType = "account";
    if (activeFilters.includes("By Service")) forecastType = "service";

    const formData = new FormData();
    formData.append('dataset_id', datasetId);

    const currentGranularity = overrideGranularity || granularity;

    if (isReset === true) {
        formData.append('forecast_type', 'overall_aggregate');
        formData.append('granularity', currentGranularity);
    } else {
        formData.append('forecast_type', forecastType);
        formData.append('granularity', currentGranularity);
        Object.keys(filterValues).forEach(key => {
          if (filterValues[key]) {
             const backendKey = fieldMap[key];
             formData.append(backendKey, filterValues[key].value);
          }
        });
    }

    try {
      const response = await fetch('/trigger-forecast/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        }
      });

      if (!response.ok) {
        throw new Error("No historical data found for this combination of filters.");
      }

      const responseData = await response.json();

      if (responseData.status?.toUpperCase() === "SUCCESS" && (responseData.data?.task_id || responseData.task_id)) {
        pollTaskStatus(responseData.data?.task_id || responseData.task_id);
      } else {
        console.error("Backend error:", responseData.errors || responseData.message);
        if (responseData.errors) {
           alert("Validation Error: " + JSON.stringify(responseData.errors));
        } else {
           alert(responseData.message || "Failed to trigger filtered forecast.");
        }
        setIsLoading(false);
      }
    } catch (error) {
      console.error("Error applying filters:", error);
      alert(`Forecast Failed: ${error.message}`);
      setIsLoading(false);
    }
  };

  const handleDownloadCSV = () => {
    if (!forecastData || forecastData.length === 0) {
      alert("No forecast data available to download.");
      return;
    }

    const headers = ['Date', 'Predicted Spend', 'Lower Bound', 'Upper Bound'];
    const activeFilterKeys = activeFilters.filter(f => f !== 'Global View');

    activeFilterKeys.forEach(filter => {
      headers.push(filter.replace('By ', ''));
    });

    const csvRows = [headers.join(',')];

    const filterRowValues = activeFilterKeys.map(filter => {
       const val = filterValues[filter]?.value;
       return val ? `"${val}"` : '"All"';
    });

    forecastData.forEach(row => {
      const date = row.ds ? new Date(row.ds).toISOString().split('T')[0] : '';
      const yhat = row.yhat ? row.yhat.toFixed(2) : '0.00';
      const lower = row.yhat_lower ? row.yhat_lower.toFixed(2) : '0.00';
      const upper = row.yhat_upper ? row.yhat_upper.toFixed(2) : '0.00';

      const baseRow = [date, yhat, lower, upper];
      const fullRow = [...baseRow, ...filterRowValues];

      csvRows.push(fullRow.join(','));
    });

    const csvString = csvRows.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);

    const uniqueId = crypto.randomUUID().split('-')[0];

    const link = document.createElement('a');
    link.href = url;
    link.download = `forecast_results_${new Date().toISOString().split('T')[0]}_${uniqueId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const pollTaskStatus = (newTaskId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/status/${newTaskId}/`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const payload = data.data ? data.data : data; // Safe unwrapping

        const isSuccess = payload.status === 'SUCCESS' || payload.state === 'SUCCESS';
        const isFailure = payload.status === 'FAILURE' || payload.state === 'FAILURE' || payload.status === 'error';

        if (payload.status === 'PROGRESS') {
          setForecastMessage(payload.message || "Running ML models...");
          return;
        }

        if (isSuccess) {
          clearInterval(pollInterval);
          setForecastMessage("Complete!");

          let activeType = "overall_aggregate";
          if (activeFilters.includes("By Segment")) activeType = "segment";
          if (activeFilters.includes("By BU Code")) activeType = "bu_code";
          if (activeFilters.includes("By Account")) activeType = "account";
          if (activeFilters.includes("By Service")) activeType = "service";

          setSearchParams({
              taskId: newTaskId,
              granularity,
              forecastType: activeType});
          return;
        }

        if (isFailure) {
          clearInterval(pollInterval);
          setIsLoading(false);

          const errorMessage = (payload.message || "").toLowerCase();

          if (errorMessage.includes("'date'") || errorMessage.includes("daily")) {
            alert("Daily data unavailable in the uploaded file. Please upload a new file with daily data.");
            setGranularity('monthly');
          } else {
            alert(`The filtered forecast failed: ${payload.message || "Unknown error"}`);
          }
          return;
        }

      } catch (err) {
        console.error("Polling error:", err);
        clearInterval(pollInterval);
        setIsLoading(false);
        alert("A network error occurred while checking the forecast status.");
      }
    }, 1000);
  };

  return (
    // Replaced hardcoded background with bg-background
    <div className="h-screen w-screen bg-background flex overflow-hidden transition-colors duration-300">
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

          <div className="flex-1 overflow-y-auto pr-4 custom-scrollbar">
            <MetricCards metrics={metricsData} isLoading={isLoading} datasetId={datasetId}/>

            {isLoading ? (
              // Themed Loading State
              <div className="h-[400px] flex flex-col items-center justify-center bg-card rounded-[24px] shadow-sm border border-border mt-6 transition-colors duration-300">
                <Loader2 className="animate-spin text-muted-foreground mb-4" size={32} />
                <p className="text-muted-foreground font-medium transition-colors duration-300">Loading your forecast...</p>
              </div>
            ) : (
              <div className="mt-6">
                {/* Header Row with Toggle and Download Button */}
                {forecastData.length > 0 && (
                  <div className="flex justify-between items-end mb-4 px-2">

                    {/* Left Side: Title & Segmented Toggle */}
                    <div className="flex items-center gap-6">
                      <h3 className="text-lg font-bold text-foreground transition-colors duration-300">Forecast Overview</h3>

                      <div className="flex bg-muted rounded-xl p-1 shadow-inner border border-border transition-colors duration-300">
                        <button
                          onClick={() => {
                              setGranularity('monthly');
                              handleApplyFilters(activeFilters.includes('Global View'), 'monthly');
                              }
                          }
                          className={`px-4 py-1.5 text-sm font-semibold rounded-lg transition-all duration-200 ${
                            granularity === 'monthly'
                              ? 'bg-card text-foreground shadow-sm'
                              : 'text-muted-foreground hover:text-foreground'
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
                              ? 'bg-card text-foreground shadow-sm'
                              : 'text-muted-foreground hover:text-foreground'
                          }`}
                        >
                          Daily
                        </button>
                      </div>
                    </div>

                    {/* Right Side: Export Button (Using your Lime Green Light Accent) */}
                    <button
                      onClick={handleDownloadCSV}
                      className="flex items-center gap-2 px-5 py-2.5 bg-light-accent text-[#09090B] rounded-xl text-sm font-semibold hover:opacity-90 transition-opacity shadow-sm border border-transparent cursor-pointer"
                    >
                      <Download size={16} />
                      Export to CSV
                    </button>
                  </div>
                )}

                {/* --- AI PRESCRIPTIVE INSIGHT CARD --- */}
                {aiInsight && (
                    <div className="mb-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
                        <Alert className="bg- border border- dark:border- shadow- rounded- transition-all duration-300">

                            <Sparkles size={16} className="text-blue-500 animate-pulse" />

                            <AlertTitle className="text- dark:text- font-semibold flex items-center gap-2">
                                FinOps AI Prescriptive Insight
                                {/*
                                  The badge uses your primary button colors, automatically inverting:
                                  Light mode: Black bg, white text. Dark mode: White bg, black text.
                                */}
                                <span className="text-xs bg-light-accent text-[#09090B] px-2 py-0.5 rounded-full font-medium">
                                    Gemma 4
                                </span>
                            </AlertTitle>

                            <AlertDescription className="text- dark:text- mt-2 leading-relaxed font-medium">
                                {aiInsight}
                            </AlertDescription>

                        </Alert>
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
                  <span className="text-sm font-semibold text-muted-foreground mr-2 transition-colors duration-300">Currently Viewing:</span>

                  {activeFilters.includes('Global View') ? (
                    <span className="px-3 py-1 bg-muted text-muted-foreground text-xs font-bold rounded-full border border-border transition-colors duration-300">
                      Global Aggregate
                    </span>
                  ) : (
                    activeFilters.map(filter => {
                      const valueObj = filterValues[filter];
                      const displayValue = valueObj ? valueObj.label : 'All';
                      const filterLabel = filter.replace('By ', '');

                      return (
                        <div key={filter} className="flex items-center bg-muted/60 border border-border rounded-full px-3 py-1.5 shadow-sm transition-colors duration-300">
                          <span className="text-xs font-bold text-muted-foreground mr-1.5 uppercase tracking-wider transition-colors duration-300">{filterLabel}:</span>
                          <span className="text-xs font-bold text-foreground transition-colors duration-300">{displayValue}</span>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
        {/* Right Sidebar Wrapper */}
        <RightSidebar />
      </div>
  );
}