import streamlit as st
import serial
import sys
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

def connect_serial(port_name):
    """Establish serial connection with enhanced error handling"""
    try:
        # Format port name for Windows
        if port_name.startswith('COM'):
            port_name = f'\\\\.\{port_name}'
            
        # Try to establish connection
        ser = serial.Serial(
            port=port_name,
            baudrate=9600,
            timeout=1,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        
        # Wait for connection to stabilize
        time.sleep(2)
        
        # Test communication
        ser.write(b"i\r")
        time.sleep(0.5)
        
        if ser.in_waiting:
            response = ser.readline().decode().strip()
            st.sidebar.success(f"Connected to {port_name}")
            st.sidebar.info(f"Device response: {response}")
            return ser
        else:
            ser.close()
            st.sidebar.error("No response from device")
            return None
            
    except serial.SerialException as e:
        st.sidebar.error(f"Serial Error: {str(e)}")
        return None
    except Exception as e:
        st.sidebar.error(f"Connection Error: {str(e)}")
        return None

def serial_listener(ser, probe_type):
    """Monitor serial port for readings"""
    while st.session_state['listening']:
        try:
            if ser.in_waiting:
                # Send read command
                ser.write(b"R\r")
                time.sleep(0.1)
                
                # Read response
                response = ser.readline().decode().strip()
                
                try:
                    value = float(response)
                    st.session_state['readings'][probe_type].append(value)
                    st.session_state['readings']['timestamps'].append(datetime.now())
                except ValueError:
                    continue
                    
            time.sleep(0.5)  # Poll every 500ms
            
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
    
    # Port input
    port_name = st.sidebar.text_input(
        "Enter COM port:",
        value="COM8",
        help="Example: COM8"
    )

    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button('🔗 Connect'):
            ser = connect_serial(port_name)
            if ser:
                st.session_state['serial_connection'] = ser
                st.session_state['program_running'] = True
    
    with col2:
        if st.button('❌ Disconnect'):
            if st.session_state['serial_connection']:
                st.session_state['listening'] = False
                time.sleep(0.5)
                st.session_state['serial_connection'].close()
                st.session_state['serial_connection'] = None
                st.session_state['program_running'] = False
                st.sidebar.success("Disconnected")

    # Main content
    if st.session_state['serial_connection']:
        tab_monitor, tab_cal = st.tabs(["📊 Monitor", "🔧 Calibration"])

        # Monitoring Tab
        with tab_monitor:
            st.subheader("Live Readings")
            
            probe_type = st.selectbox(
                "Select Probe",
                ["pH", "EC", "DO", "RTD"]
            )

            col1, col2 = st.columns(2)
            
            with col1:
                if st.button('▶️ Start Reading'):
                    if not st.session_state['listening']:
                        st.session_state['listening'] = True
                        thread = threading.Thread(
                            target=serial_listener,
                            args=(st.session_state['serial_connection'], probe_type)
                        )
                        thread.daemon = True
                        thread.start()
            
            with col2:
                if st.button('⏹️ Stop Reading'):
                    st.session_state['listening'] = False

            # Display current reading
            if st.session_state['readings'][probe_type]:
                current_value = list(st.session_state['readings'][probe_type])[-1]
                st.markdown(
                    f"""
                    <div style="padding: 20px; border-radius: 10px; background-color: #f0f2f6;">
                        <h3>{probe_type} Reading</h3>
                        <h2 style="color: #0066cc;">{current_value:.3f}</h2>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Calibration Tab
        with tab_cal:
            st.subheader("Probe Calibration")
            
            probe_type = st.selectbox(
                "Select Probe for Calibration",
                ["pH", "EC", "DO", "RTD"],
                key='cal_select'
            )

            if probe_type == "pH":
                if st.button("Calibrate pH 7 (Mid)"):
                    st.session_state['serial_connection'].write(b"cal,mid,7\r")
                    time.sleep(0.5)
                    response = st.session_state['serial_connection'].readline().decode()
                    st.success(f"Calibration response: {response}")

if __name__ == "__main__":
    main()
