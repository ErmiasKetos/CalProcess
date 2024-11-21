
import streamlit as st
import serial
import time

# Configuration for serial communication
SERIAL_PORT = 'COM3'  # Update with your Arduino's serial port
BAUD_RATE = 9600

# Connect to Arduino
@st.cache_resource
def get_serial_connection():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for the connection to stabilize
        return ser
    except Exception as e:
        st.error(f"Error connecting to Arduino: {e}")
        return None

# Send a command to the Arduino and get a response
def send_command(ser, command):
    try:
        ser.write((command + "\r").encode())  # Send command
        time.sleep(0.5)  # Allow time for response
        response = ser.readlines()
        return [line.decode().strip() for line in response]
    except Exception as e:
        st.error(f"Error communicating with Arduino: {e}")
        return []

# Streamlit app layout
st.title("EZO Device Calibration")

# Serial connection
ser = get_serial_connection()
if ser:
    st.success("Connected to Arduino!")
else:
    st.stop()

# Select the EZO device
st.sidebar.title("Device Selection")
device_type = st.sidebar.selectbox("Choose a sensor type:", [
    "pH", "Dissolved Oxygen (DO)", "Electrical Conductivity (EC)", 
    "Temperature (RTD)", "Oxidation-Reduction Potential (ORP)"
])

# Commands and actions
if st.sidebar.button("List Devices"):
    st.sidebar.write("Listing available devices...")
    response = send_command(ser, "!list")
    st.sidebar.write(response)

# Calibration workflow
st.header("Calibration Workflow")

if device_type == "pH":
    st.subheader("pH Calibration")
    mid_value = st.number_input("Midpoint (e.g., 7.00)", value=7.00, step=0.01)
    if st.button("Calibrate Midpoint"):
        response = send_command(ser, f"Cal,mid,{mid_value}")
        st.write(response)
elif device_type == "Dissolved Oxygen (DO)":
    st.subheader("Dissolved Oxygen Calibration")
    if st.button("Air Calibration"):
        response = send_command(ser, "Cal")
        st.write(response)
elif device_type == "Electrical Conductivity (EC)":
    st.subheader("Electrical Conductivity Calibration")
    ec_value = st.number_input("Calibration Solution (µS/cm)", value=1413, step=1)
    if st.button("Calibrate EC"):
        response = send_command(ser, f"Cal,{ec_value}")
        st.write(response)
elif device_type == "Temperature (RTD)":
    st.subheader("Temperature Calibration")
    temp_value = st.number_input("Temperature (°C)", value=25.0, step=0.1)
    if st.button("Calibrate Temperature"):
        response = send_command(ser, f"Cal,{temp_value}")
        st.write(response)
elif device_type == "Oxidation-Reduction Potential (ORP)":
    st.subheader("ORP Calibration")
    orp_value = st.number_input("Calibration Solution (mV)", value=475, step=1)
    if st.button("Calibrate ORP"):
        response = send_command(ser, f"Cal,{orp_value}")
        st.write(response)

# Temperature compensation
st.subheader("Temperature Compensation")
temp_comp = st.number_input("Set Temperature Compensation (°C)", value=25.0, step=0.1)
if st.button("Set Temperature Compensation"):
    response = send_command(ser, f"T,{temp_comp}")
    st.write(response)

# Take a reading
st.subheader("Take a Sensor Reading")
if st.button("Read Value"):
    response = send_command(ser, "R")
    st.write("Sensor Reading:", response)
