import React, { useState, useEffect } from 'react';
import { UploadCloud, FileSpreadsheet, Settings2, Rocket, BarChart3, Loader2 } from 'lucide-react';
import AsyncSelect from 'react-select/async';

export function ForecastUpload() {
  const [forecastType, setForecastType] = useState('overall_aggregate');
  const [granularity, setGranularity] = useState('monthly');
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);

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

  // Helper to fetch suggestions from your Django backend
  const loadOptions = async (inputValue: string, field: string) => {
    if (!inputValue) return [];
    try {
      const response = await fetch(`/get_suggestions/?q=${inputValue}&field=${field}`);
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
    formData.append('dataset', file);
    formData.append('forecast_type', forecastType);
    formData.append('granularity', granularity);

    // Append conditional fields if they exist
    if (accountName) formData.append('account_name', accountName.value);
    if (serviceName) formData.append('service_name', serviceName.value);
    if (buCode) formData.append('bu_code', buCode.value);
    if (segmentName) formData.append('segment_name', segmentName.value);

    try {
      // 1. Submit the Forecast request
      const response = await fetch('/upload/', { method: 'POST', body: formData });

      // Since your Django view currently returns an HTML snippet for HTMX,
      // we need to extract the task_id from that HTML or update the view to return JSON.
      const htmlText = await response.text();
      const taskIdMatch = htmlText.match(/task_id="([^"]+)"/);
      const taskId = taskIdMatch ? taskIdMatch[1] : null;

      if (taskId) {
          pollTaskStatus(taskId);
      }
    } catch (err) {
      console.error("Upload failed", err);
      setIsLoading(false);
    }
  };

  const pollTaskStatus = (taskId: string) => {
    const interval = setInterval(async () => {
      const res = await fetch(`/status/${taskId}/`);
      const statusHtml = await res.text();

      // Check if the task is finished by looking for dashboard results in the response
      if (statusHtml.includes('id="dashboard-results"')) {
        clearInterval(interval);
        window.location.href = "/kharchu"; // Redirect to your dashboard page
      }
    }, 2000);
  };

  return (
    <div className="max-w-2xl mx-auto mb-8">
      <div className="bg-white rounded-[24px] p-8 shadow-sm border border-gray-50">
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <div className="bg-gray-50 p-2.5 rounded-full text-gray-500">
              <BarChart3 size={24} />
            </div>
            <h1 className="text-3xl font-bold text-[#1A1A1A] tracking-tight">Time Series Forecast</h1>
          </div>
          <p className="text-gray-500 text-sm pl-12">Generate a Prophet-based budget forecast.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Dataset Upload */}
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

          {/* DYNAMIC FILTERS (Mirroring upload.js logic) */}
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

          <button type="submit" disabled={isLoading} className="w-full bg-[#EAFF52] text-[#1A1A1A] hover:bg-[#d9ed42] rounded-xl px-6 py-4 font-semibold text-lg flex items-center justify-center space-x-2 transition-all shadow-sm">
            {isLoading ? <Loader2 className="animate-spin" size={20} /> : <><span>Run Forecast</span><Rocket size={20} /></>}
          </button>
        </form>
      </div>
    </div>
  );
}