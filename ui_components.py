import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
from collections import deque

class ProbeUI:
    def __init__(self):
        self.probe_units = {
            'pH': 'pH',
            'EC': 'µS/cm',
            'DO': 'mg/L',
            'RTD': '°C'
        }
        
        self.probe_ranges = {
            'pH': (0, 14),
            'EC': (0, 200000),
            'DO': (0, 20),
            'RTD': (-200, 850)
        }
        
        self.probe_colors = {
            'pH': {
                'good': '#28a745',
                'warning': '#ffc107',
                'error': '#dc3545'
            },
            'EC': {
                'good': '#17a2b8',
                'warning': '#6c757d',
                'error': '#dc3545'
            },
            'DO': {
                'good': '#28a745',
                'warning': '#ffc107',
                'error': '#dc3545'
            },
            'RTD': {
                'good': '#17a2b8',
                'warning': '#ffc107',
                'error': '#dc3545'
            }
        }

    def create_styles(self):
        """Create custom CSS styles"""
        st.markdown("""
            <style>
            .probe-card {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                position: relative;
            }
            .reading-value {
                font-size: 36px;
                font-weight: bold;
                margin: 10px 0;
            }
            .reading-unit {
                font-size: 18px;
                color: #666;
            }
            .status-indicator {
                width: 15px;
                height: 15px;
                border-radius: 50%;
                display: inline-block;
                margin-right: 10px;
            }
            .calibration-status {
                font-size: 14px;
                margin-top: 10px;
            }
            </style>
        """, unsafe_allow_html=True)

    def get_reading_color(self, probe_type, value):
        """Determine color based on reading value"""
        if value == 0.000:
            return self.probe_colors[probe_type]['error']
            
        min_val, max_val = self.probe_ranges[probe_type]
        if min_val <= value <= max_val:
            if probe_type == 'pH':
                if 6.5 <= value <= 7.5:
                    return self.probe_colors[probe_type]['good']
                elif 5.5 <= value <= 8.5:
                    return self.probe_colors[probe_type]['warning']
                else:
                    return self.probe_colors[probe_type]['error']
            else:
                return self.probe_colors[probe_type]['good']
        return self.probe_colors[probe_type]['error']

    def create_probe_card(self, probe_type, value, last_calibration=None):
        """Create a card showing probe reading with colored status indicator"""
        color = self.get_reading_color(probe_type, value)
        
        html = f"""
            <div class="probe-card">
                <div style="display: flex; align-items: center;">
                    <div class="status-indicator" style="background-color: {color};"></div>
                    <h3>{probe_type} Probe</h3>
                </div>
                <div class="reading-value" style="color: {color};">
                    {value:.3f}
                    <span class="reading-unit">{self.probe_units[probe_type]}</span>
                </div>
                """
        
        if last_calibration:
            html += f"""
                <div class="calibration-status">
                    Last calibrated: {last_calibration}
                </div>
                """
                
        html += "</div>"
        
        st.markdown(html, unsafe_allow_html=True)

    def create_calibration_ui(self, probe_type):
        """Create calibration interface for specified probe"""
        st.subheader(f"{probe_type} Probe Calibration")
        
        if probe_type == "pH":
            col1, col2, col3 = st.columns(3)
            
            with col1:
                mid_cal = st.button("Calibrate pH 7 (Mid)")
                if mid_cal:
                    return ("mid", 7.0)
                    
            with col2:
                low_cal = st.button("Calibrate pH 4 (Low)")
                if low_cal:
                    return ("low", 4.0)
                    
            with col3:
                high_cal = st.button("Calibrate pH 10 (High)")
                if high_cal:
                    return ("high", 10.0)
                    
        elif probe_type == "EC":
            col1, col2 = st.columns(2)
            
            with col1:
                dry_cal = st.button("Dry Calibration")
                if dry_cal:
                    return ("dry", 0)
                    
            with col2:
                value = st.number_input("Solution Value (µS/cm)", 
                                      min_value=0, 
                                      max_value=200000,
                                      value=12880)
                if st.button("Calibrate"):
                    return ("point", value)
                    
        elif probe_type == "DO":
            col1, col2 = st.columns(2)
            
            with col1:
                atm_cal = st.button("Atmospheric Calibration")
                if atm_cal:
                    return ("atm", 0)
                    
            with col2:
                zero_cal = st.button("Zero Solution Calibration")
                if zero_cal:
                    return ("zero", 0)
                    
        elif probe_type == "RTD":
            value = st.number_input("Temperature (°C)", 
                                  min_value=-200.0,
                                  max_value=850.0,
                                  value=25.0)
            if st.button("Calibrate"):
                return ("point", value)
                
        return None

    def create_data_view(self, readings, probe_type):
        """Create data view with graph and statistics"""
        if not readings[probe_type]:
            st.info(f"No data recorded for {probe_type} probe")
            return
            
        # Create graph
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(readings['timestamps']),
            y=list(readings[probe_type]),
            mode='lines+markers',
            name=probe_type
        ))
        
        fig.update_layout(
            title=f"{probe_type} Readings Over Time",
            xaxis_title="Time",
            yaxis_title=self.probe_units[probe_type],
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Calculate statistics
        values = list(readings[probe_type])
        stats = {
            'Minimum': min(values),
            'Maximum': max(values),
            'Average': sum(values) / len(values),
            'Current': values[-1]
        }
        
        # Display statistics
        cols = st.columns(len(stats))
        for col, (label, value) in zip(cols, stats.items()):
            col.metric(label, f"{value:.3f} {self.probe_units[probe_type]}")
