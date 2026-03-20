import React, { useState } from 'react';
import { UploadCloud, FileSpreadsheet, Settings2, Rocket, BarChart3 } from 'lucide-react';

export function ForecastUpload() {
  const [forecastType, setForecastType] = useState('overall_aggregate');
  const [granularity, setGranularity] = useState('monthly');
  const [fileName, setFileName] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFileName(e.target.files[0].name);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Add your form submission logic/API call here
    console.log("Submitting forecast config...");
  };

  return (
    <div className="max-w-2xl mx-auto mb-8">
      <div className="bg-white rounded-[24px] p-8 shadow-sm border border-gray-50">

        {/* Header Section */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <div className="bg-gray-50 p-2.5 rounded-full text-gray-500">
              <BarChart3 size={24} />
            </div>
            <h1 className="text-3xl font-bold text-[#1A1A1A] tracking-tight">Time Series Forecast</h1>
          </div>
          <p className="text-gray-500 text-sm pl-12">
            Upload your CSV file to generate a Prophet-based budget forecast.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">

          {/* File Upload Zone */}
          <div>
            <label className="text-sm font-semibold text-gray-700 mb-2 block">Dataset</label>
            <div className="relative border-2 border-dashed border-gray-200 rounded-[16px] p-8 bg-gray-50 hover:bg-gray-100/50 transition-colors text-center cursor-pointer group">
              <input
                type="file"
                name="dataset"
                accept=".csv"
                required
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              />
              <div className="flex flex-col items-center justify-center space-y-3 pointer-events-none">
                <div className="bg-white p-3 rounded-full shadow-sm text-blue-500 group-hover:scale-110 transition-transform">
                  {fileName ? <FileSpreadsheet size={24} /> : <UploadCloud size={24} />}
                </div>
                <div>
                  <span className="font-medium text-[#1A1A1A]">
                    {fileName ? fileName : 'Click to upload or drag and drop'}
                  </span>
                  <p className="text-xs text-gray-500 mt-1">CSV files only</p>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Granularity Toggle */}
            <div>
              <label className="text-sm font-semibold text-gray-700 mb-2 block">Time Granularity</label>
              <div className="flex bg-gray-50 p-1 rounded-xl border border-gray-100">
                <button
                  type="button"
                  onClick={() => setGranularity('monthly')}
                  className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${
                    granularity === 'monthly' ? 'bg-white text-[#1A1A1A] shadow-sm' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Monthly
                </button>
                <button
                  type="button"
                  onClick={() => setGranularity('daily')}
                  className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${
                    granularity === 'daily' ? 'bg-white text-[#1A1A1A] shadow-sm' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Daily
                </button>
              </div>
            </div>

            {/* Forecast Type Select */}
            <div>
              <label className="text-sm font-semibold text-gray-700 mb-2 flex items-center space-x-2">
                <Settings2 size={16} className="text-gray-400" />
                <span>Forecast Type</span>
              </label>
              <select
                name="forecast_type"
                value={forecastType}
                onChange={(e) => setForecastType(e.target.value)}
                className="w-full bg-gray-50 border border-gray-200 text-[#1A1A1A] text-sm rounded-xl focus:ring-[#1A1A1A] focus:border-[#1A1A1A] block p-3 appearance-none outline-none transition-all"
                required
              >
                <option value="overall_aggregate">Overall Aggregate (No Filter)</option>
                <option value="account">Forecast by Account</option>
                <option value="service">Forecast by Service</option>
                <option value="bu_code">Forecast by BU Code</option>
                <option value="segment">Forecast by Segment</option>
              </select>
            </div>
          </div>

          {/* Conditional Selects based on Forecast Type */}
          {forecastType !== 'overall_aggregate' && (
            <div className="bg-blue-50/50 border border-blue-100 rounded-[16px] p-5 animate-in fade-in slide-in-from-top-2 duration-300">
              <label className="text-sm font-semibold text-[#1A1A1A] mb-2 block capitalize">
                Select {forecastType.replace('_', ' ')}
              </label>
              <select
                name={`${forecastType}_name`}
                className="w-full bg-white border border-gray-200 text-[#1A1A1A] text-sm rounded-xl focus:ring-[#1A1A1A] focus:border-[#1A1A1A] block p-3 outline-none shadow-sm"
              >
                <option value="">-- Choose an option --</option>
                {/* Populate these options dynamically from your API based on the forecastType */}
                <option value="opt1">Sample Option 1</option>
                <option value="opt2">Sample Option 2</option>
              </select>
            </div>
          )}

          {/* Submit Button */}
          <div className="pt-4">
            <button
              type="submit"
              className="w-full bg-[#EAFF52] text-[#1A1A1A] hover:bg-[#d9ed42] rounded-xl px-6 py-4 font-semibold text-lg flex items-center justify-center space-x-2 transition-colors shadow-sm"
            >
              <span>Run Forecast</span>
              <Rocket size={20} />
            </button>
          </div>
        </form>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-gray-100 flex justify-center items-center text-xs text-gray-400 font-medium">
          Built with <span className="text-gray-600 font-semibold mx-1">Prophet</span> · React
        </div>

      </div>
    </div>
  );
}