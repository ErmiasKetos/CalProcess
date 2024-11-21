import streamlit as st
import serial
import serial.tools.list_ports
import time
import threading

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

# Sidebar for device connection
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

# Probe Reading and Commands Section
st.title("EZO Probe Monitoring and Calibration")

# Tabs for each probe type
tab = st.selectbox("Select Probe Type", ["pH", "EC", "Temperature", "DO"])

# Dynamic probe reading
if ser:
    st.markdown("### Current Probe Readings")
    reading_placeholder = st.empty()

    def fetch_probe_readings(command, label):
        while True:
            response = send_command(ser, command)
            if response:
                reading_placeholder.markdown(f"#### {label}: {response[0]}")
            time.sleep(3)

    # Probe-specific commands
    if tab == "pH":
        threading.Thread(target=fetch_probe_readings, args=("R", "pH Value")).start()
        st.markdown("### pH Probe Calibration")
        if st.button("Calibrate pH 7 (Mid)"):
            response = send_command(ser, "ph:cal,mid,7")
            st.success(" ".join(response))
        if st.button("Calibrate pH 4 (Low)"):
            response = send_command(ser, "ph:cal,low,4")
            st.success(" ".join(response))
        if st.button("Calibrate pH 10 (High)"):
            response = send_command(ser, "ph:cal,high,10")
            st.success(" ".join(response))
        if st.button("❌ Clear Calibration"):
            response = send_command(ser, "ph:cal,clear")
            st.warning(" ".join(response))
        if st.button("Retrieve Slope Data"):
            slope_response = send_command(ser, "Slope,?")
            st.info(" ".join(slope_response))

    elif tab == "EC":
        threading.Thread(target=fetch_probe_readings, args=("R", "EC Value")).start()
        st.markdown("### EC Probe Calibration")
        k_value = st.selectbox("Select K Value", ["0.1", "1.0", "10.0"])
        if st.button(f"Set K Value to {k_value}"):
            response = send_command(ser, f"ec:k,{k_value}")
            st.success(" ".join(response))
        if st.button("Dry Calibration"):
            response = send_command(ser, "ec:cal,dry")
            st.success(" ".join(response))
        if k_value == "0.1" and st.button("Calibrate 84µS"):
            response = send_command(ser, "ec:cal,low,84")
            st.success(" ".join(response))
        if k_value == "1.0" and st.button("Calibrate 12,880µS"):
            response = send_command(ser, "ec:cal,low,12880")
            st.success(" ".join(response))
        if k_value == "10.0" and st.button("Calibrate 150,000µS"):
            response = send_command(ser, "ec:cal,high,150000")
            st.success(" ".join(response))
        if st.button("❌ Clear Calibration"):
            response = send_command(ser, "ec:cal,clear")
            st.warning(" ".join(response))

    elif tab == "Temperature":
        threading.Thread(target=fetch_probe_readings, args=("R", "Temperature")).start()
        st.markdown("### Temperature Calibration")
        temp_value = st.number_input("🌡️ Enter Calibration Temperature (°C)", value=25.0)
        if st.button("Calibrate Temperature"):
            response = send_command(ser, f"RTD:cal,{temp_value}")
            st.success(" ".join(response))
        if st.button("❌ Clear Calibration"):
            response = send_command(ser, "RTD:cal,clear")
            st.warning(" ".join(response))

    elif tab == "DO":
        threading.Thread(target=fetch_probe_readings, args=("R", "Dissolved Oxygen")).start()
        st.markdown("### DO Probe Calibration")
        if st.button("Calibrate to Air"):
            response = send_command(ser, "do:cal")
            st.success(" ".join(response))
        if st.button("Calibrate Zero DO"):
            response = send_command(ser, "do:cal,0")
            st.success(" ".join(response))
        if st.button("❌ Clear Calibration"):
            response = send_command(ser, "do:cal,clear")
            st.warning(" ".join(response))
else:
    st.warning("Please connect to a device to start monitoring.")

