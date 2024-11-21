import streamlit as st
import serial
import serial.tools.list_ports
import time
import threading
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from collections import deque

class EZOHandler:
    def __init__(self):
        self.probe_configs = {
            'pH': {
                'name': 'pH',
                'unit': 'pH',
                'range': (0, 14),
                'colors': {
                    'good': '#28a745',
                    'warning': '#ffc107',
                    'error': '#dc3545'
                },
                'thresholds': {
                    'good': (6.5, 7.5),
                    'warning': (5.5, 8.5)
                }
            },
            'EC': {
                'name': 'Conductivity',
                'unit': 'µS/cm',
                'range': (0, 200000),
                'colors': {
                    'good': '#17a2b8',
                    'warning': '#6c757d',
                    'error': '#dc3545'
                }
            },
            'DO': {
                'name': 'Dissolved Oxygen',
                'unit': 'mg/L',
                'range': (0, 20),
                'colors': {
                    'good': '#28a745',
                    'warning': '#ffc107',
                    'error': '#dc3545'
                }
            },
            'RTD': {
                'name': 'Temperature',
                'unit': '°C',
                'range': (-200, 850),
                'colors': {
                    'good': '#17a2b8',
                    'warning': '#ffc107',
                    'error': '#dc3545'
                }
            }
        }

    def get_available_ports(self):
        """List all available COM ports"""
        ports = []
        try:
            port_list = list(serial.tools.list_ports.comports())
            for port in port_list:
                ports.append({
                    'port': port.device,
                    'description': port.description,
                    'hwid': port.hwid
                })
        except Exception as e:
            st.error(f"Error detecting ports: {str(e)}")
        return ports

    def connect_to_port(self, port):
        """Connect to specified port with EZO configuration"""
        try:
            # Format Windows ports
            if port.startswith('COM'):
                port = f'\\\\.\{port}'

            ser = serial.Serial(
                port=port,
                baudrate=9600,
                timeout=1,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            time.sleep(2)  # Wait for connection to stabilize
            
            # Test connection
            ser.write(b"i\r")
            time.sleep(0.5)
            
            if ser.in_waiting:
                response = ser.readline().decode().strip()
                return ser, response
            
            ser.close()
            return None, "No response from device"
            
        except Exception as e:
            return None, str(e)

    def send_command(self, ser, command):
        """Send command to EZO device and get response"""
        try:
            ser.write(f"{command}\r".encode())
            time.sleep(0.5)
            
            response = []
            while ser.in_waiting:
                line = ser.readline().decode().strip()
                response.append(line)
            
            return response[0] if response else None
        except Exception as e:
            st.error(f"Command error: {str(e)}")
            return None

    def get_reading(self, ser):
        """Get current reading from probe"""
        response = self.send_command(ser, "R")
        try:
            if response and response.replace('.','').replace('-','').isdigit():
                return float(response)
        except:
            pass
        return 0.000

class EZOUI:
    def __init__(self, handler):
        self.handler = handler
        self.setup_styles()

    def setup_styles(self):
        """Set up custom CSS styles"""
        st.markdown("""
            <style>
            .reading-card {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .reading-value {
                font-size: 36px;
                font-weight: bold;
                text-align: center;
            }
            .reading-unit {
                font-size: 16px;
                color: #666;
            }
            .status-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                display: inline-block;
                margin-right: 10px;
            }
            .probe-title {
                font-size: 20px;
                font-weight: 500;
                margin-bottom: 10px;
            }
            </style>
        """, unsafe_allow_html=True)

    def create_probe_card(self, probe_type, value):
        """Create a card with probe reading and status indicator"""
        config = self.handler.probe_configs[probe_type]
        
        # Determine color based on value
        color = config['colors']['error']
        if value > 0:
            min_val, max_val = config['range']
            if min_val <= value <= max_val:
                if probe_type == 'pH' and 'thresholds' in config:
                    good_min, good_max = config['thresholds']['good']
                    warn_min, warn_max = config['thresholds']['warning']
                    if good_min <= value <= good_max:
                        color = config['colors']['good']
                    elif warn_min <= value <= warn_max:
                        color = config['colors']['warning']
                else:
                    color = config['colors']['good']
        
        html = f"""
            <div class="reading-card">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div class="status-indicator" style="background-color: {color};"></div>
                    <div class="probe-title">{config['name']} Reading</div>
                </div>
                <div class="reading-value" style="color: {color};">
                    {value:.3f}
                    <span class="reading-unit">{config['unit']}</span>
                </div>
            </div>
        """
        
        st.markdown(html, unsafe_allow_html=True)

    def create_calibration_ui(self, probe_type, ser):
        """Create calibration interface for probe"""
        st.subheader(f"{probe_type} Calibration")
        
        # Show current reading during calibration
        current_value = self.handler.get_reading(ser)
        self.create_probe_card(probe_type, current_value)
        
        if probe_type == "pH":
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Calibrate pH 7 (Mid)"):
                    response = self.handler.send_command(ser, "Cal,mid,7")
                    st.success(f"Calibration response: {response}")
            with col2:
                if st.button("Calibrate pH 4 (Low)"):
                    response = self.handler.send_command(ser, "Cal,low,4")
                    st.success(f"Calibration response: {response}")
            with col3:
                if st.button("Calibrate pH 10 (High)"):
                    response = self.handler.send_command(ser, "Cal,high,10")
                    st.success(f"Calibration response: {response}")
        
        elif probe_type == "EC":
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Dry Calibration"):
                    response = self.handler.send_command(ser, "Cal,dry")
                    st.success(f"Calibration response: {response}")
            with col2:
                value = st.number_input("Solution Value (µS/cm)", 
                                      min_value=0, 
                                      max_value=200000,
                                      value=12880)
                if st.button("Calibrate"):
                    response = self.handler.send_command(ser, f"Cal,{value}")
                    st.success(f"Calibration response: {response}")
        
        elif probe_type == "DO":
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Atmospheric Calibration"):
                    response = self.handler.send_command(ser, "Cal")
                    st.success(f"Calibration response: {response}")
            with col2:
                if st.button("Zero Solution Calibration"):
                    response = self.handler.send_command(ser, "Cal,0")
                    st.success(f"Calibration response: {response}")
        
        elif probe_type == "RTD":
            value = st.number_input("Known Temperature (°C)", 
                                  min_value=-200.0, 
                                  max_value=850.0,
                                  value=25.0)
            if st.button("Calibrate"):
                response = self.handler.send_command(ser, f"Cal,{value}")
                st.success(f"Calibration response: {response}")
