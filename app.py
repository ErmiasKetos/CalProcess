import streamlit as st
import serial
import time
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import json

# Initialize session state for historical data
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = []

class AquaponicsMonitor:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        try:
            self.ser = serial.Serial(port, baudrate)
            time.sleep(2)  # Allow time for serial connection
        except Exception as e:
            st.error(f"Error connecting to serial port: {e}")
            self.ser = None
        
        self.latest_readings = {
            'ph': 0.0,
            'do': 0.0,
            'temp': 0.0,
            'ec': 0.0
        }

    def send_command(self, command):
        if self.ser:
            try:
                self.ser.write(f"{command}\r".encode())
                time.sleep(1)  # Wait for response
                response = self.ser.readline().decode().strip()
                return response
            except Exception as e:
                st.error(f"Error sending command: {e}")
                return None
        return None

    def calibrate_sensor(self, sensor, cal_type):
        command_map = {
            'ph': {
                'mid': 'ph:cal,mid,7',
                'low': 'ph:cal,low,4',
                'high': 'ph:cal,high,10',
                'clear': 'ph:cal,clear'
            },
            'do': {
                'air': 'do:cal',
                'zero': 'do:cal,0',
                'clear': 'do:cal,clear'
            },
            'temp': {
                'custom': lambda t: f'rtd:cal,{t}',
                'clear': 'rtd:cal,clear'
            },
            'ec': {
                'dry': 'ec:cal,dry',
                'low': lambda k: f'ec:cal,low,{self.get_ec_cal_value(k, "low")}',
                'high': lambda k: f'ec:cal,high,{self.get_ec_cal_value(k, "high")}',
                'clear': 'ec:cal,clear',
                'k': lambda k: f'ec:k,{k}'
            }
        }
        
        cmd = command_map[sensor][cal_type]
        if callable(cmd):
            if sensor == 'temp':
                temp = st.number_input('Enter calibration temperature:', value=25.0)
                cmd = cmd(temp)
            elif sensor == 'ec':
                cmd = cmd(st.session_state.get('k_value', 1))
        
        response = self.send_command(cmd)
        return response

    @staticmethod
    def get_ec_cal_value(k_value, point):
        cal_values = {
            0.1: {'low': 84, 'high': 1413},
            1.0: {'low': 12880, 'high': 80000},
            10.0: {'low': 12880, 'high': 150000}
        }
        return cal_values.get(k_value, cal_values[1.0])[point]

def create_card(title, value, unit, color):
    st.markdown(
        f"""
        <div style="
            padding: 20px;
            border-radius: 10px;
            background-color: {color}22;
            border: 2px solid {color};
            margin: 10px 0;
        ">
            <h3 style="color: {color}; margin: 0;">{title}</h3>
            <h2 style="font-size: 2em; margin: 10px 0;">{value} {unit}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

def create_calibration_section(monitor, sensor):
    st.subheader(f"{sensor} Calibration")
    
    if sensor == "pH":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Calibrate pH 7 (Mid)"):
                monitor.calibrate_sensor('ph', 'mid')
        with col2:
            if st.button("Calibrate pH 4 (Low)"):
                monitor.calibrate_sensor('ph', 'low')
        with col3:
            if st.button("Calibrate pH 10 (High)"):
                monitor.calibrate_sensor('ph', 'high')
        with col4:
            if st.button("Clear pH Cal"):
                monitor.calibrate_sensor('ph', 'clear')
    
    elif sensor == "DO":
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Calibrate to Air"):
                monitor.calibrate_sensor('do', 'air')
        with col2:
            if st.button("Calibrate to 0 DO"):
                monitor.calibrate_sensor('do', 'zero')
        with col3:
            if st.button("Clear DO Cal"):
                monitor.calibrate_sensor('do', 'clear')
    
    elif sensor == "Temperature":
        col1, col2 = st.columns(2)
        with col1:
            temp = st.number_input("Calibration Temperature", value=25.0)
            if st.button("Calibrate Temperature"):
                monitor.calibrate_sensor('temp', 'custom')
        with col2:
            if st.button("Clear Temp Cal"):
                monitor.calibrate_sensor('temp', 'clear')
    
    elif sensor == "Conductivity":
        col1, col2 = st.columns(2)
        with col1:
            k_value = st.selectbox("K Value", [0.1, 1.0, 10.0], 
                                 format_func=lambda x: f"K = {x}")
            st.session_state.k_value = k_value
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Dry Calibration"):
                monitor.calibrate_sensor('ec', 'dry')
        with col2:
            if st.button("Low Point Cal"):
                monitor.calibrate_sensor('ec', 'low')
        with col3:
            if st.button("High Point Cal"):
                monitor.calibrate_sensor('ec', 'high')
        with col4:
            if st.button("Clear EC Cal"):
                monitor.calibrate_sensor('ec', 'clear')

def main():
    st.set_page_config(page_title="Aquaponics Monitor", layout="wide")
    
    st.title("🌱 Aquaponics Monitoring System")
    
    # Initialize monitor
    monitor = AquaponicsMonitor()
    
    # Main dashboard
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Readings")
        create_card("pH Level", "7.2", "pH", "#FF4B4B")
        create_card("Dissolved Oxygen", "6.5", "mg/L", "#1E88E5")
        create_card("Temperature", "25.3", "°C", "#FFA726")
        create_card("Conductivity", "850", "µS/cm", "#4CAF50")
    
    with col2:
        st.subheader("Real-time Graph")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add traces for each sensor
        times = [datetime.now().strftime("%H:%M:%S")] * 10
        fig.add_trace(
            go.Scatter(x=times, y=[7.2]*10, name="pH", line=dict(color="#FF4B4B")),
            secondary_y=False
        )
        fig.add_trace(
            go.Scatter(x=times, y=[6.5]*10, name="DO", line=dict(color="#1E88E5")),
            secondary_y=True
        )
        
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Calibration sections
    st.markdown("---")
    st.subheader("📊 Sensor Calibration")
    
    tab1, tab2, tab3, tab4 = st.tabs(["pH", "DO", "Temperature", "Conductivity"])
    
    with tab1:
        create_calibration_section(monitor, "pH")
    with tab2:
        create_calibration_section(monitor, "DO")
    with tab3:
        create_calibration_section(monitor, "Temperature")
    with tab4:
        create_calibration_section(monitor, "Conductivity")

if __name__ == "__main__":
    main()
