import React, { useState, useEffect } from 'react';
import { Cloud, Server, Database, Save, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { getCsrfToken } from '../../utils/csrf';

export function IntegrationsManager() {
  const [activeTab, setActiveTab] = useState('AWS');
  const [isLoading, setIsLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);

  // Form State
  const [datasetId, setDatasetId] = useState('');
  const [accountId, setAccountId] = useState('');

  // Provider Specific State
  const [awsRoleArn, setAwsRoleArn] = useState('');
  const [azureTenantId, setAzureTenantId] = useState('');
  const [azureClientId, setAzureClientId] = useState('');
  const [azureClientSecret, setAzureClientSecret] = useState('');

  // Existing Integration State (to show if already configured)
  const [existingConfig, setExistingConfig] = useState<any>(null);

  const tabs = [
    { id: 'AWS', name: 'AWS Cost Explorer', icon: <Cloud size={18} /> },
    { id: 'AZURE', name: 'Azure Cost Management', icon: <Server size={18} /> },
    { id: 'GCP', name: 'Google Cloud Billing', icon: <Database size={18} /> },
  ];

  // Fetch existing config when tab changes
  useEffect(() => {
    fetchIntegrationStatus();
  }, [activeTab]);

  const fetchIntegrationStatus = async () => {
    try {
      // Assuming the API can filter by provider: /api/cloud-integrations/?provider=AWS
      const res = await fetch(`/api/cloud-integrations/?provider=${activeTab}`);
      if (res.ok) {
        const data = await res.json();
        // Just grab the first one for the demo, or handle lists if users have multiple AWS accounts
        if (data.length > 0) {
          setExistingConfig(data[0]);
          setAccountId(data[0].account_id);
        } else {
          setExistingConfig(null);
          setAccountId('');
        }
      }
    } catch (err) {
      console.error("Failed to fetch integration", err);
    }
  };

  const handleSaveCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    const payload: any = {
      provider: activeTab,
      dataset_id: datasetId,
      account_id: accountId,
    };

    if (activeTab === 'AWS') payload.role_arn = awsRoleArn;
    if (activeTab === 'AZURE') {
      payload.tenant_id = azureTenantId;
      payload.access_key = azureClientId; // Mapped based on the serializer
      payload.secret_key = azureClientSecret;
    }

    try {
      const method = existingConfig ? 'PATCH' : 'POST';
      const url = existingConfig
        ? `/api/cloud-integrations/${existingConfig.id}/`
        : `/api/cloud-integrations/`;

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        alert("Credentials saved securely.");
        setAwsRoleArn(''); // Clear sensitive inputs
        setAzureClientSecret('');
        fetchIntegrationStatus(); // Refresh UI
      } else {
        const errData = await response.json();
        alert("Error saving: " + JSON.stringify(errData));
      }
    } catch (err) {
      console.error(err);
      alert("Network error.");
    } finally {
      setIsLoading(false);
    }
  };

  const pollTaskStatus = (taskId: string) => {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(`/status/${taskId}/`, {
            credentials: 'same-origin' // Maintain consistency with your other API calls
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json();

          // Safely unwrap the payload based on how your Django view returns it
          const payload = data.data ? data.data : data;
          const currentState = (payload.status || payload.state || '').toLowerCase();

          if (['progress', 'pending', 'started'].includes(currentState)) {
            // You can use payload.message here if your Celery task sends custom progress strings
            setSyncStatus("Sync in progress...");
          }
          else if (['success', 'completed'].includes(currentState)) {
            clearInterval(interval);
            setSyncStatus("Sync complete!");

            // CRUCIAL: Refresh the integration record from Django to get the new 'last_synced_at' timestamp
            fetchIntegrationStatus();

            // Optional UX polish: Revert the button text back to default after 3 seconds
            setTimeout(() => {
              setSyncStatus(null);
            }, 3000);
          }
          else if (['failure', 'error'].includes(currentState)) {
            clearInterval(interval);
            setSyncStatus("Sync failed.");
            alert(`The synchronization failed: ${payload.message || "Please check Celery logs."}`);

            setTimeout(() => {
              setSyncStatus(null);
            }, 3000);
          }

        } catch (err) {
          console.error("Polling error:", err);
          clearInterval(interval);
          setSyncStatus("Error checking status.");

          setTimeout(() => {
            setSyncStatus(null);
          }, 3000);
        }
      }, 1000); // Ping the server every 1 second
    };

    const handleSyncNow = async () => {
      if (!existingConfig) return;
      setSyncStatus("Queuing sync...");

      try {
        const response = await fetch(`/api/cloud-integrations/${existingConfig.id}/sync-now/`, {
          method: 'POST',
          headers: { 'X-CSRFToken': getCsrfToken() }
        });

        if (response.ok) {
          const data = await response.json();
          setSyncStatus("Sync in progress...");

          // Fire the polling loop using the task_id returned from your Django ViewSet
          pollTaskStatus(data.task_id);
        } else {
          // Handle the case where the server explicitly rejects the sync (e.g. inactive integration)
          const errorData = await response.json();
          setSyncStatus("Failed to start.");
          alert(errorData.error || "Failed to start sync.");
          setSyncStatus(null);
        }
      } catch (err) {
        setSyncStatus("Sync failed to start.");
        setTimeout(() => setSyncStatus(null), 3000);
      }
    };

  return (
    <div className="max-w-3xl mx-auto mb-8">
      <div className="bg-card rounded-[24px] p-8 shadow-sm border border-border transition-colors duration-300">

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground tracking-tight mb-2">Cloud Integrations</h1>
          <p className="text-muted-foreground text-sm">Connect your cloud providers to enable automated daily ingestion.</p>
        </div>

        {/* Custom Tabs */}
        <div className="flex space-x-2 mb-8 bg-muted p-1 rounded-xl border border-border">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center space-x-2 py-3 text-sm font-medium rounded-lg transition-all ${
                activeTab === tab.id
                  ? 'bg-card text-foreground shadow-sm border border-border'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab.icon}
              <span>{tab.name}</span>
            </button>
          ))}
        </div>

        {/* Status Indicator */}
        {existingConfig?.is_configured && (
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500/20 rounded-xl flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="text-green-500" size={20} />
              <div>
                <p className="text-sm font-semibold text-foreground">Connection Established</p>
                <p className="text-xs text-muted-foreground">
                  Last synced: {existingConfig.last_synced_at ? new Date(existingConfig.last_synced_at).toLocaleString() : 'Never'}
                </p>
              </div>
            </div>

            <button
              onClick={handleSyncNow}
              className="px-4 py-2 bg-card text-foreground border border-border rounded-lg text-sm font-medium hover:bg-muted transition-colors flex items-center space-x-2"
            >
              <RefreshCw size={16} className={syncStatus?.includes('progress') ? 'animate-spin' : ''} />
              <span>{syncStatus || "Sync Now"}</span>
            </button>
          </div>
        )}

        {/* Credentials Form */}
        <form onSubmit={handleSaveCredentials} className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-foreground mb-2 block uppercase">Dataset ID</label>
              <input
                required
                value={datasetId}
                onChange={(e) => setDatasetId(e.target.value)}
                placeholder="Target Forecast Dataset ID"
                className="w-full bg-background border border-border text-foreground text-sm rounded-xl p-4 outline-none focus:border-ring"
              />
            </div>
            <div>
              <label className="text-xs font-bold text-foreground mb-2 block uppercase">Account ID / Alias</label>
              <input
                required
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
                placeholder="e.g., Prod-Account-1"
                className="w-full bg-background border border-border text-foreground text-sm rounded-xl p-4 outline-none focus:border-ring"
              />
            </div>
          </div>

          <div className="border-t border-border pt-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Security Credentials</h3>

            {activeTab === 'AWS' && (
              <div>
                <label className="text-xs font-bold text-foreground mb-2 block uppercase">Cross-Account Role ARN</label>
                <input
                  required={!existingConfig?.is_configured}
                  value={awsRoleArn}
                  onChange={(e) => setAwsRoleArn(e.target.value)}
                  placeholder={existingConfig?.is_configured ? "******** (Stored securely)" : "arn:aws:iam::..."}
                  className="w-full bg-background border border-border text-foreground text-sm rounded-xl p-4 outline-none focus:border-ring"
                />
              </div>
            )}

            {activeTab === 'AZURE' && (
              <div className="space-y-4">
                <input
                  required={!existingConfig?.is_configured}
                  value={azureTenantId} onChange={(e) => setAzureTenantId(e.target.value)}
                  placeholder="Tenant ID"
                  className="w-full bg-background border border-border text-foreground text-sm rounded-xl p-4"
                />
                <input
                  required={!existingConfig?.is_configured}
                  value={azureClientId} onChange={(e) => setAzureClientId(e.target.value)}
                  placeholder="Client ID"
                  className="w-full bg-background border border-border text-foreground text-sm rounded-xl p-4"
                />
                <input
                  type="password"
                  required={!existingConfig?.is_configured}
                  value={azureClientSecret} onChange={(e) => setAzureClientSecret(e.target.value)}
                  placeholder={existingConfig?.is_configured ? "********" : "Client Secret"}
                  className="w-full bg-background border border-border text-foreground text-sm rounded-xl p-4"
                />
              </div>
            )}

            {/* GCP implementation would follow the same pattern here using a textarea for the JSON */}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-primary text-primary-foreground hover:opacity-90 rounded-xl px-6 py-4 font-semibold text-lg flex items-center justify-center space-x-2 transition-all shadow-sm disabled:opacity-50"
          >
            <Save size={20} />
            <span>{isLoading ? "Saving..." : "Save Credentials"}</span>
          </button>
        </form>

      </div>
    </div>
  );
}