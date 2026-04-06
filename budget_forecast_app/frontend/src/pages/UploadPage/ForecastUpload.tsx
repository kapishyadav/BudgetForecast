import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileSpreadsheet, Settings2, Rocket, BarChart3, Loader2, ArrowRight, ArrowLeft } from 'lucide-react';
import AsyncSelect from 'react-select/async';
import { getCsrfToken } from '../../utils/csrf';

export function ForecastUpload() {
  const navigate = useNavigate();

  // --- UI Flow State ---
  const [step, setStep] = useState<1 | 2>(1);
  const [isStaging, setIsStaging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Progress tracking states
  const [uploadProgress, setUploadProgress] = useState(0);
  const [forecastProgress, setForecastProgress] = useState(0);
  const [forecastMessage, setForecastMessage] = useState("Initializing model...");

  const [forecastType, setForecastType] = useState('overall_aggregate');
  const [granularity, setGranularity] = useState('monthly');

  // --- Data State ---
  const [file, setFile] = useState<File | null>(null);
  const [datasetId, setDatasetId] = useState<string | null>(null);

  // --- Column Validation States ---
  const [hasDateColumn, setHasDateColumn] = useState<boolean>(true);
  const [hasMonthColumn, setHasMonthColumn] = useState<boolean>(true);

  // States for the dynamic filters
  const [accountName, setAccountName] = useState<any>(null);
  const [serviceName, setServiceName] = useState<any>(null);
  const [buCode, setBuCode] = useState<any>(null);
  const [segmentName, setSegmentName] = useState<any>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);

      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target?.result as string;
        if (text) {
          const firstLine = text.split('\n')[0].toLowerCase();
          const headers = firstLine.split(',').map(h => h.trim().replace(/["\r]/g, ''));
          setHasDateColumn(headers.includes('date'));
          setHasMonthColumn(headers.includes('month'));
        }
      };
      reader.readAsText(selectedFile.slice(0, 1024));
    }
  };

  const handleForecastTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setForecastType(e.target.value);
    setAccountName(null);
    setServiceName(null);
    setBuCode(null);
    setSegmentName(null);
  };

  const handleNext = async () => {
    if (!file) {
      alert("Please select a file first.");
      return;
    }

    if (granularity === 'daily' && !hasDateColumn) {
      alert("Daily data unavailable in the uploaded file. Please upload a new file containing a 'date' column.");
      return;
    }
    if (granularity === 'monthly' && !hasMonthColumn) {
      alert("Monthly data unavailable in the uploaded file. Please upload a new file containing a 'month' column.");
      return;
    }

    setIsStaging(true);
    setUploadProgress(0);

    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) return prev;
        return prev + Math.floor(Math.random() * 10) + 5;
      });
    }, 500);

    const formData = new FormData();
    formData.append('dataset', file);
    formData.append('granularity', granularity);

    try {
      const response = await fetch('/upload/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': getCsrfToken() }
      });

      const data = await response.json();

      if (response.ok && data.dataset_id) {
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
      clearInterval(progressInterval);
      setUploadProgress(0);
      console.error("Upload error details:", err);
      alert("An error occurred during upload. Check the console.");
    } finally {
      setIsStaging(false);
    }
  };

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

  const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!file) return alert("Please upload a dataset first.");

      setIsLoading(true);
      const formData = new FormData();
      formData.append('dataset_id', datasetId as string);
      formData.append('forecast_type', forecastType);
      formData.append('granularity', granularity);

      if (accountName) formData.append('account_name', accountName.value);
      if (serviceName) formData.append('service_name', serviceName.value);
      if (buCode) formData.append('bu_code', buCode.value);
      if (segmentName) formData.append('segment_name', segmentName.value);

      try {
        const response = await fetch('/trigger-forecast/', {
          method: 'POST',
          body: formData,
          credentials: 'same-origin',
          headers: { 'X-CSRFToken' : getCsrfToken() }
        });

        const responseData = await response.json();
        const currentStatus = (responseData.status || '').toLowerCase();
        const taskId = responseData.data?.task_id || responseData.task_id;

        if (currentStatus === "success" && taskId) {
            pollTaskStatus(taskId);
        } else {
            console.error("Backend error:", responseData.errors || responseData.message);
            if (responseData.errors) {
               alert("Validation Error: " + JSON.stringify(responseData.errors));
            } else {
               alert(responseData.message || "Upload failed. Please try again.");
            }
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
        const response = await fetch(`/status/${taskId}/`, { credentials: 'same-origin' });
        if (!response.ok) throw new Error(`HTTP Error! status: ${response.status}`);

        const data = await response.json();
        const currentState = (data.status || data.state || '').toLowerCase();

        if (currentState === 'progress' || currentState === 'pending') {
            const current = data.current || 0;
            const total = data.total || 100;
            setForecastProgress(Math.round((current / total) * 100));
            if (data.message) setForecastMessage(data.message);
        }
        else if (['success', 'completed'].includes(currentState)) {
          clearInterval(interval);
          setForecastProgress(100);
          setForecastMessage("Complete!");
          setTimeout(() => {
            setIsLoading(false);
            navigate(`/kharchu?taskId=${taskId}&granularity=${granularity}&forecastType=${forecastType}`);
          }, 500);
        }
        else if (['failure', 'error'].includes(currentState)) {
          clearInterval(interval);
          setIsLoading(false);
          alert("The forecast generation failed: " + (data.message || "Unknown error"));
        }
      } catch (err) {
        console.error("Polling error. Is Django returning JSON?", err);
        clearInterval(interval);
        setIsLoading(false);
      }
    }, 1000);
  };

  return (
    <div className="max-w-2xl mx-auto mb-8">
      {/* Container Theme applied */}
      <div className="bg-card rounded-[24px] p-8 shadow-sm border border-border transition-colors duration-300">

        {/* Header Area */}
        <div className="mb-8 flex justify-between items-center">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <div className="bg-muted p-2.5 rounded-full text-muted-foreground transition-colors duration-300">
                <BarChart3 size={24} />
              </div>
              <h1 className="text-3xl font-bold text-foreground tracking-tight transition-colors duration-300">Time Series Forecast</h1>
            </div>
            <p className="text-muted-foreground text-sm pl-12 transition-colors duration-300">
              {step === 1 ? "Configure your dataset settings to begin." : "Configure your local forecasting parameters."}
            </p>
          </div>
          <div className="text-sm font-semibold text-muted-foreground bg-muted px-4 py-2 rounded-full transition-colors duration-300">
            Step {step} of 2
          </div>
        </div>

        {/* STEP 1: FILE UPLOAD SECTION */}
        {step === 1 && (
          <div className="space-y-8">

            {/* Granularity Toggle */}
            <div>
              <label className="text-sm font-semibold text-foreground mb-2 block transition-colors duration-300">1. Select Time Granularity</label>
              <div className="flex bg-muted p-1 rounded-xl border border-border transition-colors duration-300">
                {['monthly', 'daily'].map((g) => (
                  <button
                    key={g}
                    type="button"
                    onClick={() => setGranularity(g)}
                    className={`flex-1 py-3 text-sm font-medium rounded-lg transition-all capitalize ${
                      granularity === g
                        ? 'bg-card text-foreground shadow-sm border border-border'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {g}
                  </button>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-2 transition-colors duration-300">
                Ensure your CSV file contains a <strong className="text-foreground transition-colors duration-300">'{granularity === 'daily' ? 'date' : 'month'}'</strong> column.
              </p>
            </div>

            {/* File Upload Dropzone */}
            <div>
              <label className="text-sm font-semibold text-foreground mb-2 block transition-colors duration-300">2. Upload Dataset</label>
              <div className={`relative border-2 border-dashed rounded-[16px] p-8 transition-colors text-center cursor-pointer group ${
                  file ? 'border-green-500/50 bg-green-500/10' : 'border-border bg-muted hover:opacity-80'
                }`}>
                <input type="file" name="dataset" accept=".csv" required onChange={handleFileChange} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
                <div className="flex flex-col items-center justify-center space-y-3 pointer-events-none">
                  <div className={`p-3 rounded-full shadow-sm transition-transform group-hover:scale-110 ${
                    file ? 'bg-green-500/20 text-green-500' : 'bg-card text-foreground'
                  }`}>
                    {file ? <FileSpreadsheet size={24} /> : <UploadCloud size={24} />}
                  </div>
                  <span className={`font-medium transition-colors duration-300 ${
                    file ? 'text-green-600 dark:text-green-400' : 'text-foreground'
                  }`}>
                    {file ? file.name : 'Click to upload or drag and drop'}
                  </span>
                </div>
              </div>
            </div>

            {/* Progress Bar & Button Logic */}
            {isStaging ? (
              <div className="w-full bg-muted p-6 rounded-xl border border-border transition-colors duration-300">
                <div className="flex justify-between text-sm font-semibold text-foreground mb-2 transition-colors duration-300">
                  <span>Parsing and saving to database...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-border rounded-full h-2.5 overflow-hidden transition-colors duration-300">
                  <div
                    className="bg-primary h-2.5 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={handleNext}
                disabled={!file}
                className="w-full bg-primary text-primary-foreground hover:opacity-90 rounded-xl px-6 py-4 font-semibold text-lg flex items-center justify-center space-x-2 transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>Process Dataset</span><ArrowRight size={20} />
              </button>
            )}
          </div>
        )}

        {/* STEP 2: CONFIGURATION SECTION */}
        {step === 2 && (
          <form onSubmit={handleSubmit} className="space-y-6">

            {/* Forecast Type Select */}
            <div>
              <label className="text-sm font-semibold text-foreground mb-2 flex items-center space-x-2 transition-colors duration-300">
                <Settings2 size={16} className="text-muted-foreground" />
                <span>Local Forecast Type</span>
              </label>
              <select value={forecastType} onChange={handleForecastTypeChange} className="w-full bg-background border border-border text-foreground text-sm rounded-xl p-4 appearance-none outline-none transition-colors duration-300">
                <option value="overall_aggregate">Overall Aggregate (No Filter)</option>
                <option value="account">Forecast by Account</option>
                <option value="service">Forecast by Service</option>
                <option value="bu_code">Forecast by BU Code</option>
                <option value="segment">Forecast by Segment</option>
              </select>
            </div>

            {/* DYNAMIC FILTERS */}
            <div className="space-y-4">
              {forecastType === 'account' && (
                <div className="bg-muted border border-border p-5 rounded-xl transition-colors duration-300">
                  <label className="text-xs font-bold text-foreground mb-2 block uppercase">Account Name</label>
                  <AsyncSelect cacheOptions loadOptions={(v) => loadOptions(v, 'account')} onChange={setAccountName} placeholder="Search account..." />
                </div>
              )}

              {forecastType === 'service' && (
                <div className="bg-muted border border-border p-5 rounded-xl transition-colors duration-300">
                  <label className="text-xs font-bold text-foreground mb-2 block uppercase">Service Name</label>
                  <AsyncSelect cacheOptions loadOptions={(v) => loadOptions(v, 'service')} onChange={setServiceName} placeholder="Search service..." />
                </div>
              )}

              {forecastType === 'bu_code' && (
                <div className="bg-muted border border-border p-5 rounded-xl transition-colors duration-300">
                  <label className="text-xs font-bold text-foreground mb-2 block uppercase">BU Code</label>
                  <AsyncSelect cacheOptions loadOptions={(v) => loadOptions(v, 'bu_code')} onChange={setBuCode} placeholder="Search BU code..." />
                </div>
              )}

              {forecastType === 'segment' && (
                <div className="bg-muted border border-border p-5 rounded-xl transition-colors duration-300">
                  <label className="text-xs font-bold text-foreground mb-2 block uppercase">Segment</label>
                  <AsyncSelect cacheOptions loadOptions={(v) => loadOptions(v, 'segment')} onChange={setSegmentName} placeholder="Search segment..." />
                </div>
              )}
            </div>

            {/* Progress Bar & Button Logic */}
            {isLoading ? (
              <div className="w-full bg-light-accent/20 p-6 rounded-xl border border-light-accent transition-colors duration-300">
                <div className="flex justify-between text-sm font-semibold text-foreground mb-2 transition-colors duration-300">
                  <span className="flex items-center gap-2">
                    <Loader2 size={16} className="animate-spin text-foreground" />
                    {forecastMessage}
                  </span>
                  <span>{forecastProgress}%</span>
                </div>
                <div className="w-full bg-card rounded-full h-3 overflow-hidden shadow-inner transition-colors duration-300">
                  <div
                    className="bg-light-accent h-3 rounded-full transition-all duration-500 ease-out relative"
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
                  className="w-1/3 bg-card border border-border text-foreground hover:bg-muted rounded-xl px-6 py-4 font-semibold text-lg flex items-center justify-center space-x-2 transition-all shadow-sm"
                >
                  <ArrowLeft size={20} />
                  <span>Back</span>
                </button>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-2/3 bg-light-accent text-[#09090B] hover:opacity-90 rounded-xl px-6 py-4 font-semibold text-lg flex items-center justify-center space-x-2 transition-all shadow-sm disabled:opacity-50"
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