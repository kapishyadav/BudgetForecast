# Migration from Matplotlib to Plotly

## Overview
This document describes the migration from static matplotlib plots to interactive plotly visualizations in the Budget Forecasting project.

## Changes Made

### 1. Import Changes
- **Removed**: `import matplotlib.pyplot as plt`
- **Added**: 
  ```python
  import plotly.graph_objects as go
  import plotly.express as px
  from plotly.subplots import make_subplots
  import plotly.offline as pyo
  ```

### 2. Visualization Enhancements

#### Interactive Features Added:
- **Hover Information**: Detailed tooltips showing exact values when hovering over data points
- **Zoom & Pan**: Users can zoom in/out and pan across the charts
- **Legend Interaction**: Click legend items to show/hide specific data series
- **Export Options**: Right-click to save charts as PNG, SVG, or other formats
- **Responsive Design**: Charts automatically adjust to different screen sizes

#### Chart Types Migrated:
1. **Monthly Comparison Bar Charts**
   - Enhanced with grouped bars for model comparison
   - Interactive hover tooltips with formatted currency values
   - Unified hover mode for better data exploration

2. **Monthly Comparison Line Charts**
   - Smooth line transitions with markers
   - Multiple y-axis support for different scales
   - Enhanced legend with color coding

3. **Future Predictions Dashboard**
   - Subplot layout with line and bar charts
   - Comprehensive 24-month forecasting visualization
   - Model comparison with side-by-side analysis

### 3. File Organization
- **Plots Directory**: All HTML files are saved in the `plots/` directory
- **File Naming**: 
  - `monthly_comparison_bar.html`
  - `monthly_comparison_line.html`
  - `future_predictions.html`

### 4. Dependencies
Added to `requirements.txt`:
```
plotly>=5.15.0
```

## Usage

### Running the Main Script
```bash
# Install dependencies
pip install -r requirements.txt

# Run with plotly visualizations
python src/main.py --train true --optimizer bayesian --model catboost
```

### Viewing Interactive Plots
1. Run the main script
2. Open the generated HTML files in any web browser
3. Interact with the charts using:
   - Mouse hover for detailed information
   - Scroll wheel to zoom
   - Click and drag to pan
   - Legend clicks to toggle series visibility

### Testing Plotly Integration
```bash
python test_plotly.py
```

## Benefits of Plotly Migration

### 1. Enhanced User Experience
- **Interactivity**: Users can explore data dynamically
- **Professional Appearance**: Modern, clean design with white template
- **Accessibility**: Better for presentations and reports

### 2. Advanced Features
- **Data Export**: Easy export of chart data
- **Responsive**: Works on desktop and mobile devices
- **Customizable**: Extensive styling and layout options

### 3. Better Data Exploration
- **Hover Details**: Precise values without cluttering the chart
- **Zoom Capabilities**: Focus on specific time periods
- **Multi-axis Support**: Compare different scales effectively

## Technical Implementation

### Chart Configuration
```python
fig.update_layout(
    title="Chart Title",
    xaxis_title="X Axis",
    yaxis_title="Y Axis",
    hovermode='x unified',  # Enhanced hover behavior
    template='plotly_white'  # Clean, professional appearance
)
```

### Hover Templates
```python
hovertemplate='<b>Month:</b> %{x}<br><b>Value:</b> $%{y:,.2f}<extra></extra>'
```

### Subplot Creation
```python
fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=("Title 1", "Title 2"),
    vertical_spacing=0.1
)
```

## Future Enhancements

### Potential Additions:
1. **Dashboard Integration**: Combine multiple charts in a single dashboard
2. **Real-time Updates**: Dynamic data refresh capabilities
3. **Advanced Interactivity**: Range sliders, date pickers
4. **Export Functionality**: PDF reports with embedded charts
5. **Web Application**: Deploy as a web-based dashboard

### Performance Considerations:
- Large datasets may require data sampling for optimal performance
- Consider using plotly's `FigureWidget` for Jupyter notebook integration
- Implement lazy loading for multiple chart generation

## Troubleshooting

### Common Issues:
1. **Missing Dependencies**: Ensure plotly is installed via `pip install plotly`
2. **Browser Compatibility**: Use modern browsers for best experience
3. **File Permissions**: Ensure write access to the plots directory

### Debug Mode:
```python
# Enable plotly debug mode
import plotly.io as pio
pio.renderers.default = "browser"
```

## Conclusion
The migration to plotly significantly enhances the user experience by providing interactive, professional-quality visualizations that are more engaging and informative than static matplotlib plots. The new charts maintain all the analytical capabilities while adding modern web-based interactivity. 