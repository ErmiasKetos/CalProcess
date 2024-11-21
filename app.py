import streamlit as st
import serial
import serial.tools.list_ports
import time
import threading
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from collections import deque

# Page config
st.set_page_config(
    page_title="EZO Probe Monitor",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .reading-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .reading-value {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .reading-timestamp {
        font-size: 12px;
        color: #666;
    }
    .status-connected {
        color: #28a745;
        font-weight: bold;
    }
    .status-disconnected {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'serial_connection' not in st.session_state:
    st.session_state['serial_connection'] = None
if 'readings' not in st.session_state:
    st.session_state['readings'] = {
        'pH': deque(maxlen=100),
        'EC': deque(maxlen=100),
        'DO': deque(maxlen=100),
        'RTD': deque(maxlen=100),
        'timestamps': deque(maxlen=100)
    }
if 'reading_active' not in st.session_state:
    st.session_state['reading_active'] = False
if 'last_reading_time' not in st.session_state:
    st.session_state['last_reading_time'] = None

def list_serial_ports():
    """List all available serial ports"""
    try:
        ports = list(serial.tools.list_ports.comports())
        available_ports = []
        for port in ports:
            st.write(f"Found port - Device: {port.device}, Description: {port.description}")
            if "Arduino" in port.description:
                st.write(f"Arduino detected on {port.device}")
            available_ports.append({"port": port.device, "description": port.description})
        return available_ports
    except Exception as e:
        st.error(f"Error listing ports: {e}")
        return []

def connect_to_device(port):
    """Connect to the selected serial port"""
    try:
        if not port:
            st.error("No port selected")
            return None
            
        ser = serial.Serial()
        ser.port = port
        ser.baudrate = 9600
        ser.timeout = 1
        
        if ser.is_open:
            ser.close()
            time.sleep(0.5)
            
        ser.open()
        time.sleep(2)  # Allow Arduino to stabilize
        
        if ser.is_open:
            return ser
        else:
            st.sidebar.error("Failed to open port")
            return None
            
    except Exception as e:
        st.sidebar.error(f"❌ Failed to connect: {e}")
        return None

def disconnect_device():
    """Disconnect from the serial port"""
    if 'serial_connection' in st.session_state and st.session_state['serial_connection']:
        try:
            st.session_state['reading_active'] = False
            time.sleep(0.5)  # Allow reading thread to stop
            st.session_state['serial_connection'].close()
            st.session_state['serial_connection'] = None
            st.session_state['last_reading_time'] = None
            st.sidebar.success("Disconnected successfully")
        except Exception as e:
            st.sidebar.error(f"Error disconnecting: {e}")

def send_command(ser, command):
    """Send command to the device and get response"""
    if not ser or not ser.is_open:
        st.error("No active connection")
        return []
        
    try:
        ser.reset_input_buffer()
        ser.write((command + "\r").encode())
        time.sleep(0.5)
        
        response = []
        while ser.in_waiting:
            line = ser.readline()
            response.append(line.decode().strip())
            
        return response
    except Exception as e:
        st.error(f"Error sending command: {e}")
        try:
            ser.close()
            time.sleep(0.5)
            ser.open()
        except:
            pass
        return []

def update_readings(probe_type, value):
    """Update readings in session state"""
    try:
        value = float(value)
        st.session_state['readings'][probe_type].append(value)
        current_time = datetime.now()
        st.session_state['readings']['timestamps'].append(current_time)
        st.session_state['last_reading_time'] = current_time
    except ValueError as e:
        st.error(f"Invalid reading value: {e}")
    except Exception as e:
        st.error(f"Error updating readings: {e}")

def create_reading_card(title, value, unit, timestamp=None):
    """Create a styled card for readings"""
    html = f"""
        <div class="reading-card">
            <h3>{title}</h3>
            <div class="reading-value">{value} {unit}</div>
            {f'<div class="reading-timestamp">Last updated: {timestamp}</div>' if timestamp else ''}
        </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def continuous_reading(ser, probe_type):
    """Continuously read from the probe"""
    while st.session_state['reading_active']:
        try:
            if not ser or not ser.is_open:
                st.error("Serial connection lost")
                st.session_state['reading_active'] = False
                break
                
            response = send_command(ser, "R")
            if response:
                update_readings(probe_type, response[0])
                
            # Check if it's time to log data
            current_time = datetime.now()
            if st.session_state.get('last_reading_time'):
                time_diff = (current_time - st.session_state['last_reading_time']).total_seconds()
                if time_diff < 3:  # Wait for remainder of 3 seconds
                    time.sleep(3 - time_diff)
            else:
                time.sleep(3)
                
        except Exception as e:
            st.error(f"Reading error: {e}")
            st.session_state['reading_active'] = False
            break

def get_reading_statistics(probe_type):
    """Calculate statistics for readings"""
    if not st.session_state['readings'][probe_type]:
        return None
        
    readings = list(st.session_state['readings'][probe_type])
    return {
        'min': min(readings),
        'max': max(readings),
        'avg': sum(readings) / len(readings),
        'count': len(readings)
    }

def clear_readings(probe_type=None):
    """Clear readings from session state"""
    if probe_type:
        st.session_state['readings'][probe_type].clear()
    else:
        for key in st.session_state['readings']:
            st.session_state['readings'][key].clear()
    st.session_state['last_reading_time'] = None
# Sidebar - Device Connection
st.sidebar.title("Device Connection")
available_ports = list_serial_ports()

if not available_ports:
    st.warning("No ports detected")
else:
    port_descriptions = [f"{p['port']} - {p['description']}" for p in available_ports]
    selected_port_desc = st.sidebar.selectbox(
        "Select Port",
        options=port_descriptions,
        index=0 if port_descriptions else None
    )
    
    if selected_port_desc:
        selected_port = selected_port_desc.split(' - ')[0]
    else:
        selected_port = None

    # Connection/Disconnection buttons
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔗 Connect"):
            if selected_port:
                ser = connect_to_device(selected_port)
                if ser:
                    st.session_state['serial_connection'] = ser
                    st.sidebar.success(f"✅ Connected to {selected_port}")
            else:
                st.sidebar.error("Please select a port")

    with col2:
        if st.session_state['serial_connection']:
            if st.button("❌ Disconnect"):
                disconnect_device()

# Main content
st.title("🧪 EZO Probe Monitoring and Calibration")

# Tabs for different functions
tab_main, tab_cal, tab_data = st.tabs(["📊 Monitoring", "🔧 Calibration", "📈 Data"])

# Monitoring Tab
with tab_main:
    if st.session_state['serial_connection']:
        st.subheader("Live Readings")
        
        # Probe selection
        probe_type = st.selectbox("Select Probe", ["pH", "EC", "DO", "RTD"])
        
        # Start/Stop reading
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start Reading"):
                st.session_state['reading_active'] = True
                thread = threading.Thread(
                    target=continuous_reading,
                    args=(st.session_state['serial_connection'], probe_type)
                )
                thread.daemon = True
                thread.start()
        
        with col2:
            if st.button("⏹️ Stop Reading"):
                st.session_state['reading_active'] = False

        # Display current reading
        if st.session_state['readings'][probe_type]:
            current_value = list(st.session_state['readings'][probe_type])[-1]
            current_time = list(st.session_state['readings']['timestamps'])[-1]
            
            units = {
                'pH': 'pH',
                'EC': 'µS/cm',
                'DO': 'mg/L',
                'RTD': '°C'
            }
            
            create_reading_card(
                f"{probe_type} Reading",
                f"{current_value:.2f}",
                units.get(probe_type, ''),
                current_time.strftime('%H:%M:%S')
            )

        # Display graph
        if len(st.session_state['readings'][probe_type]) > 1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(st.session_state['readings']['timestamps']),
                y=list(st.session_state['readings'][probe_type]),
                mode='lines+markers',
                name=probe_type
            ))
            
            fig.update_layout(
                title=f"{probe_type} Readings Over Time",
                xaxis_title="Time",
                yaxis_title=units.get(probe_type, ''),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please connect to a device to start monitoring.")

# Calibration Tab
with tab_cal:
    if st.session_state['serial_connection']:
        probe_type = st.selectbox("Select Probe for Calibration", 
                                ["pH", "EC", "DO", "RTD"], key='cal_select')
        
        if probe_type == "pH":
            st.subheader("pH Calibration")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Calibrate pH 7 (Mid)"):
                    response = send_command(st.session_state['serial_connection'], 
                                         "cal,mid,7")
                    st.success(f"Response: {' '.join(response)}")
            with col2:
                if st.button("Calibrate pH 4 (Low)"):
                    response = send_command(st.session_state['serial_connection'], 
                                         "cal,low,4")
                    st.success(f"Response: {' '.join(response)}")
            with col3:
                if st.button("Calibrate pH 10 (High)"):
                    response = send_command(st.session_state['serial_connection'], 
                                         "cal,high,10")
                    st.success(f"Response: {' '.join(response)}")

        elif probe_type == "EC":
            st.subheader("EC Calibration")
            k_value = st.selectbox("Select K Value", ["0.1", "1.0", "10.0"])
            if st.button(f"Set K Value to {k_value}"):
                response = send_command(st.session_state['serial_connection'], 
                                     f"k,{k_value}")
                st.success(f"Response: {' '.join(response)}")

        # Add other probe calibration options here...


# Data Tab
with tab_data:
    # First select the probe type
    selected_probe_type = st.selectbox(
        "Select Probe Type for Data",
        ["pH", "EC", "DO", "RTD"],
        key='data_probe_select'
    )
    
    # Then use the selected probe type for data display
    if st.session_state['readings'][selected_probe_type]:
        st.subheader(f"Recorded Data for {selected_probe_type}")
        
        # Convert readings to DataFrame
        df = pd.DataFrame({
            'Timestamp': list(st.session_state['readings']['timestamps']),
            'Value': list(st.session_state['readings'][selected_probe_type])
        })
        
        st.dataframe(df)
        
        # Download button
        if st.button("Download Data"):
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                f"{selected_probe_type}_readings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
            
        # Add statistics
        st.subheader("Statistics")
        stats = get_reading_statistics(selected_probe_type)
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Minimum", f"{stats['min']:.2f}")
            with col2:
                st.metric("Maximum", f"{stats['max']:.2f}")
            with col3:
                st.metric("Average", f"{stats['avg']:.2f}")
            with col4:
                st.metric("Count", stats['count'])
                
        # Clear data button
        if st.button("Clear Data"):
            clear_readings(selected_probe_type)
            st.success(f"Cleared all readings for {selected_probe_type}")
    else:
        st.info(f"No data recorded yet for {selected_probe_type}")
