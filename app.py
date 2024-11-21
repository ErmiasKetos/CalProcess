import streamlit as st
import serial
import time
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import json
from pathlib import Path
from styles import AppStyle, apply_plot_style, init_styling

def main():
    init_styling()

class WhiteboxEZOApp:
    DEFAULT_ADDRESSES = {
        'pH': 99,
        'EC': 100,
        'DO': 97,
        'RTD': 102,
        'ORP': 98,
        'HUM': 111
    }

    def __init__(self):
        self.serial_conn = None
        self.current_device = None
        self.init_session_state()

    def init_session_state(self):
        if 'connected' not in st.session_state:
            st.session_state.connected = False
        if 'readings' not in st.session_state:
            st.session_state.readings = []
        if 'calibration_log' not in st.session_state:
            st.session_state.calibration_log = []
            
    def send_command(self, command):
        """Send command to EZO device through Whitebox"""
        if not self.serial_conn:
            return None
            
        try:
            # Add carriage return to command
            command = f"{command}\r"
            self.serial_conn.write(command.encode())
            time.sleep(0.3)  # Wait for processing
            
            # Read response
            if self.serial_conn.in_waiting:
                response = self.serial_conn.readline().decode().strip()
                return response
        except Exception as e:
            st.error(f"Command error: {str(e)}")
        return None

    def scan_devices(self):
        """Scan for connected EZO devices"""
        response = self.send_command("!scan")
        devices = []
        if response:
            lines = response.split('\n')
            for line in lines:
                if ':' in line:
                    addr, device_info = line.split(':', 1)
                    addr = int(addr.strip())
                    device_type = device_info.strip().split()[1]
                    devices.append({
                        'address': addr,
                        'type': device_type,
                        'info': device_info.strip()
                    })
        return devices

    def select_device(self, address):
        """Select EZO device by address"""
        response = self.send_command(str(address))
        if response and "SUCCESS" in response:
            return True
        return False

    def setup_ui(self):
        st.set_page_config(page_title="Whitebox EZO Calibration", layout="wide")
        st.title("🧪 Whitebox EZO Calibration Hub")

        # Connection panel
        with st.sidebar:
            self.render_connection_panel()

        if not st.session_state.connected:
            st.info("Please connect to your Whitebox device using the sidebar")
            return

        # Main content
        tab1, tab2, tab3 = st.tabs(["📊 Monitoring", "🔧 Calibration", "📝 History"])
        
        with tab1:
            self.render_monitoring_tab()
        with tab2:
            self.render_calibration_tab()
        with tab3:
            self.render_history_tab()

    def render_connection_panel(self):
        st.sidebar.header("Connection Settings")
        port = st.sidebar.text_input("Serial Port", "/dev/ttyUSB0")
        
        if not st.session_state.connected:
            if st.sidebar.button("Connect"):
                try:
                    self.serial_conn = serial.Serial(port, 9600, timeout=1)
                    st.session_state.connected = True
                    st.sidebar.success("Connected!")
                except Exception as e:
                    st.sidebar.error(f"Connection failed: {str(e)}")
        else:
            if st.sidebar.button("Disconnect"):
                if self.serial_conn:
                    self.serial_conn.close()
                st.session_state.connected = False
                self.serial_conn = None
                st.sidebar.info("Disconnected")

        # Device scanning
        if st.session_state.connected:
            if st.sidebar.button("Scan Devices"):
                devices = self.scan_devices()
                st.session_state.devices = devices
                for device in devices:
                    st.sidebar.text(f"{device['type']} at {device['address']}")

    def render_monitoring_tab(self):
        st.header("Real-time Monitoring")
        
        if 'devices' not in st.session_state:
            st.warning("Please scan for devices first")
            return

        # Device selection
        selected_device = st.selectbox(
            "Select Device",
            st.session_state.devices,
            format_func=lambda x: f"{x['type']} ({x['address']})"
        )

        if selected_device:
            self.current_device = selected_device
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Temperature compensation
                temp = st.number_input(
                    "Temperature Compensation (°C)",
                    value=25.0,
                    min_value=0.0,
                    max_value=100.0
                )
                if st.button("Set Temperature"):
                    self.send_command(f"T,{temp}")

            with col2:
                # Manual reading
                if st.button("Take Reading"):
                    if self.select_device(selected_device['address']):
                        response = self.send_command("R")
                        if response:
                            st.metric("Current Reading", response)
                            self.log_reading(selected_device['type'], response)

            # Continuous reading option
            if st.checkbox("Enable Continuous Reading"):
                placeholder = st.empty()
                while True:
                    if self.select_device(selected_device['address']):
                        response = self.send_command("R")
                        if response:
                            placeholder.metric("Current Reading", response)
                            self.log_reading(selected_device['type'], response)
                    time.sleep(1)
                    if not st.checkbox("Enable Continuous Reading"):
                        break

    def render_calibration_tab(self):
        if not self.current_device:
            st.warning("Please select a device first")
            return

        st.header(f"Calibration - {self.current_device['type']}")

        if self.current_device['type'] == 'pH':
            self.render_ph_calibration()
        elif self.current_device['type'] == 'EC':
            self.render_ec_calibration()
        elif self.current_device['type'] == 'DO':
            self.render_do_calibration()
        elif self.current_device['type'] == 'RTD':
            self.render_rtd_calibration()

    def render_ph_calibration(self):
        st.subheader("pH Probe Calibration")
        
        # pH Slope check
        if st.button("Check Calibration Status"):
            response = self.send_command("Slope,?")
            if response:
                st.info(f"Slope status: {response}")

        # Calibration points
        cal_points = [
            ("Mid (pH 7.0)", "Cal,mid,7.00"),
            ("Low (pH 4.0)", "Cal,low,4.00"),
            ("High (pH 10.0)", "Cal,high,10.00")
        ]

        for point_name, command in cal_points:
            with st.expander(point_name):
                self.calibration_step(point_name, command)

        if st.button("Clear Calibration"):
            response = self.send_command("Cal,clear")
            if response:
                st.success("Calibration cleared")

    def render_ec_calibration(self):
        st.subheader("EC Probe Calibration")
        
        # K-value selection
        k_value = st.selectbox("Select K-value", ["0.1", "1.0", "10.0"])
        if st.button("Set K-value"):
            response = self.send_command(f"K,{k_value}")
            if response:
                st.success(f"K-value set to {k_value}")

        # Calibration points based on K-value
        if k_value == "0.1":
            cal_points = [
                ("Dry Calibration", "Cal,dry"),
                ("84 µS/cm", "Cal,84"),
                ("1413 µS/cm", "Cal,1413")
            ]
        elif k_value == "1.0":
            cal_points = [
                ("Dry Calibration", "Cal,dry"),
                ("12880 µS/cm", "Cal,12880"),
                ("80000 µS/cm", "Cal,80000")
            ]
        else:  # k_value == "10.0"
            cal_points = [
                ("Dry Calibration", "Cal,dry"),
                ("12880 µS/cm", "Cal,12880"),
                ("150000 µS/cm", "Cal,150000")
            ]

        for point_name, command in cal_points:
            with st.expander(point_name):
                self.calibration_step(point_name, command)

    def render_do_calibration(self):
        st.subheader("DO Probe Calibration")
        
        cal_points = [
            ("Atmospheric Oxygen Calibration", "Cal"),
            ("Zero DO Calibration", "Cal,0")
        ]

        for point_name, command in cal_points:
            with st.expander(point_name):
                self.calibration_step(point_name, command)

    def render_rtd_calibration(self):
        st.subheader("Temperature (RTD) Calibration")
        
        temp = st.number_input("Known Temperature (°C)", 
                             value=25.0,
                             min_value=-200.0,
                             max_value=850.0)
        
        self.calibration_step("Temperature", f"Cal,{temp}")

    def calibration_step(self, point_name, command):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Current Reading:")
            reading_placeholder = st.empty()
            
            # Stabilization period
            if st.button(f"Start Stabilization", key=f"stab_{point_name}"):
                for i in range(30):  # 30 second stabilization
                    response = self.send_command("R")
                    if response:
                        reading_placeholder.metric("Reading", response)
                    time.sleep(1)
                st.success("Stabilization complete")

        with col2:
            if st.button(f"Calibrate {point_name}", key=f"cal_{point_name}"):
                response = self.send_command(command)
                if response:
                    st.success(f"Calibration response: {response}")
                    self.log_calibration(point_name, command, response)

    def render_history_tab(self):
        st.header("Calibration History")
        
        if not st.session_state.calibration_log:
            st.info("No calibration history available")
            return

        # Display calibration history
        df = pd.DataFrame(st.session_state.calibration_log)
        st.dataframe(df)

        # Export options
        if st.button("Export History"):
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "calibration_history.csv",
                "text/csv"
            )

    def log_reading(self, device_type, value):
        st.session_state.readings.append({
            'timestamp': datetime.now().isoformat(),
            'device_type': device_type,
            'value': value
        })

    def log_calibration(self, point, command, response):
        st.session_state.calibration_log.append({
            'timestamp': datetime.now().isoformat(),
            'device_type': self.current_device['type'],
            'point': point,
            'command': command,
            'response': response
        })

if __name__ == "__main__":
    app = WhiteboxEZOApp()
    app.setup_ui()
