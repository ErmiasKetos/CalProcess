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

def verify_port_exists(port):
    """Verify if a port exists in the system"""
    try:
        all_ports = [p.device for p in serial.tools.list_ports.comports()]
        return port in all_ports
    except:
        return False

def test_port_connection(port):
    """Test if we can open a connection to the port"""
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        ser.close()
        return True
    except:
        return False

def get_system_ports():
    """Get system-specific default ports"""
    import platform
    system = platform.system()
    
    if system == "Windows":
        return [f"COM{i}" for i in range(1, 11)]
    elif system == "Linux":
        return ["/dev/ttyUSB0", "/dev/ttyACM0", "/dev/ttyS0"]
    elif system == "Darwin":  # macOS
        return ["/dev/tty.usbserial", "/dev/tty.usbmodem"]
    return []

def list_serial_ports():
    """List all available serial ports with better error handling"""
    try:
        ports = list(serial.tools.list_ports.comports())
        available_ports = []
        
        if not ports:
            st.warning("No serial ports found. Please check if your device is connected.")
            return []
            
        for port in ports:
            # Debug output
            st.sidebar.write(f"Detected: {port.device} - {port.description}")
            available_ports.append({
                "port": port.device,
                "description": port.description,
                "hwid": port.hwid
            })
            
        return available_ports
    except Exception as e:
        st.error(f"Error listing ports: {str(e)}")
        return []

def connect_to_device(port):
    """Connect to the selected serial port with enhanced error checking"""
    try:
        # Verify port exists
        if not verify_port_exists(port):
            st.sidebar.error(f"Port {port} not found in system")
            return None
            
        # Test if port is accessible
        if not test_port_connection(port):
            st.sidebar.error(f"Cannot access port {port}")
            return None
            
        # Try to connect
        ser = serial.Serial()
        ser.port = port
        ser.baudrate = 9600
        ser.timeout = 1
        
        # Close if already open
        if ser.is_open:
            ser.close()
            time.sleep(0.5)
        
        # Open connection
        ser.open()
        time.sleep(2)  # Allow Arduino to stabilize
        
        # Verify connection
        if ser.is_open:
            # Test communication
            ser.write(b"i\r")  # Send identification command
            time.sleep(0.5)
            if ser.in_waiting:
                return ser
            else:
                ser.close()
                st.sidebar.error("No response from device")
                return None
        else:
            st.sidebar.error("Failed to open port")
            return None
            
    except Exception as e:
        st.sidebar.error(f"❌ Connection error: {str(e)}")
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
    """Send command to device and get response"""
    if not ser or not ser.is_open:
        st.error("No active connection")
        return []
        
    try:
        # Clear input buffer
        ser.reset_input_buffer()
        
        # Send command with carriage return
        ser.write(f"{command}\r".encode())
        time.sleep(0.5)
        
        # Read response
        response = []
        while ser.in_waiting:
            line = ser.readline()
            response.append(line.decode().strip())
            
        return response
    except Exception as e:
        st.error(f"Error sending command: {e}")
        # Try to recover connection
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
        st.session_state['readings']['timestamps'].clear()
    else:
        for key in st.session_state['readings']:
            st.session_state['readings'][key].clear()
    st.session_state['last_reading_time'] = None

def export_readings(probe_type):
    """Export readings to CSV"""
    if not st.session_state['readings'][probe_type]:
        return None
        
    df = pd.DataFrame({
        'Timestamp': list(st.session_state['readings']['timestamps']),
        'Value': list(st.session_state['readings'][probe_type])
    })
    return df

def validate_reading(value, probe_type):
    """Validate reading values based on probe type"""
    try:
        value = float(value)
        # Define valid ranges for each probe type
        ranges = {
            'pH': (0, 14),
            'EC': (0, 200000),  # µS/cm
            'DO': (0, 20),      # mg/L
            'RTD': (-200, 850)  # °C
        }
        
        if probe_type in ranges:
            min_val, max_val = ranges[probe_type]
            return min_val <= value <= max_val
        return True
    except:
        return False

def get_unit_for_probe(probe_type):
    """Get the unit for a specific probe type"""
    units = {
        'pH': 'pH',
        'EC': 'µS/cm',
        'DO': 'mg/L',
        'RTD': '°C'
    }
    return units.get(probe_type, '')

def format_reading_value(value, probe_type):
    """Format reading value based on probe type"""
    try:
        value = float(value)
        formats = {
            'pH': '{:.2f}',
            'EC': '{:.0f}',
            'DO': '{:.2f}',
            'RTD': '{:.1f}'
        }
        return formats.get(probe_type, '{:.2f}').format(value)
    except:
        return str(value)
# Main title
st.title("🧪 EZO Probe Monitoring and Calibration")

# Sidebar - Device Connection
st.sidebar.title("Device Connection")

# Debug information
st.sidebar.write("Searching for ports...")
available_ports = list_serial_ports()

if not available_ports:
    st.sidebar.warning("No ports detected. Troubleshooting steps:")
    st.sidebar.markdown("""
    1. Check USB connection
    2. Verify Arduino power
    3. Try a different USB port
    4. Check device manager
    """)
    
    # Manual port entry option
    manual_port = st.sidebar.text_input("Or enter port manually:", 
                                      "COM3",  # Default for Windows
                                      help="Example: COM3 (Windows) or /dev/ttyUSB0 (Linux)")
    if st.sidebar.button("Connect to Manual Port"):
        ser = connect_to_device(manual_port)
        if ser:
            st.session_state['serial_connection'] = ser
            st.sidebar.success(f"✅ Connected to {manual_port}")
else:
    # Port selection from detected ports
    port_options = [f"{p['port']} - {p['description']}" for p in available_ports]
    selected_port_desc = st.sidebar.selectbox(
        "Select Port",
        options=port_options,
        index=0 if port_options else None,
        help="Select the port where your Arduino is connected"
    )
    
    if selected_port_desc:
        selected_port = selected_port_desc.split(' - ')[0]
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🔗 Connect"):
                ser = connect_to_device(selected_port)
                if ser:
                    st.session_state['serial_connection'] = ser
                    st.sidebar.success(f"✅ Connected to {selected_port}")
        
        with col2:
            if st.session_state.get('serial_connection'):
                if st.button("❌ Disconnect"):
                    disconnect_device()

# Add port refresh button
if st.sidebar.button("🔄 Refresh Ports"):
    st.experimental_rerun()

# Add connection status
if st.session_state.get('serial_connection'):
    st.sidebar.markdown(
        '<div class="status-connected">● Connected</div>',
        unsafe_allow_html=True
    )
else:
    st.sidebar.markdown(
        '<div class="status-disconnected">● Disconnected</div>',
        unsafe_allow_html=True
    )

# Main content
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
            
            create_reading_card(
                f"{probe_type} Reading",
                format_reading_value(current_value, probe_type),
                get_unit_for_probe(probe_type),
                current_time.strftime('%H:%M:%S')
            )

            # Display statistics
            stats = get_reading_statistics(probe_type)
            if stats:
                st.subheader("Statistics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Minimum", format_reading_value(stats['min'], probe_type))
                with col2:
                    st.metric("Maximum", format_reading_value(stats['max'], probe_type))
                with col3:
                    st.metric("Average", format_reading_value(stats['avg'], probe_type))
                with col4:
                    st.metric("Count", stats['count'])

            # Display graph
            if len(st.session_state['readings'][probe_type]) > 1:
                st.subheader("Readings Chart")
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
                    yaxis_title=get_unit_for_probe(probe_type),
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please connect to a device to start monitoring.")

# Calibration Tab
with tab_cal:
    if st.session_state['serial_connection']:
        st.subheader("Probe Calibration")
        probe_type = st.selectbox("Select Probe for Calibration", 
                                ["pH", "EC", "DO", "RTD"], 
                                key='cal_select')
        
        if probe_type == "pH":
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
    else:
        st.warning("Please connect to a device to perform calibration.")

# Data Tab
with tab_data:
    st.subheader("Recorded Data")
    selected_probe = st.selectbox("Select Probe Type", 
                                ["pH", "EC", "DO", "RTD"], 
                                key='data_probe_select')
    
    if st.session_state['readings'][selected_probe]:
        # Show data table
        df = export_readings(selected_probe)
        if df is not None:
            st.dataframe(df)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                f"{selected_probe}_readings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
            
            # Clear data button
            if st.button("Clear Data"):
                clear_readings(selected_probe)
                st.success(f"Cleared all readings for {selected_probe}")
    else:
        st.info(f"No data recorded yet for {selected_probe}")

if __name__ == "__main__":
    # This will only run when the script is run directly
    pass
