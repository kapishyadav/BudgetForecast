import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Create plots directory if it doesn't exist
plots_dir = 'plots/spend'
os.makedirs(plots_dir, exist_ok=True)

# Set style for better visualizations
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

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
    'count',           # Number of records per month
    'sum',            # Total spend per month
    'mean',           # Average spend per record per month
    'median',         # Median spend per record per month
    'std',            # Standard deviation
    'min',            # Minimum spend per month
    'max'             # Maximum spend per month
]).reset_index()

monthly_spend.columns = ['month', 'record_count', 'total_spend', 'avg_spend', 'median_spend', 'std_spend', 'min_spend', 'max_spend']

print("\nMonthly Spend Summary:")
print(monthly_spend.round(2))

# Function to save plot
def save_plot(fig, filename, dpi=300):
    """Save plot with high resolution"""
    filepath = os.path.join(plots_dir, filename)
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
    print(f"Saved: {filepath}")

# 1. Monthly Total Spend Trend
plt.figure(figsize=(12, 8))
plt.plot(monthly_spend['month'], monthly_spend['total_spend'], marker='o', linewidth=3, markersize=8)
plt.title('Monthly Total Spend Trend', fontsize=16, fontweight='bold')
plt.xlabel('Month', fontsize=12)
plt.ylabel('Total Spend ($)', fontsize=12)
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
save_plot(plt.gcf(), '01_monthly_total_spend_trend.png')
plt.close()

# 2. Monthly Average Spend Trend
plt.figure(figsize=(12, 8))
plt.plot(monthly_spend['month'], monthly_spend['avg_spend'], marker='s', linewidth=3, markersize=8, color='orange')
plt.title('Monthly Average Spend per Record', fontsize=16, fontweight='bold')
plt.xlabel('Month', fontsize=12)
plt.ylabel('Average Spend ($)', fontsize=12)
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
save_plot(plt.gcf(), '02_monthly_average_spend_trend.png')
plt.close()

# 3. Monthly Record Count
plt.figure(figsize=(12, 8))
plt.bar(monthly_spend['month'], monthly_spend['record_count'], color='lightblue', alpha=0.7)
plt.title('Number of Records per Month', fontsize=16, fontweight='bold')
plt.xlabel('Month', fontsize=12)
plt.ylabel('Number of Records', fontsize=12)
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
save_plot(plt.gcf(), '03_monthly_record_count.png')
plt.close()

# 4. Box Plot of Spend by Month
plt.figure(figsize=(14, 8))
df_box = df.copy()
df_box['month_str'] = df_box['month'].dt.strftime('%Y-%m')
sns.boxplot(data=df_box, x='month_str', y='spend')
plt.title('Spend Distribution by Month (Box Plot)', fontsize=16, fontweight='bold')
plt.xlabel('Month', fontsize=12)
plt.ylabel('Spend ($)', fontsize=12)
plt.xticks(rotation=45)
save_plot(plt.gcf(), '04_spend_distribution_boxplot.png')
plt.close()

# 5. Violin Plot of Spend by Month
plt.figure(figsize=(14, 8))
sns.violinplot(data=df_box, x='month_str', y='spend')
plt.title('Spend Distribution by Month (Violin Plot)', fontsize=16, fontweight='bold')
plt.xlabel('Month', fontsize=12)
plt.ylabel('Spend ($)', fontsize=12)
plt.xticks(rotation=45)
save_plot(plt.gcf(), '05_spend_distribution_violin.png')
plt.close()

# 6. Histogram of All Spend Values
plt.figure(figsize=(12, 8))
plt.hist(df['spend'], bins=50, alpha=0.7, color='green', edgecolor='black')
plt.title('Distribution of All Spend Values', fontsize=16, fontweight='bold')
plt.xlabel('Spend ($)', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.yscale('log')  # Log scale to see the distribution better
save_plot(plt.gcf(), '06_spend_distribution_histogram.png')
plt.close()

# 7. Monthly Min/Max/Avg Comparison
plt.figure(figsize=(12, 8))
x_pos = range(len(monthly_spend))
plt.plot(x_pos, monthly_spend['max_spend'], marker='^', label='Max', linewidth=2, markersize=6)
plt.plot(x_pos, monthly_spend['avg_spend'], marker='o', label='Average', linewidth=2, markersize=6)
plt.plot(x_pos, monthly_spend['min_spend'], marker='v', label='Min', linewidth=2, markersize=6)
plt.title('Monthly Min/Average/Max Spend Comparison', fontsize=16, fontweight='bold')
plt.xlabel('Month Index', fontsize=12)
plt.ylabel('Spend ($)', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
save_plot(plt.gcf(), '07_monthly_min_avg_max_comparison.png')
plt.close()

# 8. Heatmap of Spend by Month and Service
plt.figure(figsize=(16, 10))
service_month_spend = df.groupby(['serviceName', 'month'])['spend'].sum().unstack(fill_value=0)
# Take top 10 services by total spend
top_services = df.groupby('serviceName')['spend'].sum().nlargest(10).index
service_month_spend_top = service_month_spend.loc[top_services]
sns.heatmap(service_month_spend_top, cmap='YlOrRd', cbar_kws={'label': 'Total Spend ($)'})
plt.title('Top 10 Services: Monthly Spend Heatmap', fontsize=16, fontweight='bold')
plt.xlabel('Month', fontsize=12)
plt.ylabel('Service Name', fontsize=12)
plt.xticks(rotation=45)
save_plot(plt.gcf(), '08_services_monthly_heatmap.png')
plt.close()

# 9. Cumulative Spend Over Time
plt.figure(figsize=(12, 8))
monthly_spend['cumulative_spend'] = monthly_spend['total_spend'].cumsum()
plt.plot(monthly_spend['month'], monthly_spend['cumulative_spend'], marker='o', linewidth=3, markersize=8, color='purple')
plt.title('Cumulative Spend Over Time', fontsize=16, fontweight='bold')
plt.xlabel('Month', fontsize=12)
plt.ylabel('Cumulative Spend ($)', fontsize=12)
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
save_plot(plt.gcf(), '09_cumulative_spend_over_time.png')
plt.close()

# 10. Spend Distribution Percentiles
plt.figure(figsize=(12, 8))
percentiles = [10, 25, 50, 75, 90, 95, 99]
percentile_values = [np.percentile(df['spend'], p) for p in percentiles]
plt.bar(range(len(percentiles)), percentile_values, color='coral', alpha=0.7)
plt.title('Spend Distribution Percentiles', fontsize=16, fontweight='bold')
plt.xlabel('Percentile', fontsize=12)
plt.ylabel('Spend ($)', fontsize=12)
plt.xticks(range(len(percentiles)), [f'{p}%' for p in percentiles])
save_plot(plt.gcf(), '10_spend_distribution_percentiles.png')
plt.close()

# 11. Monthly Spend Growth Rate
plt.figure(figsize=(12, 8))
monthly_spend['growth_rate'] = monthly_spend['total_spend'].pct_change() * 100
plt.bar(range(1, len(monthly_spend)), monthly_spend['growth_rate'].iloc[1:], color='lightgreen', alpha=0.7)
plt.title('Monthly Spend Growth Rate (%)', fontsize=16, fontweight='bold')
plt.xlabel('Month Index', fontsize=12)
plt.ylabel('Growth Rate (%)', fontsize=12)
plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
plt.grid(True, alpha=0.3)
save_plot(plt.gcf(), '11_monthly_spend_growth_rate.png')
plt.close()

# 12. Spend vs Record Count Scatter
plt.figure(figsize=(12, 8))
scatter = plt.scatter(monthly_spend['record_count'], monthly_spend['total_spend'], s=100, alpha=0.7, c=range(len(monthly_spend)), cmap='viridis')
plt.title('Total Spend vs Record Count', fontsize=16, fontweight='bold')
plt.xlabel('Number of Records', fontsize=12)
plt.ylabel('Total Spend ($)', fontsize=12)
plt.colorbar(scatter, label='Month Index')
save_plot(plt.gcf(), '12_spend_vs_record_count_scatter.png')
plt.close()

# Additional detailed analysis
print("\n" + "="*80)
print("DETAILED SPEND ANALYSIS")
print("="*80)

# Summary statistics
print(f"\nOverall Statistics:")
print(f"Total Records: {len(df):,}")
print(f"Total Spend: ${df['spend'].sum():,.2f}")
print(f"Average Spend per Record: ${df['spend'].mean():.2f}")
print(f"Median Spend per Record: ${df['spend'].median():.2f}")
print(f"Standard Deviation: ${df['spend'].std():.2f}")

# Zero spend analysis
zero_spend_count = (df['spend'] == 0).sum()
zero_spend_pct = (zero_spend_count / len(df)) * 100
print(f"\nZero Spend Analysis:")
print(f"Records with $0 spend: {zero_spend_count:,} ({zero_spend_pct:.1f}%)")

# High spend analysis
high_spend_threshold = df['spend'].quantile(0.95)
high_spend_count = (df['spend'] >= high_spend_threshold).sum()
print(f"\nHigh Spend Analysis (Top 5%):")
print(f"Threshold: ${high_spend_threshold:.2f}")
print(f"Records above threshold: {high_spend_count:,}")

# Monthly statistics
print(f"\nMonthly Statistics:")
for _, row in monthly_spend.iterrows():
    month_str = row['month'].strftime('%Y-%m')
    print(f"{month_str}: {row['record_count']:3.0f} records, "
          f"Total: ${row['total_spend']:8,.2f}, "
          f"Avg: ${row['avg_spend']:6.2f}, "
          f"Max: ${row['max_spend']:7.2f}")

# Create additional plots for deeper insights

# 1. Spend distribution by service (top 15)
plt.figure(figsize=(14, 10))
top_services_spend = df.groupby('serviceName')['spend'].sum().sort_values(ascending=False).head(15)
plt.barh(range(len(top_services_spend)), top_services_spend.values)
plt.yticks(range(len(top_services_spend)), top_services_spend.index, fontsize=10)
plt.title('Top 15 Services by Total Spend', fontsize=16, fontweight='bold')
plt.xlabel('Total Spend ($)', fontsize=12)
save_plot(plt.gcf(), '13_top_15_services_by_spend.png')
plt.close()

# 2. Monthly spend breakdown by service category
plt.figure(figsize=(16, 10))
service_categories = df.groupby(['month', 'serviceName'])['spend'].sum().unstack(fill_value=0)
top_5_services = df.groupby('serviceName')['spend'].sum().nlargest(5).index
service_categories_top5 = service_categories[top_5_services]
service_categories_top5.plot(kind='area', stacked=True, alpha=0.7)
plt.title('Monthly Spend by Top 5 Services (Stacked)', fontsize=16, fontweight='bold')
plt.xlabel('Month', fontsize=12)
plt.ylabel('Spend ($)', fontsize=12)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.xticks(rotation=45)
save_plot(plt.gcf(), '14_monthly_spend_by_top_5_services.png')
plt.close()

# 3. Spend distribution by account
plt.figure(figsize=(14, 8))
top_accounts_spend = df.groupby('accountName')['spend'].sum().sort_values(ascending=False).head(10)
plt.bar(range(len(top_accounts_spend)), top_accounts_spend.values, color='lightcoral')
plt.title('Top 10 Accounts by Total Spend', fontsize=16, fontweight='bold')
plt.xlabel('Account', fontsize=12)
plt.ylabel('Total Spend ($)', fontsize=12)
plt.xticks(range(len(top_accounts_spend)), [acc[:20] + '...' if len(acc) > 20 else acc for acc in top_accounts_spend.index], rotation=45, ha='right')
save_plot(plt.gcf(), '15_top_10_accounts_by_spend.png')
plt.close()

# 4. Spend trend with confidence intervals
plt.figure(figsize=(12, 8))
monthly_stats = df.groupby('month')['spend'].agg(['mean', 'std', 'count']).reset_index()
monthly_stats['se'] = monthly_stats['std'] / np.sqrt(monthly_stats['count'])
monthly_stats['ci_95'] = 1.96 * monthly_stats['se']

plt.fill_between(monthly_stats['month'], 
                 monthly_stats['mean'] - monthly_stats['ci_95'],
                 monthly_stats['mean'] + monthly_stats['ci_95'], 
                 alpha=0.3, label='95% Confidence Interval')
plt.plot(monthly_stats['month'], monthly_stats['mean'], marker='o', linewidth=2, label='Mean Spend')
plt.title('Monthly Average Spend with 95% Confidence Intervals', fontsize=16, fontweight='bold')
plt.xlabel('Month', fontsize=12)
plt.ylabel('Average Spend ($)', fontsize=12)
plt.legend()
plt.xticks(rotation=45)
save_plot(plt.gcf(), '16_monthly_average_spend_with_confidence_intervals.png')
plt.close()

# 5. Spend distribution by usage family
plt.figure(figsize=(14, 8))
usage_family_spend = df.groupby('usageFamily')['spend'].sum().sort_values(ascending=False)
plt.bar(range(len(usage_family_spend)), usage_family_spend.values, color='skyblue')
plt.title('Total Spend by Usage Family', fontsize=16, fontweight='bold')
plt.xlabel('Usage Family', fontsize=12)
plt.ylabel('Total Spend ($)', fontsize=12)
plt.xticks(range(len(usage_family_spend)), usage_family_spend.index, rotation=45, ha='right')
save_plot(plt.gcf(), '17_spend_by_usage_family.png')
plt.close()

# 6. Monthly spend trend by region
plt.figure(figsize=(14, 8))
region_monthly_spend = df.groupby(['month', 'region'])['spend'].sum().unstack(fill_value=0)
region_monthly_spend.plot(kind='line', marker='o', linewidth=2, markersize=6)
plt.title('Monthly Spend Trend by Region', fontsize=16, fontweight='bold')
plt.xlabel('Month', fontsize=12)
plt.ylabel('Total Spend ($)', fontsize=12)
plt.legend()
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
save_plot(plt.gcf(), '18_monthly_spend_trend_by_region.png')
plt.close()

print(f"\nAnalysis complete! Generated {len(monthly_spend)} monthly data points.")
print(f"Key insight: Spend ranges from ${min_spend:.2f} to ${max_spend:.2f} per individual record,")
print(f"with monthly averages ranging from ${monthly_spend['avg_spend'].min():.2f} to ${monthly_spend['avg_spend'].max():.2f}")
print(f"\nAll plots have been saved to: {plots_dir}/")
print(f"Total plots generated: 18")
