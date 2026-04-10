import { useState, useCallback } from 'react';
import axios from 'axios';

export const useHistoricalVisuals = (datasetId: string | null) => {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  const toggleVisuals = useCallback(async () => {
    if (isVisible) {
      setIsVisible(false);
      return;
    }

    if (!datasetId) {
      alert("No active dataset found.");
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.get(`/api/visualize_history/?dataset_id=${datasetId}`);

      // Look for the exact shape from your api_response utility
      if (response.data?.status === "error") {
        console.error("Backend Error:", response.data.message);
        alert(response.data.message || "Failed to load historical data.");
        setIsVisible(false);
        return;
      }

      // Safely unpack the data block
      const payload = response.data.data ? response.data.data : response.data;

      // Log it so we can easily debug the structure in the browser console
      console.log("Historical Data Payload:", payload);

      setData(payload);
      setIsVisible(true);
    } catch (error) {
      console.error("Failed to fetch historical visuals:", error);
      alert("Failed to load historical data visualization.");
    } finally {
      setIsLoading(false);
    }
  }, [datasetId, isVisible]);

  return { data, isLoading, isVisible, toggleVisuals };
};