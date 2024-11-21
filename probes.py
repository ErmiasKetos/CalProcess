import streamlit as st
import serial
import serial.tools.list_ports
import time

# Helper function to get serial ports
def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

# Function to send commands to Arduino
def send_command(ser, command):
    try:
        ser.write((command + "\r").encode())
        time.sleep(0.5)
        response = ser.readlines()
        return [line.decode().strip() for line in response]
    except Exception as e:
        st.error(f"Error communicating with device: {e}")
        return []

# Port Testing Setup
def setup_port_testing(key_prefix=""):
    ports = list_serial_ports()
    selected_port = st.sidebar.selectbox(
        "Select Port", ports, key=f"{key_prefix}_port_selectbox"
    )

    if st.sidebar.button("Test Port Connection", key=f"{key_prefix}_test_port_button"):
        try:
            ser = serial.Serial(selected_port, 9600, timeout=1)
            time.sleep(2)  # Allow connection to stabilize
            st.sidebar.success("Connected successfully!")
            return ser
        except Exception as e:
            st.sidebar.error(f"Connection failed: {e}")
            return None

# pH Calibration
def pH_calibration(key_prefix=""):
    ser = setup_port_testing(key_prefix=key_prefix)

    col1, col2, col3 = st.columns(3)
    with col1:
        mid_value = st.number_input("Mid Calibration (pH 7.00)", value=7.00, step=0.01, key=f"{key_prefix}_mid_value_input")
    with col2:
        low_value = st.number_input("Low Calibration (pH 4.00)", value=4.00, step=0.01, key=f"{key_prefix}_low_value_input")
    with col3:
        high_value = st.number_input("High Calibration (pH 10.00)", value=10.00, step=0.01, key=f"{key_prefix}_high_value_input")

    col1, col2, col3, col4 = st.columns(4)
    if col1.button("Calibrate Mid (pH 7)", key=f"{key_prefix}_calibrate_mid_button"):
        response = send_command(ser, f"Cal,mid,{mid_value}")
        st.success("Response: " + str(response))
    if col2.button("Calibrate Low (pH 4)", key=f"{key_prefix}_calibrate_low_button"):
        response = send_command(ser, f"Cal,low,{low_value}")
        st.success("Response: " + str(response))
    if col3.button("Calibrate High (pH 10)", key=f"{key_prefix}_calibrate_high_button"):
        response = send_command(ser, f"Cal,high,{high_value}")
        st.success("Response: " + str(response))
    if col4.button("Get Slope", key=f"{key_prefix}_get_slope_button"):
        slope_response = send_command(ser, "Slope,?")
        st.info("Slope Values: " + str(slope_response))

# EC Calibration
def EC_calibration(key_prefix=""):
    ser = setup_port_testing(key_prefix=key_prefix)
    col1, col2 = st.columns(2)
    with col1:
        ec_value = st.number_input("Calibration Solution (µS/cm)", value=1413, step=1, key=f"{key_prefix}_ec_value_input")
    if col2.button("Calibrate EC", key=f"{key_prefix}_calibrate_ec_button"):
        response = send_command(ser, f"Cal,{ec_value}")
        st.success("Response: " + str(response))

# DO Calibration
def DO_calibration(key_prefix=""):
    ser = setup_port_testing(key_prefix=key_prefix)
    if st.button("Air Calibration", key=f"{key_prefix}_calibrate_do_button"):
        response = send_command(ser, "Cal")
        st.success("Response: " + str(response))

# Temperature Calibration
def temperature_calibration(key_prefix=""):
    ser = setup_port_testing(key_prefix=key_prefix)
    col1, col2 = st.columns(2)
    with col1:
        temp_value = st.number_input("Calibration Temperature (°C)", value=25.0, step=0.1, key=f"{key_prefix}_temp_value_input")
