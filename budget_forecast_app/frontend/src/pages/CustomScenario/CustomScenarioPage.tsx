import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Play, UploadCloud, Settings2 } from 'lucide-react';
import { LeftSidebar } from '../KharchuDashboard/LeftSidebar';
import { TopHeader } from '../KharchuDashboard/TopHeader';
import AsyncSelect from 'react-select/async';

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
  const [forecastType, setForecastType] = useState('overall_aggregate');
  const [hyperparameters, setHyperparameters] = useState<any>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // --- ADDED: Missing Filter States ---
  const [accountName, setAccountName] = useState<any>(null);
  const [serviceName, setServiceName] = useState<any>(null);
  const [segmentName, setSegmentName] = useState<any>(null);
  const [buCode, setBuCode] = useState<any>(null);

  useEffect(() => {
    const defaults: any = {};
    MODEL_CONFIGS[modelType as keyof typeof MODEL_CONFIGS].params.forEach(param => {
      defaults[param.key] = param.default;
    });
    setHyperparameters(defaults);
  }, [modelType]);

  // --- ADDED: Missing loadOptions function ---
  const loadOptions = async (inputValue: string, field: string) => {
    if (!inputValue || !datasetId) return [];
    try {
      const response = await fetch(`/get_suggestions/?q=${inputValue}&field=${field}&dataset_id=${datasetId}`);
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

  const pollCustomTaskStatus = (newTaskId: string, activeModel: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/status/${newTaskId}/`);
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        const data = await response.json();
        const payload = data.data ? data.data : data;
        const currentState = (payload.state || payload.status || '').toLowerCase();

        if (['success', 'completed'].includes(currentState)) {
          clearInterval(pollInterval);
          navigate(`/kharchu?taskId=${newTaskId}&model=${activeModel}`);
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

    // --- Validation Logic ---
    if (forecastType === 'account' && !accountName) return alert("Please select an Account.");
    if (forecastType === 'service' && !serviceName) return alert("Please select a Service.");
    if (forecastType === 'segment' && !segmentName) return alert("Please select a Segment.");
    if (forecastType === 'bu_code' && !buCode) return alert("Please select a BU Code.");

    setIsSubmitting(true);

    const payload = {
      dataset_id: datasetId,
      model_name: modelType,
      forecast_type: forecastType,
      granularity: "monthly",
      hyperparameters: hyperparameters,
      // Pass the selected values
      account_name: accountName?.value,
      service_name: serviceName?.value,
      segment_name: segmentName?.value,
      bu_code: buCode?.value
    };

    try {
      const response = await fetch('/api/run-scenario/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (response.ok && (data.status === "success" || data.status === "SUCCESS")) {
        pollCustomTaskStatus(data.task_id || data.data?.task_id, modelType);
      } else {
        alert("Failed: " + (data.message || "Unknown error"));
        setIsSubmitting(false);
      }
    } catch (error) {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#E5E0D8] p-4 flex justify-center items-center">
      <div className="bg-[#F5F1EB] rounded-[40px] shadow-2xl w-full max-w-[1600px] h-[95vh] flex overflow-hidden border border-white/40">
        <LeftSidebar />
        <div className="flex-1 flex flex-col py-8 px-8 overflow-y-auto custom-scrollbar">
          <TopHeader />

          <div className="flex items-center gap-4 mt-6 mb-8">
            <button onClick={() => navigate(-1)} className="p-2 bg-white rounded-full shadow-sm">
              <ArrowLeft size={20} className="text-gray-600" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-[#1A1A1A]">Configure Custom Scenario</h1>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-8 max-w-5xl">
            <div className="col-span-1 space-y-6">
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <UploadCloud size={18} className="text-blue-500" /> Dataset Context
                </h3>
                {datasetId && (
                  <div className="bg-gray-50 border border-gray-200 p-3 rounded-xl mb-4 text-xs font-mono truncate">
                    {datasetId}
                  </div>
                )}
                <button onClick={() => navigate('/upload')} className="w-full py-2.5 border-2 border-dashed border-gray-300 rounded-xl text-sm">
                  Upload New Dataset
                </button>
              </div>

              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-semibold text-gray-800 mb-4">Forecast Target</h3>
                <select
                  className="w-full bg-gray-50 border border-gray-200 text-sm rounded-xl p-3 mb-6"
                  value={forecastType}
                  onChange={(e) => {
                    setForecastType(e.target.value);
                    setAccountName(null); setServiceName(null); setSegmentName(null); setBuCode(null);
                  }}
                >
                  <option value="overall_aggregate">Global View (Aggregate)</option>
                  <option value="account">By Account</option>
                  <option value="service">By Service</option>
                  <option value="segment">By Segment</option>
                  <option value="bu_code">By BU Code</option>
                </select>

                <div className="space-y-4">
                  {forecastType === 'account' && <AsyncSelect cacheOptions loadOptions={(v) => loadOptions(v, 'account')} onChange={setAccountName} placeholder="Search account..." />}
                  {forecastType === 'service' && <AsyncSelect cacheOptions loadOptions={(v) => loadOptions(v, 'service')} onChange={setServiceName} placeholder="Search service..." />}
                  {forecastType === 'segment' && <AsyncSelect cacheOptions loadOptions={(v) => loadOptions(v, 'segment')} onChange={setSegmentName} placeholder="Search segment..." />}
                  {forecastType === 'bu_code' && <AsyncSelect cacheOptions loadOptions={(v) => loadOptions(v, 'bu_code')} onChange={setBuCode} placeholder="Search BU code..." />}
                </div>
              </div>
            </div> {/* Column 1 Close */}

            <div className="col-span-2 space-y-6">
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-semibold text-gray-800 mb-6 flex items-center gap-2">
                  <Settings2 size={18} className="text-purple-500" /> Algorithm Settings
                </h3>
                <div className="flex bg-[#E5E0D8] rounded-xl p-1 mb-8 w-fit">
                  {Object.keys(MODEL_CONFIGS).map(modelKey => (
                    <button
                      key={modelKey}
                      onClick={() => setModelType(modelKey)}
                      className={`px-6 py-2 text-sm font-semibold rounded-lg ${modelType === modelKey ? 'bg-white text-black' : 'text-gray-500'}`}
                    >
                      {MODEL_CONFIGS[modelKey as keyof typeof MODEL_CONFIGS].name}
                    </button>
                  ))}
                </div>
                <div className="grid grid-cols-2 gap-6">
                  {MODEL_CONFIGS[modelType as keyof typeof MODEL_CONFIGS].params.map(param => (
                    <div key={param.key} className="flex flex-col">
                      <label className="text-sm font-medium text-gray-600 mb-2">{param.label}</label>
                      <input
                        type={param.type}
                        step={param.step}
                        value={hyperparameters[param.key] ?? ''}
                        onChange={(e) => handleParamChange(param.key, e.target.value)}
                        className="bg-gray-50 border border-gray-200 text-sm rounded-xl p-3"
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <button
                  onClick={handleRunScenario}
                  disabled={isSubmitting}
                  className={`flex items-center gap-2 px-8 py-4 rounded-xl font-bold text-lg ${isSubmitting ? 'bg-gray-200 text-gray-400' : 'bg-[#D4FF00] text-black'}`}
                >
                  {isSubmitting ? 'Initializing...' : 'Execute Scenario'}
                  {!isSubmitting && <Play size={20} className="fill-current" />}
                </button>
              </div>
            </div> {/* Column 2 Close */}
          </div> {/* Grid Close */}
        </div> {/* Content Close */}
      </div> {/* Card Close */}
    </div> // Page Close
  );
}