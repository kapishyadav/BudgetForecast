import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Create plots directory if it doesn't exist
plots_dir = 'plots/spend/html'
os.makedirs(plots_dir, exist_ok=True)

# Load the data
df = pd.read_csv('actual_detail_2025-08-14.csv')

# Convert 'month' column to datetime
df['month'] = pd.to_datetime(df['month'], format='%Y-%m')

# Calculate basic statistics
min_spend = df['spend'].min()
max_spend = df['spend'].max()
print(f"Spend Range: ${min_spend:.2f} to ${max_spend:.2f}")

# Create monthly aggregated dataframe
monthly_spend = df.groupby('month')['spend'].agg([
    'count', 'sum', 'mean', 'median', 'std', 'min', 'max'
]).reset_index()

monthly_spend.columns = ['month', 'record_count', 'total_spend', 'avg_spend',
                         'median_spend', 'std_spend', 'min_spend', 'max_spend']

print("\nMonthly Spend Summary:")
print(monthly_spend.round(2))

# Save helper
def save_plot(fig, filename):
    filepath = os.path.join(plots_dir, filename)
    fig.write_html(filepath)
    print(f"Saved: {filepath}")

# 1. Monthly Total Spend Trend
fig = px.line(monthly_spend, x='month', y='total_spend',
              markers=True, title='Monthly Total Spend Trend')
save_plot(fig, '01_monthly_total_spend_trend.html')

# 2. Monthly Average Spend Trend
fig = px.line(monthly_spend, x='month', y='avg_spend',
              markers=True, title='Monthly Average Spend per Record')
save_plot(fig, '02_monthly_average_spend_trend.html')

# 3. Monthly Record Count
fig = px.bar(monthly_spend, x='month', y='record_count',
             title='Number of Records per Month')
save_plot(fig, '03_monthly_record_count.html')

# 4. Box Plot of Spend by Month
df['month_str'] = df['month'].dt.strftime('%Y-%m')
fig = px.box(df, x='month_str', y='spend', title='Spend Distribution by Month (Box Plot)')
save_plot(fig, '04_spend_distribution_boxplot.html')

# 5. Violin Plot of Spend by Month
fig = px.violin(df, x='month_str', y='spend', box=True, points="all",
                title='Spend Distribution by Month (Violin Plot)')
save_plot(fig, '05_spend_distribution_violin.html')

# 6. Histogram of All Spend Values
fig = px.histogram(df, x='spend', nbins=50, log_y=True,
                   title='Distribution of All Spend Values')
save_plot(fig, '06_spend_distribution_histogram.html')

# 7. Monthly Min/Max/Avg Comparison
fig = go.Figure()
fig.add_trace(go.Scatter(x=monthly_spend['month'], y=monthly_spend['max_spend'],
                         mode='lines+markers', name='Max'))
fig.add_trace(go.Scatter(x=monthly_spend['month'], y=monthly_spend['avg_spend'],
                         mode='lines+markers', name='Average'))
fig.add_trace(go.Scatter(x=monthly_spend['month'], y=monthly_spend['min_spend'],
                         mode='lines+markers', name='Min'))
fig.update_layout(title='Monthly Min/Average/Max Spend Comparison',
                  xaxis_title='Month', yaxis_title='Spend ($)')
save_plot(fig, '07_monthly_min_avg_max_comparison.html')

# 8. Heatmap of Spend by Month and Service
service_month_spend = df.groupby(['serviceName', 'month'])['spend'].sum().unstack(fill_value=0)
top_services = df.groupby('serviceName')['spend'].sum().nlargest(10).index
service_month_spend_top = service_month_spend.loc[top_services]

fig = px.imshow(service_month_spend_top,
                labels=dict(x="Month", y="Service Name", color="Total Spend ($)"),
                x=service_month_spend_top.columns.strftime('%Y-%m'),
                y=service_month_spend_top.index,
                title="Top 10 Services: Monthly Spend Heatmap")
save_plot(fig, '08_services_monthly_heatmap.html')

# 9. Cumulative Spend Over Time
monthly_spend['cumulative_spend'] = monthly_spend['total_spend'].cumsum()
fig = px.line(monthly_spend, x='month', y='cumulative_spend', markers=True,
              title='Cumulative Spend Over Time')
save_plot(fig, '09_cumulative_spend_over_time.html')

# 10. Spend Distribution Percentiles
percentiles = [10, 25, 50, 75, 90, 95, 99]
percentile_values = [np.percentile(df['spend'], p) for p in percentiles]
fig = px.bar(x=[f'{p}%' for p in percentiles], y=percentile_values,
             title='Spend Distribution Percentiles',
             labels={'x': 'Percentile', 'y': 'Spend ($)'})
save_plot(fig, '10_spend_distribution_percentiles.html')

# 11. Monthly Spend Growth Rate
monthly_spend['growth_rate'] = monthly_spend['total_spend'].pct_change() * 100
fig = px.bar(monthly_spend.iloc[1:], x='month', y='growth_rate',
             title='Monthly Spend Growth Rate (%)')
fig.add_hline(y=0, line_dash="dash", opacity=0.5)
save_plot(fig, '11_monthly_spend_growth_rate.html')

# 12. Spend vs Record Count Scatter
fig = px.scatter(monthly_spend, x='record_count', y='total_spend',
                 color=monthly_spend.index, size='avg_spend',
                 title='Total Spend vs Record Count',
                 labels={'color': 'Month Index'})
save_plot(fig, '12_spend_vs_record_count_scatter.html')

# 13. Top 15 Services by Total Spend
top_services_spend = df.groupby('serviceName')['spend'].sum().sort_values(ascending=False).head(15)
fig = px.bar(top_services_spend, x=top_services_spend.values, y=top_services_spend.index,
             orientation='h', title='Top 15 Services by Total Spend',
             labels={'x': 'Total Spend ($)', 'y': 'Service'})
save_plot(fig, '13_top_15_services_by_spend.html')

# 14. Monthly Spend by Top 5 Services
service_categories = df.groupby(['month', 'serviceName'])['spend'].sum().unstack(fill_value=0)
top_5_services = df.groupby('serviceName')['spend'].sum().nlargest(5).index
service_categories_top5 = service_categories[top_5_services]

fig = px.area(service_categories_top5, x=service_categories_top5.index, y=top_5_services,
              title='Monthly Spend by Top 5 Services (Stacked)')
save_plot(fig, '14_monthly_spend_by_top_5_services.html')

# 15. Top 10 Accounts by Spend
top_accounts_spend = df.groupby('accountName')['spend'].sum().sort_values(ascending=False).head(10)
fig = px.bar(top_accounts_spend, x=top_accounts_spend.index, y=top_accounts_spend.values,
             title='Top 10 Accounts by Total Spend')
save_plot(fig, '15_top_10_accounts_by_spend.html')

# 16. Monthly Average Spend with Confidence Intervals
monthly_stats = df.groupby('month')['spend'].agg(['mean', 'std', 'count']).reset_index()
monthly_stats['se'] = monthly_stats['std'] / np.sqrt(monthly_stats['count'])
monthly_stats['ci_95'] = 1.96 * monthly_stats['se']

fig = go.Figure()
fig.add_trace(go.Scatter(x=monthly_stats['month'], y=monthly_stats['mean'],
                         mode='lines+markers', name='Mean Spend'))
fig.add_trace(go.Scatter(x=monthly_stats['month'],
                         y=monthly_stats['mean'] + monthly_stats['ci_95'],
                         mode='lines', name='Upper CI', line=dict(dash='dash')))
fig.add_trace(go.Scatter(x=monthly_stats['month'],
                         y=monthly_stats['mean'] - monthly_stats['ci_95'],
                         mode='lines', name='Lower CI', line=dict(dash='dash'),
                         fill='tonexty'))
fig.update_layout(title='Monthly Average Spend with 95% Confidence Intervals',
                  xaxis_title='Month', yaxis_title='Spend ($)')
save_plot(fig, '16_monthly_average_spend_with_confidence_intervals.html')

# 17. Spend by Usage Family
usage_family_spend = df.groupby('usageFamily')['spend'].sum().sort_values(ascending=False)
fig = px.bar(usage_family_spend, x=usage_family_spend.index, y=usage_family_spend.values,
             title='Total Spend by Usage Family')
save_plot(fig, '17_spend_by_usage_family.html')

# 18. Monthly Spend by Region
region_monthly_spend = df.groupby(['month', 'region'])['spend'].sum().unstack(fill_value=0)
fig = px.line(region_monthly_spend, x=region_monthly_spend.index, y=region_monthly_spend.columns,
              title='Monthly Spend Trend by Region')
save_plot(fig, '18_monthly_spend_trend_by_region.html')

print(f"\n✅ Analysis complete! All interactive plots saved as HTML in {plots_dir}/")
