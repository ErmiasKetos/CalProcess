import streamlit as st
import serial
import serial.tools.list_ports
import pandas as pd
import time
from threading import Thread, Lock
import queue
import json
from datetime import datetime

# Initialize session state variables
if 'serial_port' not in st.session_state:
    st.session_state.serial_port = None
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'message_queue' not in st.session_state:
    st.session_state.message_queue = queue.Queue()
if 'current_reading' not in st.session_state:
    st.session_state.current_reading = "No reading"
if 'calibration_log' not in st.session_state:
    st.session_state.calibration_log = []

# Create a lock for thread-safe serial communication
serial_lock = Lock()

def get_available_ports():
    """Get list of available serial ports"""
    return [port.device for port in serial.tools.list_ports.comports()]

def connect_serial(port):
    """Connect to the selected serial port"""
    try:
        serial_port = serial.Serial(
            port=port,
            baudrate=9600,
            timeout=0.1,
            write_timeout=0.1,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        return serial_port
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

def send_command(command):
    """Send a command to the serial port"""
    if st.session_state.serial_port and st.session_state.serial_port.is_open:
        try:
            with serial_lock:
                cmd = f"{command}\r"
                st.session_state.serial_port.write(cmd.encode('ascii'))
                log_action(f"Sent command: {command}")
        except Exception as e:
            st.error(f"Error sending command: {str(e)}")
            log_action(f"Error: {str(e)}")

def log_action(message):
    """Log actions with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.calibration_log.append({"timestamp": timestamp, "message": message})

def main():
    st.title("Atlas Scientific Probe Calibrator")
    
    # Sidebar for connection controls
    with st.sidebar:
        st.header("Connection Settings")
        ports = get_available_ports()
        selected_port = st.selectbox("Select Serial Port", ports if ports else ["No ports available"])
        
        if st.button("Connect" if not st.session_state.connected else "Disconnect"):
            if not st.session_state.connected:
                st.session_state.serial_port = connect_serial(selected_port)
                if st.session_state.serial_port:
                    st.session_state.connected = True
                    log_action(f"Connected to {selected_port}")
            else:
                if st.session_state.serial_port:
                    st.session_state.serial_port.close()
                st.session_state.serial_port = None
                st.session_state.connected = False
                log_action("Disconnected from device")
        
        st.write("Connection Status:", "Connected" if st.session_state.connected else "Disconnected")

    # Main content area with tabs
    tab1, tab2, tab3, tab4 = st.tabs(["pH Calibration", "EC Calibration", "Temperature", "DO Calibration"])
    
    with tab1:
        st.header("pH Probe Calibration")
        if st.session_state.connected:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Calibrate pH 7 (Mid)"):
                    send_command("Cal,mid,7.00")
            with col2:
                if st.button("Calibrate pH 4 (Low)"):
                    send_command("Cal,low,4.00")
            with col3:
                if st.button("Calibrate pH 10 (High)"):
                    send_command("Cal,high,10.00")
            
            if st.button("Clear pH Calibration"):
                send_command("Cal,clear")
    
    with tab2:
        st.header("EC Probe Calibration")
        if st.session_state.connected:
            k_value = st.text_input("K Value", "1.0")
            if st.button("Set K Value"):
                send_command(f"K,{k_value}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Dry Calibration"):
                    send_command("Cal,dry")
            with col2:
                if st.button("Calibrate 12,880μS"):
                    send_command("Cal,low")
            with col3:
                if st.button("Calibrate 80,000μS"):
                    send_command("Cal,high")
    
    with tab3:
        st.header("Temperature Calibration")
        if st.session_state.connected:
            temp_value = st.text_input("Temperature Value (°C)", "25.0")
            if st.button("Calibrate Temperature"):
                send_command(f"Cal,{temp_value}")
    
    with tab4:
        st.header("DO Calibration")
        if st.session_state.connected:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Calibrate to Air"):
                    send_command("Cal,atm")
            with col2:
                if st.button("Calibrate Zero DO"):
                    send_command("Cal,zero")
    
    # Display current reading and calibration log
    st.header("Current Reading")
    st.write(st.session_state.current_reading)
    
    st.header("Calibration Log")
    if st.session_state.calibration_log:
        log_df = pd.DataFrame(st.session_state.calibration_log)
        st.dataframe(log_df, use_container_width=True)

if __name__ == "__main__":
    main()
