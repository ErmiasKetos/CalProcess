import streamlit as st
import time
import threading
from datetime import datetime
from collections import deque
from connection_handler import ConnectionHandler
from ui_components import ProbeUI

# Page config
st.set_page_config(
    page_title="EZO Probe Monitor",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize all session state variables"""
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
    if 'last_calibration' not in st.session_state:
        st.session_state['last_calibration'] = {
            'pH': None,
            'EC': None,
            'DO': None,
            'RTD': None
        }
    if 'connection_handler' not in st.session_state:
        st.session_state['connection_handler'] = ConnectionHandler()
    if 'ui' not in st.session_state:
        st.session_state['ui'] = ProbeUI()

def continuous_reading(connection_handler, probe_type):
    """Background thread for continuous probe reading"""
    while st.session_state['reading_active']:
        try:
            if st.session_state['serial_connection'] and st.session_state['serial_connection'].is_open:
                reading = connection_handler.probe_reading(
                    st.session_state['serial_connection'], 
                    probe_type
                )
                
                st.session_state['readings'][probe_type].append(reading)
                st.session_state['readings']['timestamps'].append(datetime.now())
                
                time.sleep(1)  # Read every second
            else:
                st.session_state['reading_active'] = False
                break
        except Exception as e:
            st.error(f"Reading error: {str(e)}")
            st.session_state['reading_active'] = False
            break

def main():
    # Initialize session state
    initialize_session_state()
    
    # Get instances from session state
    connection_handler = st.session_state['connection_handler']
    ui = st.session_state['ui']
    
    # Create custom styles
    ui.create_styles()
    
    # Main title
    st.title("🧪 EZO Probe Monitor")
    
    # Sidebar - Connection handling
    st.sidebar.title("Device Connection")
    
    # Scan for ports
    st.sidebar.write("🔍 Scanning for available ports...")
    available_ports = connection_handler.scan_ports()
    
    if available_ports:
        st.sidebar.success(f"Found {len(available_ports)} available port(s)")
        for port in available_ports:
            status_color = "🟢" if port["status"] == "active" else "🟡"
            st.sidebar.write(f"{status_color} {port['port']} - {port['description']}")
    else:
        st.sidebar.warning("No ports automatically detected")
    
    # Manual port entry
    manual_port = st.sidebar.text_input(
        "Enter port manually:",
        value="COM6",
        help="Enter the port name (e.g., COM6, /dev/ttyUSB0)"
    )
    
    # Connection buttons
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔗 Connect"):
            ser = connection_handler.connect_to_port(manual_port)
            if ser:
                st.session_state['serial_connection'] = ser
                connection_handler.detect_probes(ser)
                st.sidebar.success(f"Connected to {manual_port}")
            else:
                st.sidebar.error("Connection failed")
    
    with col2:
        if st.session_state.get('serial_connection'):
            if st.button("❌ Disconnect"):
                st.session_state['serial_connection'].close()
                st.session_state['serial_connection'] = None
                st.session_state['reading_active'] = False
                st.sidebar.success("Disconnected")
    
    # Main content
    if st.session_state.get('serial_connection'):
        # Tabs for different functions
        tab_monitor, tab_cal, tab_data = st.tabs([
            "📊 Monitor", 
            "🔧 Calibration", 
            "📈 Data Analysis"
        ])
        
        # Monitoring Tab
        with tab_monitor:
            st.subheader("Live Probe Readings")
            
            # Probe selection
            probe_type = st.selectbox(
                "Select Probe",
                ["pH", "EC", "DO", "RTD"]
            )
            
            # Start/Stop reading
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Start Reading"):
                    st.session_state['reading_active'] = True
                    thread = threading.Thread(
                        target=continuous_reading,
                        args=(connection_handler, probe_type)
                    )
                    thread.daemon = True
                    thread.start()
            
            with col2:
                if st.button("⏹️ Stop Reading"):
                    st.session_state['reading_active'] = False
            
            # Display current reading
            if st.session_state['reading_active']:
                current_value = (
                    list(st.session_state['readings'][probe_type])[-1] 
                    if st.session_state['readings'][probe_type] 
                    else 0.000
                )
                ui.create_probe_card(
                    probe_type, 
                    current_value,
                    st.session_state['last_calibration'][probe_type]
                )
            
            # Display graph and statistics
            if st.session_state['readings'][probe_type]:
                ui.create_data_view(st.session_state['readings'], probe_type)
        
        # Calibration Tab
        with tab_cal:
            probe_type = st.selectbox(
                "Select Probe for Calibration",
                ["pH", "EC", "DO", "RTD"],
                key='cal_select'
            )
            
            # Show current reading during calibration
            current_value = connection_handler.probe_reading(
                st.session_state['serial_connection'],
                probe_type
            )
            ui.create_probe_card(probe_type, current_value)
            
            # Calibration interface
            cal_result = ui.create_calibration_ui(probe_type)
            if cal_result:
                point, value = cal_result
                response = connection_handler.calibrate_probe(
                    st.session_state['serial_connection'],
                    probe_type,
                    point,
                    value
                )
                st.success(f"Calibration response: {response}")
                if "OK" in str(response):
                    st.session_state['last_calibration'][probe_type] = datetime.now()
        
        # Data Analysis Tab
        with tab_data:
            probe_type = st.selectbox(
                "Select Probe Data",
                ["pH", "EC", "DO", "RTD"],
                key='data_select'
            )
            
            if st.session_state['readings'][probe_type]:
                # Create DataFrame
                df = pd.DataFrame({
                    'Timestamp': list(st.session_state['readings']['timestamps']),
                    'Value': list(st.session_state['readings'][probe_type])
                })
                
                # Show data table
                st.dataframe(df)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"{probe_type}_readings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
                
                # Clear data button
                if st.button("🗑️ Clear Data"):
                    st.session_state['readings'][probe_type].clear()
                    st.session_state['readings']['timestamps'].clear()
                    st.success(f"Cleared all readings for {probe_type}")
            else:
                st.info(f"No data recorded for {probe_type}")
    else:
        st.warning("Please connect to a device to start monitoring.")

if __name__ == "__main__":
    main()
