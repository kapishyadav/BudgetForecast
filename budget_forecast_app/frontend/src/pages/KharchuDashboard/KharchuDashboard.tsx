import { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, LogOut } from 'lucide-react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { LeftSidebar } from './LeftSidebar';
import { TopHeader } from './TopHeader';
import { RightSidebar } from './RightSidebar';
import { TabNavigation } from './TabNavigation';
import { MetricCards } from './MetricCards';
import { StatisticsChart } from './StatisticsChart';

export function KharchuDashboard() {
  const [forecastData, setForecastData] = useState([]);
  const [historicalData, setHistoricalData] = useState([]);
  const [metricsData, setMetricsData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Extract the Celery task ID from the URL (e.g., /kharchu?taskId=123-abc)
  const [searchParams] = useSearchParams();
  const taskId = searchParams.get('taskId');

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
      } catch (error) {
        console.error("Failed to load dashboard data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [taskId]); // Add taskId as a dependency

  return (
    <div className="min-h-screen bg-[#E5E0D8] p-4 flex justify-center items-center">
      <div className="bg-[#F5F1EB] rounded-[40px] shadow-2xl w-full max-w-[1600px] h-[95vh] flex overflow-hidden border border-white/40">

        <LeftSidebar />

        <div className="flex-1 flex flex-col py-8 px-2 overflow-hidden">
          <TopHeader />
          <TabNavigation />

          <div className="flex-1 overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-gray-300">
            <MetricCards metrics={metricsData} isLoading={isLoading} />

            {isLoading ? (
              <div className="h-[400px] flex flex-col items-center justify-center bg-white rounded-[24px] shadow-sm border border-gray-100 mt-6">
                <Loader2 className="animate-spin text-gray-400 mb-4" size={32} />
                <p className="text-gray-500 font-medium">Loading your forecast...</p>
              </div>
            ) : (
              <StatisticsChart forecast={forecastData} historical={historicalData} />
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
