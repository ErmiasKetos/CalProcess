import streamlit as st
import serial
import time
import threading
from datetime import datetime
from collections import deque
from connection_handler import ConnectionHandler
from ui_components import ProbeUI

def initialize_session_state():
    if 'serial_connection' not in st.session_state:
        st.session_state['serial_connection'] = None
    if 'program_running' not in st.session_state:
        st.session_state['program_running'] = True
    if 'listening' not in st.session_state:
        st.session_state['listening'] = False
    if 'readings' not in st.session_state:
        st.session_state['readings'] = {
            'pH': deque(maxlen=100),
            'EC': deque(maxlen=100),
            'DO': deque(maxlen=100),
            'RTD': deque(maxlen=100),
            'timestamps': deque(maxlen=100)
        }
    if 'connection_handler' not in st.session_state:
        st.session_state['connection_handler'] = ConnectionHandler()
    if 'ui' not in st.session_state:
        st.session_state['ui'] = ProbeUI()

def serial_listener(ser, probe_type):
    """Background thread for serial monitoring"""
    while st.session_state['listening']:
        try:
            if ser.in_waiting > 0:
                # Read the data
                serial_string = ser.readline()
                try:
                    # Try to decode and convert to float
                    value = float(serial_string.decode('ASCII').strip())
                    # Update readings
                    st.session_state['readings'][probe_type].append(value)
                    st.session_state['readings']['timestamps'].append(datetime.now())
                except ValueError:
                    continue
            time.sleep(0.1)  # Small delay to prevent CPU overhead
        except Exception as e:
            st.error(f"Reading error: {str(e)}")
            st.session_state['listening'] = False
            break

def main():
    st.set_page_config(
        page_title="EZO Probe Monitor",
        page_icon="🧪",
        layout="wide",
    )

    initialize_session_state()
    
    st.title("🧪 EZO Probe Monitor")

    # Sidebar - Connection
    st.sidebar.title("Device Connection")
    
    # Port selection
    manual_port = st.sidebar.text_input(
        "Enter port name:",
        value="COM6",
        help="Example: COM6 (Windows) or /dev/ttyUSB0 (Linux)"
    )

    col1, col2, col3 = st.sidebar.columns(3)
    
    try:
        with col1:
            if st.button('🔗 Connect', key='connect'):
                try:
                    ser = serial.Serial(
                        port=manual_port,
                        baudrate=9600,
                        bytesize=8,
                        timeout=2,
                        stopbits=serial.STOPBITS_ONE
                    )
                    st.session_state['serial_connection'] = ser
                    st.session_state['program_running'] = True
                    st.sidebar.success(f"Connected to {manual_port}")
                except Exception as e:
                    st.sidebar.error(f"Connection failed: {str(e)}")

        with col2:
            if st.button('⏹️ Stop', key='stop'):
                if st.session_state['serial_connection']:
                    st.session_state['listening'] = False
                    time.sleep(0.5)  # Give time for listener to stop
                    st.session_state['serial_connection'].close()
                    st.sidebar.success("Stopped monitoring")

        with col3:
            if st.button('❌ Exit', key='exit'):
                if st.session_state['serial_connection']:
                    st.session_state['listening'] = False
                    st.session_state['program_running'] = False
                    time.sleep(0.5)
                    st.session_state['serial_connection'].close()
                    st.session_state['serial_connection'] = None
                st.sidebar.success("Connection closed")

        # Main content
        if st.session_state['serial_connection']:
            tab_monitor, tab_cal, tab_data = st.tabs([
                "📊 Monitor", 
                "🔧 Calibration", 
                "📈 Data"
            ])

            # Monitoring Tab
            with tab_monitor:
                st.subheader("Live Readings")
                
                probe_type = st.selectbox(
                    "Select Probe",
                    ["pH", "EC", "DO", "RTD"]
                )

                if st.button('▶️ Start Reading'):
                    if not st.session_state['listening']:
                        st.session_state['listening'] = True
                        thread = threading.Thread(
                            target=serial_listener,
                            args=(st.session_state['serial_connection'], probe_type)
                        )
                        thread.daemon = True
                        thread.start()
                        st.success("Started monitoring")

                # Display current reading if available
                if st.session_state['readings'][probe_type]:
                    current_value = list(st.session_state['readings'][probe_type])[-1]
                    st.session_state['ui'].create_probe_card(
                        probe_type,
                        current_value,
                        None
                    )

                # Display graph if we have data
                if len(st.session_state['readings'][probe_type]) > 1:
                    st.session_state['ui'].create_data_view(
                        st.session_state['readings'],
                        probe_type
                    )

            # Calibration Tab
            with tab_cal:
                st.subheader("Probe Calibration")
                probe_type = st.selectbox(
                    "Select Probe for Calibration",
                    ["pH", "EC", "DO", "RTD"],
                    key='cal_select'
                )
                
                # Show live reading during calibration
                if st.session_state['listening']:
                    if st.session_state['readings'][probe_type]:
                        current_value = list(st.session_state['readings'][probe_type])[-1]
                        st.session_state['ui'].create_probe_card(probe_type, current_value)

                cal_result = st.session_state['ui'].create_calibration_ui(probe_type)
                if cal_result:
                    point, value = cal_result
                    st.session_state['connection_handler'].calibrate_probe(
                        st.session_state['serial_connection'],
                        probe_type,
                        point,
                        value
                    )

            # Data Tab content remains the same...

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        if st.session_state['serial_connection']:
            st.session_state['serial_connection'].close()
            st.session_state['serial_connection'] = None
        st.session_state['listening'] = False
        st.session_state['program_running'] = False

if __name__ == "__main__":
    main()
