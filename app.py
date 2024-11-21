import streamlit as st
import serial
import time
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from pathlib import Path
import json
import yaml
from styles import AppStyle, apply_plot_style, init_styling
from utils import SerialManager, DataLogger, DeviceManager
from setup_utils import WhiteboxSetup
from protocol_utils import ProtocolManager
from setup_utils import WhiteboxSetup


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
        self.init_session_state()
        self.load_config()
        self.serial_conn = None
        self.current_device = None
        self.data_logger = DataLogger()

    def init_session_state(self):
        """Initialize session state variables"""
        if 'connected' not in st.session_state:
            st.session_state.connected = False
        if 'readings' not in st.session_state:
            st.session_state.readings = []
        if 'calibration_log' not in st.session_state:
            st.session_state.calibration_log = []
        if 'devices' not in st.session_state:
            st.session_state.devices = []
        if 'current_device' not in st.session_state:
            st.session_state.current_device = None

    def load_config(self):
        """Load configuration from config.yaml"""
        with open('config.yaml', 'r') as file:
            self.config = yaml.safe_load(file)

    def setup_ui(self):
        """Setup main user interface"""
        st.set_page_config(
            page_title="WB Calibration Hub",
            page_icon="🧪",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize styling
        init_styling()

        # Main title with styled header
        st.markdown("""
            <div class="main-header">
                <h1>🧪 Whitebox Calibration Hub</h1>
            </div>
        """, unsafe_allow_html=True)

        # Sidebar
        self.render_sidebar()

        # Main content
        if not st.session_state.connected:
            AppStyle.alert(
                "Please connect to your Whitebox device using the sidebar", 
                "info"
            )
            return

        # Main tabs
        tabs = st.tabs([
            "📊 Dashboard",
            "🔧 Calibration",
            "📈 Analysis",
            "📝 Logs",
            "⚙️ Settings",
            "🔌 Setup"  # New tab
        ])

        with tabs[0]:
            self.render_dashboard()
        with tabs[1]:
            self.render_calibration()
        with tabs[2]:
            self.render_analysis()
        with tabs[3]:
            self.render_logs()
        with tabs[4]:
            self.render_settings()
        with tabs[5]:
            self.render_setup()

    def render_sidebar(self):
        """Render sidebar with connection controls"""
        st.sidebar.header("Device Connection")

        # Connection status
        if st.session_state.connected:
            AppStyle.status_indicator(True)
        else:
            AppStyle.status_indicator(False)

        # Port selection and connection
        port = st.sidebar.text_input("Serial Port", "/dev/ttyUSB0")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if not st.session_state.connected:
                if st.button("Connect", key="connect"):
                    self.connect_device(port)
            else:
                if st.button("Disconnect", key="disconnect"):
                    self.disconnect_device()
        
        with col2:
            if st.session_state.connected:
                if st.button("Scan Devices", key="scan"):
                    self.scan_devices()

        # Device list
        if st.session_state.connected and st.session_state.devices:
            st.sidebar.header("Connected Devices")
            for device in st.session_state.devices:
                with st.sidebar.expander(
                    f"{device['type']} (#{device['address']})"
                ):
                    AppStyle.device_card(
                        device['type'].lower(),
                        "Device Info",
                        device['info']
                    )

    def render_dashboard(self):
        """Render main dashboard"""
        st.header("Real-time Monitoring")

        # Device selection
        if not st.session_state.devices:
            AppStyle.alert("No devices detected. Please scan for devices.", "warning")
            return

        selected_device = st.selectbox(
            "Select Device",
            st.session_state.devices,
            format_func=lambda x: f"{x['type']} (#{x['address']})"
        )

        if selected_device:
            self.current_device = selected_device
            
            # Create three columns for readings
            col1, col2, col3 = st.columns(3)
            
            with col1:
                self.render_current_reading(selected_device)
            
            with col2:
                self.render_temperature_control(selected_device)
            
            with col3:
                if selected_device['type'] == 'pH':
                    self.render_ph_status(selected_device)
                elif selected_device['type'] == 'EC':
                    self.render_ec_status(selected_device)
                elif selected_device['type'] == 'DO':
                    self.render_do_status(selected_device)

            # Readings chart
            self.render_readings_chart(selected_device)

    def render_current_reading(self, device):
        """Render current reading display"""
        AppStyle.device_card(
            device['type'].lower(),
            "Current Reading",
            """
            <div class="reading-container">
                <div class="reading-label">Latest Measurement</div>
            </div>
            """
        )

        if st.button("Take Reading", key="take_reading"):
            if self.select_device(device['address']):
                response = self.send_command("R")
                if response:
                    AppStyle.reading_display(
                        response,
                        self.get_unit_for_device(device['type'])
                    )
                    self.log_reading(device['type'], response)

    def render_temperature_control(self, device):
        """Render temperature compensation control"""
        AppStyle.device_card(
            device['type'].lower(),
            "Temperature Compensation",
            """
            <div class="temperature-control">
                <div class="current-temp">Current: 25.0°C</div>
            </div>
            """
        )

        temp = st.number_input(
            "Temperature (°C)",
            value=25.0,
            min_value=0.0,
            max_value=100.0,
            key="temp_input"
        )

        if st.button("Set Temperature", key="set_temp"):
            if self.select_device(device['address']):
                response = self.send_command(f"T,{temp}")
                if response:
                    AppStyle.alert(
                        "Temperature compensation updated", 
                        "success"
                    )

    def render_ph_status(self, device):
        """Render pH-specific status"""
        if st.button("Check Slope", key="check_slope"):
            if self.select_device(device['address']):
                response = self.send_command("Slope,?")
                if response:
                    slopes = response.split(',')
                    AppStyle.device_card(
                        "ph",
                        "Calibration Status",
                        f"""
                        <div class="slope-info">
                            <div>Acid: {slopes[1]}%</div>
                            <div>Base: {slopes[2]}%</div>
                            <div>Zero: {slopes[3]} mV</div>
                        </div>
                        """
                    )

    
    def render_ec_status(self, device):
        """Render EC-specific status"""
        if st.button("Check K Value", key="check_k"):
            if self.select_device(device['address']):
                response = self.send_command("K,?")
                if response:
                    AppStyle.device_card(
                        "ec",
                        "Probe Status",
                        f"""
                        <div class="k-value-info">
                            <div>K Value: {response}</div>
                        </div>
                        """
                    )

    def render_do_status(self, device):
        """Render DO-specific status"""
        if st.button("Check Atmospheric Pressure", key="check_atm"):
            if self.select_device(device['address']):
                response = self.send_command("P,?")
                if response:
                    AppStyle.device_card(
                        "do",
                        "Probe Status",
                        f"""
                        <div class="pressure-info">
                            <div>Pressure: {response} kPa</div>
                        </div>
                        """
                    )

    def render_calibration(self):
        """Render calibration interface"""
        st.header("Probe Calibration")

        if not self.current_device:
            AppStyle.alert("Please select a device first", "warning")
            return

        # Display current device
        AppStyle.device_card(
            self.current_device['type'].lower(),
            "Selected Device",
            f"""
            <div class="device-info">
                <div>Type: {self.current_device['type']}</div>
                <div>Address: {self.current_device['address']}</div>
            </div>
            """
        )

        # Device-specific calibration
        if self.current_device['type'] == 'pH':
            self.render_ph_calibration()
        elif self.current_device['type'] == 'EC':
            self.render_ec_calibration()
        elif self.current_device['type'] == 'DO':
            self.render_do_calibration()
        elif self.current_device['type'] == 'RTD':
            self.render_rtd_calibration()

    def render_ph_calibration(self):
        """Render pH calibration interface"""
        st.subheader("pH Probe Calibration")
        
        cal_points = [
            {
                "name": "Mid Point (pH 7.0)",
                "command": "Cal,mid,7.00",
                "value": 7.0,
                "solution": "pH 7.00 buffer"
            },
            {
                "name": "Low Point (pH 4.0)",
                "command": "Cal,low,4.00",
                "value": 4.0,
                "solution": "pH 4.00 buffer"
            },
            {
                "name": "High Point (pH 10.0)",
                "command": "Cal,high,10.00",
                "value": 10.0,
                "solution": "pH 10.00 buffer"
            }
        ]

        for point in cal_points:
            with st.expander(point["name"]):
                self.calibration_step(
                    point["name"],
                    point["command"],
                    point["solution"]
                )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Calibration", key="clear_ph_cal"):
                response = self.send_command("Cal,clear")
                if response:
                    AppStyle.alert("Calibration cleared", "success")

        with col2:
            if st.button("Verify Calibration", key="verify_ph_cal"):
                response = self.send_command("Slope,?")
                if response:
                    slopes = response.split(',')
                    self.show_calibration_verification(slopes)

    def render_ec_calibration(self):
        """Render EC calibration interface"""
        st.subheader("EC Probe Calibration")

        # K-value selection
        k_value = st.selectbox(
            "Select K-value",
            ["0.1", "1.0", "10.0"],
            key="k_value_select"
        )

        if st.button("Set K-value", key="set_k"):
            response = self.send_command(f"K,{k_value}")
            if response:
                AppStyle.alert(f"K-value set to {k_value}", "success")

        # Get calibration points based on K-value
        cal_points = self.get_ec_cal_points(k_value)

        # Render calibration steps
        for point in cal_points:
            with st.expander(point["name"]):
                self.calibration_step(
                    point["name"],
                    point["command"],
                    point["solution"]
                )

        if st.button("Clear Calibration", key="clear_ec_cal"):
            response = self.send_command("Cal,clear")
            if response:
                AppStyle.alert("Calibration cleared", "success")

    def render_do_calibration(self):
        """Render DO calibration interface"""
        st.subheader("DO Probe Calibration")

        # Atmospheric pressure compensation
        pressure = st.number_input(
            "Atmospheric Pressure (kPa)",
            value=101.3,
            min_value=20.0,
            max_value=200.0
        )

        if st.button("Set Pressure", key="set_pressure"):
            response = self.send_command(f"P,{pressure}")
            if response:
                AppStyle.alert("Pressure updated", "success")

        cal_points = [
            {
                "name": "Atmospheric Oxygen Calibration",
                "command": "Cal",
                "solution": "Probe in air"
            },
            {
                "name": "Zero Oxygen Calibration",
                "command": "Cal,0",
                "solution": "Zero oxygen solution"
            }
        ]

        for point in cal_points:
            with st.expander(point["name"]):
                self.calibration_step(
                    point["name"],
                    point["command"],
                    point["solution"]
                )

        if st.button("Clear Calibration", key="clear_do_cal"):
            response = self.send_command("Cal,clear")
            if response:
                AppStyle.alert("Calibration cleared", "success")

    def render_rtd_calibration(self):
        """Render temperature calibration interface"""
        st.subheader("Temperature Probe Calibration")

        temp = st.number_input(
            "Known Temperature (°C)",
            value=25.0,
            min_value=-200.0,
            max_value=850.0
        )

        self.calibration_step(
            "Temperature Calibration",
            f"Cal,{temp}",
            "Known temperature reference"
        )

        if st.button("Clear Calibration", key="clear_rtd_cal"):
            response = self.send_command("Cal,clear")
            if response:
                AppStyle.alert("Calibration cleared", "success")

    def calibration_step(self, point_name, command, solution_info):
        """Render a single calibration step"""
        st.markdown(f"**Solution**: {solution_info}")

        col1, col2 = st.columns(2)

        with col1:
            # Current reading display
            reading_placeholder = st.empty()
            
            if st.button("Start Stabilization", key=f"stab_{point_name}"):
                self.run_stabilization(reading_placeholder)

        with col2:
            if st.button("Calibrate", key=f"cal_{point_name}"):
                response = self.send_command(command)
                if response:
                    AppStyle.alert(f"Calibration response: {response}", "success")
                    self.log_calibration(point_name, command, response)

    # ... [Part 2 of 3] - To be continued in next response ...
    def render_analysis(self):
        """Render data analysis interface"""
        st.header("Data Analysis")

        # Date range selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")

        # Device type filter
        device_type = st.selectbox(
            "Select Device Type",
            ["All"] + list(self.DEFAULT_ADDRESSES.keys())
        )

        # Get filtered data
        df = self.data_logger.get_readings_history(
            device_type if device_type != "All" else None,
            start_date,
            end_date
        )

        if df.empty:
            AppStyle.alert("No data available for selected criteria", "info")
            return

        # Display statistics
        self.render_statistics(df)
        
        # Display chart
        self.render_analysis_chart(df)

    def render_logs(self):
        """Render logs interface"""
        st.header("System Logs")

        tab1, tab2 = st.tabs(["Readings Log", "Calibration Log"])

        with tab1:
            self.render_readings_log()

        with tab2:
            self.render_calibration_log()

    def render_readings_log(self):
        """Render readings log table"""
        df = pd.DataFrame(st.session_state.readings)
        if not df.empty:
            st.dataframe(df)
            
            # Export option
            if st.button("Export Readings"):
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "readings_log.csv",
                    "text/csv"
                )
        else:
            st.info("No readings recorded yet")

    def render_calibration_log(self):
        """Render calibration log table"""
        df = pd.DataFrame(st.session_state.calibration_log)
        if not df.empty:
            st.dataframe(df)
            
            # Export option
            if st.button("Export Calibration Log"):
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "calibration_log.csv",
                    "text/csv"
                )
        else:
            st.info("No calibration events recorded yet")

    # Helper Methods
    def connect_device(self, port):
        """Connect to the Whitebox device"""
        try:
            self.serial_conn = serial.Serial(port, 9600, timeout=1)
            st.session_state.connected = True
            AppStyle.alert("Connected successfully!", "success")
        except Exception as e:
            AppStyle.alert(f"Connection failed: {str(e)}", "error")

    def disconnect_device(self):
        """Disconnect from the device"""
        if self.serial_conn:
            self.serial_conn.close()
        st.session_state.connected = False
        st.session_state.devices = []
        self.current_device = None
        AppStyle.alert("Disconnected from device", "info")

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
            st.session_state.devices = devices
            AppStyle.alert(f"Found {len(devices)} devices", "success")
        else:
            AppStyle.alert("No devices found", "warning")

    def send_command(self, cmd):
        """Send command to device"""
        if not self.serial_conn or not self.serial_conn.is_open:
            AppStyle.alert("Not connected to device", "error")
            return None

        try:
            self.serial_conn.write(f"{cmd}\r".encode())
            time.sleep(0.3)
            
            if self.serial_conn.in_waiting:
                response = self.serial_conn.readline().decode().strip()
                return response
            return None
        except Exception as e:
            AppStyle.alert(f"Command error: {str(e)}", "error")
            return None

    def select_device(self, address):
        """Select a device by address"""
        response = self.send_command(str(address))
        return response is not None

    def log_reading(self, device_type, value):
        """Log a reading"""
        st.session_state.readings.append({
            'timestamp': datetime.now().isoformat(),
            'device_type': device_type,
            'value': value
        })

    def log_calibration(self, point, command, response):
        """Log a calibration event"""
        st.session_state.calibration_log.append({
            'timestamp': datetime.now().isoformat(),
            'device_type': self.current_device['type'],
            'point': point,
            'command': command,
            'response': response
        })

    def get_unit_for_device(self, device_type):
        """Get the unit for a device type"""
        units = {
            'pH': 'pH',
            'EC': 'µS/cm',
            'DO': 'mg/L',
            'RTD': '°C',
            'ORP': 'mV',
            'HUM': '%'
        }
        return units.get(device_type, '')

    def run_stabilization(self, placeholder, duration=30):
        """Run stabilization period"""
        progress = st.progress(0)
        for i in range(duration):
            progress.progress((i + 1) / duration)
            response = self.send_command("R")
            if response:
                placeholder.metric("Current Reading", response)
            time.sleep(1)
        AppStyle.alert("Stabilization complete", "success")

    def get_ec_cal_points(self, k_value):
        """Get EC calibration points based on K-value"""
        if k_value == "0.1":
            return [
                {"name": "Dry Calibration", "command": "Cal,dry", "solution": "Dry probe"},
                {"name": "84 µS/cm", "command": "Cal,84", "solution": "84 µS/cm solution"},
                {"name": "1413 µS/cm", "command": "Cal,1413", "solution": "1413 µS/cm solution"}
            ]
        elif k_value == "1.0":
            return [
                {"name": "Dry Calibration", "command": "Cal,dry", "solution": "Dry probe"},
                {"name": "12880 µS/cm", "command": "Cal,12880", "solution": "12880 µS/cm solution"},
                {"name": "80000 µS/cm", "command": "Cal,80000", "solution": "80000 µS/cm solution"}
            ]

        else:  # k_value == "10.0"
            return [
                {"name": "Dry Calibration", "command": "Cal,dry", "solution": "Dry probe"},
                {"name": "12880 µS/cm", "command": "Cal,12880", "solution": "12880 µS/cm solution"},
                {"name": "150000 µS/cm", "command": "Cal,150000", "solution": "150000 µS/cm solution"}
            ]

    def render_readings_chart(self, device):
        """Render readings chart"""
        if not st.session_state.readings:
            return

        df = pd.DataFrame(st.session_state.readings)
        df = df[df['device_type'] == device['type']].copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        if df.empty:
            return

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['value'],
            mode='lines+markers',
            name=f"{device['type']} Readings"
        ))
        
        fig.update_layout(
            title=f"{device['type']} Readings Over Time",
            xaxis_title="Time",
            yaxis_title=f"Value ({self.get_unit_for_device(device['type'])})",
            height=400
        )
        
        fig = apply_plot_style(fig)
        st.plotly_chart(fig, use_container_width=True)

    def render_statistics(self, df):
        """Render statistics for analysis"""
        st.subheader("Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            AppStyle.reading_display(
                f"{df['value'].mean():.2f}",
                "Average"
            )
        
        with col2:
            AppStyle.reading_display(
                f"{df['value'].std():.2f}",
                "Std Dev"
            )
        
        with col3:
            AppStyle.reading_display(
                f"{df['value'].min():.2f}",
                "Minimum"
            )
        
        with col4:
            AppStyle.reading_display(
                f"{df['value'].max():.2f}",
                "Maximum"
            )

    def render_analysis_chart(self, df):
        """Render analysis chart"""
        st.subheader("Trend Analysis")
        
        fig = go.Figure()
        
        # Add readings trace
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['value'],
            mode='lines+markers',
            name='Readings'
        ))
        
        # Add moving average
        df['MA'] = df['value'].rolling(window=10).mean()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['MA'],
            mode='lines',
            name='Moving Average (10)',
            line=dict(dash='dash')
        ))
        
        fig.update_layout(
            title="Reading Trends with Moving Average",
            xaxis_title="Time",
            yaxis_title="Value",
            height=500
        )
        
        fig = apply_plot_style(fig)
        st.plotly_chart(fig, use_container_width=True)

    def show_calibration_verification(self, slopes):
            """Show calibration verification results for pH probe"""
            try:
                acid_slope = float(slopes[1])
                base_slope = float(slopes[2])
                zero_offset = float(slopes[3])
                
                st.subheader("Calibration Verification")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    status = "good" if 95 <= acid_slope <= 105 else "warning"
                    AppStyle.device_card(
                        "ph",
                        "Acid Slope",
                        f"""
                        <div class="verification-{status}">
                            <div class="value">{acid_slope:.1f}%</div>
                            <div class="status">
                                {status.upper()} 
                                {'✓' if status == 'good' else '⚠️'}
                            </div>
                            <div class="range">Target: 95-105%</div>
                        </div>
                        """
                    )
                
                with col2:
                    status = "good" if 95 <= base_slope <= 105 else "warning"
                    AppStyle.device_card(
                        "ph",
                        "Base Slope",
                        f"""
                        <div class="verification-{status}">
                            <div class="value">{base_slope:.1f}%</div>
                            <div class="status">
                                {status.upper()}
                                {'✓' if status == 'good' else '⚠️'}
                            </div>
                            <div class="range">Target: 95-105%</div>
                        </div>
                        """
                    )
                
                with col3:
                    status = "good" if -30 <= zero_offset <= 30 else "warning"
                    AppStyle.device_card(
                        "ph",
                        "Zero Offset",
                        f"""
                        <div class="verification-{status}">
                            <div class="value">{zero_offset:.1f} mV</div>
                            <div class="status">
                                {status.upper()}
                                {'✓' if status == 'good' else '⚠️'}
                            </div>
                            <div class="range">Target: ±30mV</div>
                        </div>
                        """
                    )

            # Add interpretation
            if all([95 <= acid_slope <= 105, 95 <= base_slope <= 105, -30 <= zero_offset <= 30]):
                st.success("✅ Calibration is valid and within acceptable ranges")
            else:
                st.warning("""
                ⚠️ One or more calibration parameters are outside recommended ranges.
                Consider recalibrating the probe.
                """)
                
                # Detailed recommendations
                if acid_slope < 95 or acid_slope > 105:
                    st.info("""
                    **Acid Slope Issue:**
                    - Clean probe tip
                    - Use fresh pH 4.0 buffer
                    - Ensure proper temperature compensation
                    """)
                
                if base_slope < 95 or base_slope > 105:
                    st.info("""
                    **Base Slope Issue:**
                    - Clean probe tip
                    - Use fresh pH 10.0 buffer
                    - Ensure proper temperature compensation
                    """)
                
                if abs(zero_offset) > 30:
                    st.info("""
                    **Zero Offset Issue:**
                    - Recalibrate mid-point (pH 7.0)
                    - Check for probe damage
                    - Consider probe replacement if persistent
                    """)

        except Exception as e:
            st.error(f"Error processing calibration verification: {str(e)}")
            st.info("Please ensure valid calibration data is available")

def main():
    app = WhiteboxEZOApp()
    app.setup_ui()

if __name__ == "__main__":
    main()
