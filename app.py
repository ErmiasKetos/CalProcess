import streamlit as st
import serial
import serial.tools.list_ports
import time
import threading
from datetime import datetime
from collections import deque
from connection_handler import ConnectionHandler
from ui_components import ProbeUI

def get_available_ports():
    """Get list of available COM ports"""
    ports = []
    try:
        # List all COM ports
        port_list = serial.tools.list_ports.comports()
        st.sidebar.write("Detecting available ports...")
        
        if not port_list:
            st.sidebar.warning("No COM ports detected!")
        else:
            for port in port_list:
                st.sidebar.write(f"Found: {port.device} - {port.description}")
                ports.append(port.device)
    except Exception as e:
        st.sidebar.error(f"Error detecting ports: {str(e)}")
    
    return ports

def verify_port(port):
    """Verify if a port exists and is available"""
    try:
        # Check if port is in available ports list
        available_ports = get_available_ports()
        if port not in available_ports:
            st.sidebar.error(f"Port {port} not found in available ports!")
            st.sidebar.info("Available ports: " + ", ".join(available_ports))
            return False
            
        # Try to open the port
        ser = serial.Serial(port, 9600, timeout=1)
        ser.close()
        return True
    except Exception as e:
        st.sidebar.error(f"Error verifying port: {str(e)}")
        return False

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
    if 'available_ports' not in st.session_state:
        st.session_state['available_ports'] = []

def serial_listener(ser, probe_type):
    """Background thread for serial monitoring"""
    while st.session_state['listening']:
        try:
            if ser.in_waiting > 0:
                serial_string = ser.readline()
                try:
                    value = float(serial_string.decode('ASCII').strip())
                    st.session_state['readings'][probe_type].append(value)
                    st.session_state['readings']['timestamps'].append(datetime.now())
                except ValueError:
                    continue
            time.sleep(0.1)
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
    
    # Refresh ports button
    if st.sidebar.button("🔄 Refresh Ports"):
        st.session_state['available_ports'] = get_available_ports()

    # Port selection
    if not st.session_state['available_ports']:
        st.session_state['available_ports'] = get_available_ports()

    if st.session_state['available_ports']:
        port_selected = st.sidebar.selectbox(
            "Select Port",
            options=st.session_state['available_ports']
        )
    else:
        port_selected = st.sidebar.text_input(
            "Enter port manually:",
            value="COM6",
            help="No ports detected. Enter manually if you know the port."
        )

    col1, col2, col3 = st.sidebar.columns(3)
    
    try:
        with col1:
            if st.button('🔗 Connect', key='connect'):
                if verify_port(port_selected):
                    try:
                        ser = serial.Serial(
                            port=port_selected,
                            baudrate=9600,
                            bytesize=8,
                            timeout=2,
                            stopbits=serial.STOPBITS_ONE
                        )
                        st.session_state['serial_connection'] = ser
                        st.session_state['program_running'] = True
                        st.sidebar.success(f"Connected to {port_selected}")
                    except Exception as e:
                        st.sidebar.error(f"Connection failed: {str(e)}")
                else:
                    st.sidebar.error("Please select a valid port")

        # Rest of the code remains the same...
        
        with col2:
            if st.button('⏹️ Stop', key='stop'):
                if st.session_state['serial_connection']:
                    st.session_state['listening'] = False
                    time.sleep(0.5)
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

        # Main content remains the same...
        if st.session_state['serial_connection']:
            # ... rest of the code ...
            pass

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        if st.session_state['serial_connection']:
            st.session_state['serial_connection'].close()
            st.session_state['serial_connection'] = None
        st.session_state['listening'] = False
        st.session_state['program_running'] = False

if __name__ == "__main__":
    main()
