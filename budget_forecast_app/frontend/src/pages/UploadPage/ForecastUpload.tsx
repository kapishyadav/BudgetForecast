import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileSpreadsheet, Settings2, Rocket, BarChart3, Loader2, ArrowRight, ArrowLeft } from 'lucide-react';
import AsyncSelect from 'react-select/async';
import { getCsrfToken } from '../../utils/csrf';

export function ForecastUpload() {
  const navigate = useNavigate();

  // --- UI Flow State ---
  const [step, setStep] = useState<1 | 2>(1);
  const [isStaging, setIsStaging] = useState(false); // For Step 1 loading
  const [isLoading, setIsLoading] = useState(false); // For Step 2 loading

  // Progress tracking states
  const [uploadProgress, setUploadProgress] = useState(0);
  const [forecastProgress, setForecastProgress] = useState(0);
  const [forecastMessage, setForecastMessage] = useState("Initializing model...");

  const [forecastType, setForecastType] = useState('overall_aggregate');
  const [granularity, setGranularity] = useState('monthly');

  // --- Data State ---
  const [file, setFile] = useState<File | null>(null);
  const [datasetId, setDatasetId] = useState<string | null>(null);

  // States for the dynamic filters
  const [accountName, setAccountName] = useState(null);
  const [serviceName, setServiceName] = useState(null);
  const [buCode, setBuCode] = useState(null);
  const [segmentName, setSegmentName] = useState(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  // ==========================================
  // UPLOAD FILE & GET DATASET ID
  // ==========================================
  const handleNext = async () => {
    if (!file) {
      alert("Please select a file first.");
      return;
    }

    setIsStaging(true);
    setUploadProgress(0);

    // 1. Declare at the very top of the function scope
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) return prev;
        return prev + Math.floor(Math.random() * 10) + 5;
      });
    }, 500);

    const formData = new FormData();
    formData.append('dataset', file);

    try {
      const response = await fetch('/upload/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': getCsrfToken() }
      });

      const data = await response.json();

      if (response.ok && data.dataset_id) {
        // 2. Clear using the exact same variable name
        clearInterval(progressInterval);
        setUploadProgress(100);

        setTimeout(() => {
          setDatasetId(data.dataset_id);
          setStep(2);
        }, 500);
      } else {
        throw new Error(data.message || "Upload failed");
      }
    } catch (err) {
      // 3. Clear here as well to prevent memory leaks if the server crashes
      clearInterval(progressInterval);
      setUploadProgress(0);
      console.error("Upload error details:", err);
      alert("An error occurred during upload. Check the console.");
    } finally {
      setIsStaging(false);
    }
  };

  // ==========================================
  // DYNAMIC SUGGESTIONS (Requires Dataset ID)
  // ==========================================
  const loadOptions = async (inputValue: string, field: string) => {
    if (!inputValue || !datasetId) return [];
    try {
      // Pass the dataset_id so Postgres only searches this specific file's data
      const response = await fetch(`/get_suggestions/?q=${inputValue}&field=${field}&dataset_id=${datasetId}`);
      const data = await response.json();
      return (data.suggestions || []).map((item: string) => ({ value: item, label: item }));
    } catch (error) {
      console.error("Error fetching suggestions:", error);
      return [];
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!file) return alert("Please upload a dataset first.");

      setIsLoading(true);
      const formData = new FormData();
      formData.append('dataset_id', datasetId);
      formData.append('forecast_type', forecastType);
      formData.append('granularity', granularity);

      // Append conditional fields if they exist
      if (accountName) formData.append('account_name', accountName.value);
      if (serviceName) formData.append('service_name', serviceName.value);
      if (buCode) formData.append('bu_code', buCode.value);
      if (segmentName) formData.append('segment_name', segmentName.value);

      try {
        // 1. Submit the Forecast request via the Vite proxy to Django
        const response = await fetch('/trigger-forecast/', {
          method: 'POST',
          body: formData,
          credentials: 'same-origin',
          headers: {
              'X-CSRFToken' : getCsrfToken(),
              }
        });

        // 2. Parse the JSON response returned by your updated Django view
        const data = await response.json();

        // 3. Extract task_id and start polling
        if (data.task_id) {
            pollTaskStatus(data.task_id);
        } else {
            // Handle cases where the backend returns an error message instead of a task_id
            console.error("Backend error:", data.message || "Unknown error");
            alert(data.message || "Upload failed. Please try again.");
            setIsLoading(false);
        }
      } catch (err) {
        console.error("Upload failed:", err);
        alert("Network error occurred during upload.");
        setIsLoading(false);
      }
  };

  const pollTaskStatus = (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/status/${taskId}/`, {
            credentials: 'same-origin'
            });
        const data = await response.json()
        // Update the progress bar based on Celery's reported progress
        if (data.status === 'PROGRESS') {
            const current = data.current || 0;
            const total = data.total || 100;
            setForecastProgress(Math.round((current / total) * 100));
            if (data.message) setForecastMessage(data.message);
        }
        // Check the JSON's standard "state" or "status" key
        else if (data.status === 'SUCCESS' || data.state === 'SUCCESS') {
          clearInterval(interval);
          setForecastProgress(100);
          setForecastMessage("Complete!");
          setTimeout(() => {
            setIsLoading(false);
            navigate(`/kharchu?taskId=${taskId}`); // Include the Task ID to retrieve directly from Celery
          }, 500);
        }
        else if (data.status === 'FAILURE' || data.state === 'FAILURE' || data.status === 'error') {
          // Handle backend errors gracefully
          clearInterval(interval);
          setIsLoading(false);
          alert("The forecast generation failed: " + (data.message || "Unknown error"));
        }
        } catch (err) {
        // If the fetch fails (or the JSON parse fails because Django returned HTML)
        console.error("Polling error. Is Django returning JSON?", err);
        clearInterval(interval);
        setIsLoading(false);
      }
    }, 1000); // Poll slightly faster (1.0s) for smoother progress updates
  };

  return (
    <div className="max-w-2xl mx-auto mb-8">
      <div className="bg-white rounded-[24px] p-8 shadow-sm border border-gray-50">

        {/* Header Area */}
        <div className="mb-8 flex justify-between items-center">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <div className="bg-gray-50 p-2.5 rounded-full text-gray-500">
                <BarChart3 size={24} />
              </div>
              <h1 className="text-3xl font-bold text-[#1A1A1A] tracking-tight">Time Series Forecast</h1>
            </div>
            <p className="text-gray-500 text-sm pl-12">
              {step === 1 ? "Upload your dataset to begin." : "Configure your forecasting parameters."}
            </p>
          </div>
          <div className="text-sm font-semibold text-gray-400 bg-gray-50 px-4 py-2 rounded-full">
            Step {step} of 2
          </div>
        </div>

        {/* ============================== */}
        {/* STEP 1: FILE UPLOAD SECTION    */}
        {/* ============================== */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <label className="text-sm font-semibold text-gray-700 mb-2 block">Dataset</label>
              <div className="relative border-2 border-dashed border-gray-200 rounded-[16px] p-8 bg-gray-50 hover:bg-gray-100/50 transition-colors text-center cursor-pointer group">
                <input type="file" name="dataset" accept=".csv" required onChange={handleFileChange} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
                <div className="flex flex-col items-center justify-center space-y-3 pointer-events-none">
                  <div className="bg-white p-3 rounded-full shadow-sm text-blue-500 group-hover:scale-110 transition-transform">
                    {file ? <FileSpreadsheet size={24} /> : <UploadCloud size={24} />}
                  </div>
                  <span className="font-medium text-[#1A1A1A]">{file ? file.name : 'Click to upload or drag and drop'}</span>
                </div>
              </div>
            </div>

            {/* ---> PROGRESS BAR & BUTTON LOGIC <--- */}
            {isStaging ? (
              <div className="w-full bg-gray-50 p-6 rounded-xl border border-gray-100">
                <div className="flex justify-between text-sm font-semibold text-gray-700 mb-2">
                  <span>Parsing and saving to database...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-black h-2.5 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={handleNext}
                disabled={!file}
                className="w-full bg-[#1A1A1A] text-white hover:bg-black rounded-xl px-6 py-4 font-semibold text-lg flex items-center justify-center space-x-2 transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>Next Step</span><ArrowRight size={20} />
              </button>
            )}
          </div>
        )}

        {/* ============================== */}
        {/* STEP 2: CONFIGURATION SECTION  */}
        {/* ============================== */}
        {step === 2 && (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Granularity Toggle */}
              <div>
                <label className="text-sm font-semibold text-gray-700 mb-2 block">Time Granularity</label>
                <div className="flex bg-gray-50 p-1 rounded-xl border border-gray-100">
                  {['monthly', 'daily'].map((g) => (
                    <button key={g} type="button" onClick={() => setGranularity(g)} className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all capitalize ${granularity === g ? 'bg-white text-[#1A1A1A] shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>{g}</button>
                  ))}
                </div>
              </div>

              {/* Forecast Type Select */}
              <div>
                <label className="text-sm font-semibold text-gray-700 mb-2 flex items-center space-x-2">
                  <Settings2 size={16} className="text-gray-400" />
                  <span>Forecast Type</span>
                </label>
                <select value={forecastType} onChange={(e) => setForecastType(e.target.value)} className="w-full bg-gray-50 border border-gray-200 text-[#1A1A1A] text-sm rounded-xl p-3 appearance-none outline-none transition-all">
                  <option value="overall_aggregate">Overall Aggregate (No Filter)</option>
                  <option value="account">Forecast by Account</option>
                  <option value="service">Forecast by Service</option>
                  <option value="bu_code">Forecast by BU Code</option>
                  <option value="segment">Forecast by Segment</option>
                </select>
              </div>
            </div>

            {/* DYNAMIC FILTERS */}
            <div className="space-y-4">
              {(['account', 'service', 'segment'].includes(forecastType)) && (
                <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-100">
                  <label className="text-xs font-bold text-blue-600 mb-2 block uppercase">Account Name</label>
                  <AsyncSelect cacheOptions loadOptions={(v) => loadOptions(v, 'account')} onChange={setAccountName} placeholder="Search account..." />
                </div>
              )}

              {(['service', 'segment'].includes(forecastType)) && (
                <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-100">
                  <label className="text-xs font-bold text-blue-600 mb-2 block uppercase">Service Name</label>
                  <AsyncSelect cacheOptions loadOptions={(v) => loadOptions(v, 'service')} onChange={setServiceName} placeholder="Search service..." />
                </div>
              )}

              {forecastType === 'bu_code' && (
                <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-100">
                  <label className="text-xs font-bold text-blue-600 mb-2 block uppercase">BU Code</label>
                  <AsyncSelect cacheOptions loadOptions={(v) => loadOptions(v, 'bu_code')} onChange={setBuCode} placeholder="Search BU code..." />
                </div>
              )}

              {forecastType === 'segment' && (
                <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-100">
                  <label className="text-xs font-bold text-blue-600 mb-2 block uppercase">Segment</label>
                  <AsyncSelect cacheOptions loadOptions={(v) => loadOptions(v, 'segment')} onChange={setSegmentName} placeholder="Search segment..." />
                </div>
              )}
            </div>

            {/* ---> PROGRESS BAR & BUTTON LOGIC <--- */}
            {isLoading ? (
              <div className="w-full col-span-2 bg-[#EAFF52]/20 p-6 rounded-xl border border-[#EAFF52]">
                <div className="flex justify-between text-sm font-semibold text-gray-800 mb-2">
                  <span className="flex items-center gap-2">
                    <Loader2 size={16} className="animate-spin" />
                    {forecastMessage}
                  </span>
                  <span>{forecastProgress}%</span>
                </div>
                <div className="w-full bg-white rounded-full h-3 overflow-hidden shadow-inner">
                  <div
                    className="bg-[#c2d62e] h-3 rounded-full transition-all duration-500 ease-out relative"
                    style={{ width: `${forecastProgress}%` }}
                  >
                    <div className="absolute top-0 left-0 right-0 bottom-0 bg-white/20 animate-pulse"></div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  disabled={isLoading}
                  className="w-1/3 bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 rounded-xl px-6 py-4 font-semibold text-lg flex items-center justify-center space-x-2 transition-all shadow-sm"
                >
                  <ArrowLeft size={20} />
                  <span>Back</span>
                </button>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-2/3 bg-[#EAFF52] text-[#1A1A1A] hover:bg-[#d9ed42] rounded-xl px-6 py-4 font-semibold text-lg flex items-center justify-center space-x-2 transition-all shadow-sm disabled:opacity-50"
                >
                  <span>Run Forecast</span><Rocket size={20} />
                </button>
              </div>
            )}
          </form>
        )}

      </div>
    </div>
  );
}