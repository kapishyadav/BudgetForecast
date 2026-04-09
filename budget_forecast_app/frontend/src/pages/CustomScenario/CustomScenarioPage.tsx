import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Play, UploadCloud, Settings2, Sparkles, Info } from 'lucide-react';
import { LeftSidebar } from '../KharchuDashboard/LeftSidebar';
import { RightSidebar } from '../KharchuDashboard/RightSidebar';
import { TopHeader } from '../KharchuDashboard/TopHeader';
import { TabNavigation } from '../KharchuDashboard/TabNavigation';

const MODEL_CONFIGS = {
  prophet: {
    name: 'Prophet',
    params: [
      { key: 'changepoint_prior_scale', label: 'Changepoint Prior Scale', type: 'number', default: 0.05, step: 0.01 },
      { key: 'seasonality_prior_scale', label: 'Seasonality Prior Scale', type: 'number', default: 10.0, step: 0.1 }
    ]
  },
  xgboost: {
    name: 'XGBoost',
    params: [
      { key: 'n_estimators', label: 'N-Estimators', type: 'number', default: 100, step: 10 },
      { key: 'learning_rate', label: 'Learning Rate', type: 'number', default: 0.1, step: 0.01 },
      { key: 'max_depth', label: 'Max Depth', type: 'number', default: 3, step: 1 }
    ]
  },
  catboost: {
    name: 'CatBoost',
    params: [
      { key: 'n_estimators', label: 'Iterations', type: 'number', default: 100, step: 10 },
      { key: 'learning_rate', label: 'Learning Rate', type: 'number', default: 0.1, step: 0.01 },
      { key: 'max_depth', label: 'Depth', type: 'number', default: 6, step: 1 }
    ]
  }
};

export function CustomScenarioPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Core State
  const [datasetId, setDatasetId] = useState(searchParams.get('datasetId') || '');
  const [modelType, setModelType] = useState('xgboost');
  const [hyperparameters, setHyperparameters] = useState<any>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // NEW: Optuna State
  const [isOptunaEnabled, setIsOptunaEnabled] = useState(false);
  const [optunaTrials, setOptunaTrials] = useState(20);

  const [activeFilters, setActiveFilters] = useState<string[]>(['Global View']);
  const [filterValues, setFilterValues] = useState<Record<string, any>>({});

  useEffect(() => {
    const defaults: any = {};
    MODEL_CONFIGS[modelType as keyof typeof MODEL_CONFIGS].params.forEach(param => {
      defaults[param.key] = param.default;
    });
    setHyperparameters(defaults);
  }, [modelType]);

  const handleToggleFilter = (filterName: string) => {
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

  const handleUpdateFilterValue = (filterName: string, selectedOption: any) => {
    setFilterValues(prev => ({ ...prev, [filterName]: selectedOption }));
  };

  const loadOptions = async (inputValue: string, filterName: string) => {
    if (!datasetId || !inputValue) return [];

    const fieldMap: Record<string, string> = {
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
      return (data.suggestions || []).map((item: string) => ({ value: item, label: item }));
    } catch (error) {
      console.error("Error fetching suggestions:", error);
      return [];
    }
  };

  const handleParamChange = (key: string, value: string) => {
    setHyperparameters((prev: any) => ({ ...prev, [key]: parseFloat(value) }));
  };

  const handleApplyFilters = () => {};

  const pollCustomTaskStatus = (newTaskId: string, activeModel: string, mappedForecastType: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/status/${newTaskId}/`);
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        const data = await response.json();
        const payload = data.data ? data.data : data;
        const currentState = (payload.state || payload.status || '').toLowerCase();

        if (['success', 'completed'].includes(currentState)) {
          clearInterval(pollInterval);

          const queryParams = new URLSearchParams({
            taskId: newTaskId,
            model: activeModel,
            forecastType: mappedForecastType,
            granularity: 'monthly'
          });

          const paramMap: Record<string, string> = {
            "By Account": "account_name",
            "By Service": "service_name",
            "By Segment": "segment_name",
            "By BU Code": "bu_code"
          };

          activeFilters.forEach(filter => {
            if (filter !== 'Global View' && filterValues[filter]) {
              queryParams.append(paramMap[filter], filterValues[filter].value);
            }
          });

          navigate(`/kharchu?${queryParams.toString()}`);

        } else if (['failure', 'error'].includes(currentState)) {
          clearInterval(pollInterval);
          setIsSubmitting(false);
          alert(`Scenario failed: ${payload.message || "Unknown error"}`);
        }
      } catch (err) {
        clearInterval(pollInterval);
        setIsSubmitting(false);
      }
    }, 1000);
  };

  const handleRunScenario = async () => {
    if (!datasetId) {
      alert("Please ensure a dataset is selected or uploaded.");
      return;
    }

    let mappedForecastType = "overall_aggregate";
    if (activeFilters.includes("By Segment")) mappedForecastType = "segment";
    if (activeFilters.includes("By BU Code")) mappedForecastType = "bu_code";
    if (activeFilters.includes("By Account")) mappedForecastType = "account";
    if (activeFilters.includes("By Service")) mappedForecastType = "service";

    const missingSelections = activeFilters.filter(filter => filter !== 'Global View' && !filterValues[filter]);
    if (missingSelections.length > 0) {
       return alert(`Please select a value for: ${missingSelections.join(', ')}`);
    }

    setIsSubmitting(true);

    const payload = {
      dataset_id: datasetId,
      model_name: modelType,
      forecast_type: mappedForecastType,
      granularity: "monthly",
      hyperparameters: hyperparameters,
      account_name: filterValues["By Account"]?.value || null,
      service_name: filterValues["By Service"]?.value || null,
      segment_name: filterValues["By Segment"]?.value || null,
      bu_code: filterValues["By BU Code"]?.value || null,
      // NEW: Send Optuna flags to backend
      tune_hyperparameters: isOptunaEnabled,
      tuning_trials: isOptunaEnabled ? optunaTrials : undefined
    };

    try {
      const response = await fetch('/api/run-scenario/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (response.ok && (data.status?.toUpperCase() === "SUCCESS" || response.status === 202)) {
        pollCustomTaskStatus(data.task_id || data.data?.task_id, modelType, mappedForecastType);
      } else {
        alert("Failed: " + (data.message || "Unknown error"));
        setIsSubmitting(false);
      }
    } catch (error) {
      setIsSubmitting(false);
    }
  };

  return (
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

          <div className="flex items-center gap-4 mt-6 mb-8">
            <button onClick={() => navigate(-1)} className="p-2 bg-card border border-border hover:bg-muted rounded-full shadow-sm transition-colors duration-300 cursor-pointer">
              <ArrowLeft size={20} className="text-foreground transition-colors duration-300" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-foreground transition-colors duration-300">Configure Custom Scenario</h1>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-8 max-w-5xl">
            {/* Left Column: Dataset */}
            <div className="col-span-1 space-y-6">
              <div className="bg-card rounded-2xl p-6 shadow-sm border border-border transition-colors duration-300">
                <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2 transition-colors duration-300">
                  <UploadCloud size={18} className="text-primary" /> Dataset Context
                </h3>
                {datasetId && (
                  <div className="bg-muted border border-border p-3 rounded-xl mb-4 text-xs font-mono truncate text-muted-foreground transition-colors duration-300">
                    {datasetId}
                  </div>
                )}
                <button onClick={() => navigate('/upload')} className="w-full py-2.5 border-2 border-dashed border-border rounded-xl text-sm font-semibold text-muted-foreground hover:bg-muted hover:text-foreground transition-all duration-300 cursor-pointer">
                  Upload New Dataset
                </button>
              </div>
            </div>

            {/* Right Column: Algorithms */}
            <div className="col-span-2 space-y-6">
              <div className="bg-card rounded-2xl p-6 shadow-sm border border-border transition-colors duration-300">
                <h3 className="font-semibold text-foreground mb-6 flex items-center gap-2 transition-colors duration-300">
                  <Settings2 size={18} className="text-primary" /> Algorithm Settings
                </h3>

                <div className="flex bg-muted border border-border rounded-xl p-1 mb-8 w-fit transition-colors duration-300">
                  {Object.keys(MODEL_CONFIGS).map(modelKey => (
                    <button
                      key={modelKey}
                      onClick={() => setModelType(modelKey)}
                      className={`px-6 py-2 text-sm font-semibold rounded-lg transition-all duration-200 cursor-pointer ${
                        modelType === modelKey
                          ? 'bg-card text-foreground shadow-sm'
                          : 'text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      {MODEL_CONFIGS[modelKey as keyof typeof MODEL_CONFIGS].name}
                    </button>
                  ))}
                </div>

                {/* Manual Params Grid (Dims if Optuna is active) */}
                <div className={`grid grid-cols-2 gap-6 transition-opacity duration-300 ${isOptunaEnabled ? 'opacity-40 pointer-events-none' : 'opacity-100'}`}>
                  {MODEL_CONFIGS[modelType as keyof typeof MODEL_CONFIGS].params.map(param => (
                    <div key={param.key} className="flex flex-col">
                      <label className="text-sm font-medium text-muted-foreground mb-2 transition-colors duration-300">{param.label}</label>
                      <input
                        type={param.type}
                        step={param.step}
                        value={hyperparameters[param.key] ?? ''}
                        onChange={(e) => handleParamChange(param.key, e.target.value)}
                        disabled={isOptunaEnabled}
                        className="bg-background border border-border text-foreground text-sm rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors duration-300 disabled:cursor-not-allowed"
                      />
                    </div>
                  ))}
                </div>

                {/* Optuna Toggle Section */}
                <div className="mt-8 pt-6 border-t border-border">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h4 className="text-md font-semibold text-foreground flex items-center gap-2">
                        <Sparkles size={16} className="text-blue-500" />
                        Auto-Tune with Optuna
                      </h4>
                      <p className="text-xs text-muted-foreground mt-1">
                        Automatically find the optimal hyperparameters. Overrides manual inputs.
                      </p>
                    </div>

                    {/* Custom Toggle Switch */}
                    <button
                      onClick={() => setIsOptunaEnabled(!isOptunaEnabled)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer ${
                        isOptunaEnabled
                          ? 'bg-blue-600 dark:bg-light-accent'
                          : 'bg-muted border border-border'
                      }`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform shadow-sm ${
                        isOptunaEnabled ? 'translate-x-6' : 'translate-x-1'
                      }`} />
                    </button>
                  </div>

                  {/* Disclaimer & Trial Input (Expands when Optuna is on) */}
                  {isOptunaEnabled && (
                    <div className="bg-blue-500/10 dark:bg-light-accent/10 border border-blue-500/20 dark:border-light-accent/20 rounded-xl p-4 flex flex-col gap-4 animate-in fade-in slide-in-from-top-2 duration-300">
                      <div className="flex items-start gap-3">
                        {/* Swaps to light-accent only in dark mode */}
                        <Info size={18} className="text-blue-600 dark:text-light-accent shrink-0 mt-0.5" />

                        <p className="text-sm text-foreground/80 leading-relaxed">
                          {/* Slightly darker blue for the bold text in light mode for maximum readability */}
                          <strong className="text-blue-700 dark:text-light-accent">Computational Disclaimer:</strong> Hyperparameter tuning requires training the model multiple times. This process is computationally expensive and will take significantly longer to complete than a standard scenario.
                        </p>
                      </div>

                      {/* The divider line matches the active theme */}
                      <div className="flex items-center justify-between border-t border-blue-500/20 dark:border-light-accent/20 pt-3">
                        <label className="text-sm font-medium text-foreground">Number of Trials (Iterative trainings)</label>
                        <input
                          type="number"
                          min={1}
                          max={100}
                          value={optunaTrials}
                          onChange={(e) => setOptunaTrials(parseInt(e.target.value) || 1)}
                          // Focus rings update dynamically based on theme
                          className="bg-background border border-border text-foreground text-sm rounded-lg p-2 w-24 focus:outline-none focus:ring-2 focus:ring-blue-500/50 dark:focus:ring-light-accent/50"
                        />
                      </div>
                    </div>
                  )}
                </div>

              </div>

              <div className="flex justify-end pt-4">
                <button
                  onClick={handleRunScenario}
                  disabled={isSubmitting}
                  className={`flex items-center gap-2 px-8 py-4 rounded-xl font-bold text-lg transition-all cursor-pointer ${
                    isSubmitting
                      ? 'bg-muted text-muted-foreground border border-border cursor-not-allowed'
                      : 'bg-light-accent text-[#09090B] hover:opacity-90 shadow-sm border border-transparent'
                  }`}
                >
                  {isSubmitting ? 'Initializing...' : 'Execute Scenario'}
                  {!isSubmitting && <Play size={20} className="fill-current" />}
                </button>
              </div>
            </div>
          </div>
        </div>
        <RightSidebar />
    </div>
  );
}