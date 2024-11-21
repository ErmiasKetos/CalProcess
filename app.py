import streamlit as st
import serial
import serial.tools.list_ports
import time

# Helper function to get available serial ports
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

# Streamlit GUI
st.title("Atlas Scientific Probe Calibration")

# Sidebar for Port Testing
st.sidebar.header("Port Testing")
ports = list_serial_ports()
selected_port = st.sidebar.selectbox("Select Port", ports)

if st.sidebar.button("Test Port Connection"):
    try:
        ser = serial.Serial(selected_port, 9600, timeout=1)
        time.sleep(2)  # Allow connection to stabilize
        st.sidebar.success("Connected successfully!")
    except Exception as e:
        st.sidebar.error(f"Connection failed: {e}")

# Main GUI Tabs
tab1, tab2, tab3, tab4 = st.tabs(["pH", "EC", "DO", "Temperature"])

# pH Calibration Tab
with tab1:
    st.subheader("pH Probe Calibration")
    mid_value = st.number_input("Midpoint Calibration (e.g., pH 7.00)", value=7.00, step=0.01)
    low_value = st.number_input("Low Calibration (e.g., pH 4.00)", value=4.00, step=0.01)
    high_value = st.number_input("High Calibration (e.g., pH 10.00)", value=10.00, step=0.01)

    if st.button("Calibrate pH 7 (Mid)"):
        response = send_command(ser, f"Cal,mid,{mid_value}")
        st.write("Response:", response)

    if st.button("Calibrate pH 4 (Low)"):
        response = send_command(ser, f"Cal,low,{low_value}")
        st.write("Response:", response)

    if st.button("Calibrate pH 10 (High)"):
        response = send_command(ser, f"Cal,high,{high_value}")
        st.write("Response:", response)

    if st.button("Clear pH Calibration"):
        response = send_command(ser, "Cal,clear")
        st.write("Response:", response)

    if st.button("Get pH Slope"):
        response = send_command(ser, "Slope,?")
        st.write("Slope Values:", response)

# EC Calibration Tab
with tab2:
    st.subheader("EC Probe Calibration")
    ec_value = st.number_input("Calibration Solution (µS/cm)", value=1413, step=1)
    if st.button("Calibrate EC"):
        response = send_command(ser, f"Cal,{ec_value}")
        st.write("Response:", response)

# DO Calibration Tab
with tab3:
    st.subheader("DO Probe Calibration")
    if st.button("Air Calibration"):
        response = send_command(ser, "Cal")
        st.write("Response:", response)

# Temperature Calibration Tab
with tab4:
    st.subheader("Temperature Probe Calibration")
    temp_value = st.number_input("Calibration Temperature (°C)", value=25.0, step=0.1)
    if st.button("Calibrate Temperature"):
        response = send_command(ser, f"Cal,{temp_value}")
        st.write("Response:", response)

# Temperature Compensation
st.subheader("Set Temperature Compensation")
temp_comp = st.number_input("Temperature Compensation (°C)", value=25.0, step=0.1)
if st.button("Set Temperature Compensation"):
    response = send_command(ser, f"T,{temp_comp}")
    st.write("Response:", response)

# Take a Reading
st.subheader("Take Sensor Reading")
if st.button("Read Sensor Value"):
    response = send_command(ser, "R")
    st.write("Sensor Reading:", response)
