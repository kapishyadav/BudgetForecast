#!/usr/bin/env python3
"""
Test script to verify Plotly integration
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
import pandas as pd
import numpy as np
import os

def test_plotly_integration():
    """Test basic plotly functionality"""
    print("Testing Plotly integration...")
    
    # Create sample data
    dates = pd.date_range('2025-01-01', periods=12, freq='M')
    actual = np.random.normal(1000, 200, 12)
    predicted = actual + np.random.normal(0, 50, 12)
    
    # Create a simple line plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, 
        y=actual, 
        mode='lines+markers', 
        name='Actual',
        line=dict(color='blue', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=dates, 
        y=predicted, 
        mode='lines+markers', 
        name='Predicted',
        line=dict(color='red', width=2)
    ))
    
    fig.update_layout(
        title="Test Plotly Integration",
        xaxis_title="Date",
        yaxis_title="Value",
        template='plotly_white',
        hovermode='x unified'
    )
    
    # Create plots directory if it doesn't exist
    plots_dir = 'plots'
    os.makedirs(plots_dir, exist_ok=True)
    
    # Save the plot
    output_file = os.path.join(plots_dir, 'test_plotly.html')
    pyo.plot(fig, filename=output_file)
    
    print(f"✅ Plotly test successful! Plot saved to: {output_file}")
    print("Open the HTML file in your browser to view the interactive plot.")
    
    return True

if __name__ == "__main__":
    test_plotly_integration() 