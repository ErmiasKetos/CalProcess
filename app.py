import streamlit as st
import serial
import serial.tools.list_ports
import time

# Function to list available serial ports
def list_serial_ports():
    try:
        ports = serial.tools.list_ports.comports()
        st.write("Available Ports:", [(p.device, p.description) for p in ports])  # Debug output
        return [port.device for port in ports]
    except Exception as e:
        st.error(f"Error listing ports: {e}")
        return []

# Function to connect to the selected port
def connect_to_device(port):
    try:
        ser = serial.Serial(port, 9600, timeout=1)  # Set baud rate to 9600
        time.sleep(2)  # Allow time for Arduino to stabilize
        st.sidebar.success(f"✅ Connected to {port}")
        return ser
    except Exception as e:
        st.sidebar.error(f"❌ Failed to connect: {e}")
        return None

# Sidebar for port selection
st.sidebar.title("Device Connection")
ports = list_serial_ports()

# If no ports detected, force COM6
if not ports:
    st.warning("No ports detected. Forcing COM6 as fallback.")
    ports = ["COM6"]

selected_port = st.sidebar.selectbox("Select Port", ports)

# Attempt to connect to the selected port
if st.sidebar.button("🔗 Connect Device"):
    ser = connect_to_device(selected_port)
else:
    ser = None

# Function to send commands to the Arduino
def send_command(ser, command):
    try:
        ser.write((command + "\r").encode())  # Write command to serial
        time.sleep(0.5)  # Wait for response
        response = ser.readlines()  # Read response
        return [line.decode().strip() for line in response]
    except Exception as e:
        st.error(f"Error sending command: {e}")
        return []

# If connected, allow the user to send commands
if ser:
    if st.sidebar.button("🔍 Scan for EZO Devices"):
        response = send_command(ser, "I2C,scan")  # Send I2C scan command
        if response:
            st.sidebar.info("Devices Found:\n" + "\n".join(response))
        else:
            st.sidebar.warning("No devices detected.")
else:
    st.sidebar.warning("Connect to a device to send commands.")
