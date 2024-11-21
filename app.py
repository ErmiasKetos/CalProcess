import streamlit as st
import serial
import serial.tools.list_ports
import time

# Function to list available serial ports
def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

# Function to establish connection with the Whitebox T1

def connect_to_device(port):
    try:
        ser = serial.Serial(port, 9600, timeout=1)  # Set correct baud rate
        time.sleep(2)  # Allow time for the device to stabilize
        return ser
    except Exception as e:
        st.error(f"Failed to connect to device: {e}")
        return None

# Function to send a command to the device
def send_command(ser, command):
    try:
        ser.write((command + "\r").encode())
        time.sleep(0.5)  # Allow time for response
        response = ser.readlines()
        return [line.decode().strip() for line in response]
    except Exception as e:
        st.error(f"Error sending command: {e}")
        return []

# Sidebar for device connection
st.sidebar.title("Device Connection")
ports = list_serial_ports()
selected_port = st.sidebar.selectbox("Select Port", ports)

# Connect to device
if st.sidebar.button("🔗 Connect Device"):
    ser = connect_to_device(selected_port)
    if ser:
        st.sidebar.success("✅ Connected to Device!")
    else:
        st.sidebar.error("❌ Connection Failed")
else:
    ser = None

# Scan for connected EZO devices
if ser and st.sidebar.button("🔍 Scan for EZO Devices"):
    response = send_command(ser, "I2C,scan")
    st.sidebar.info("Connected Devices:\n" + "\n".join(response))

# Tabs for calibration
tab = st.selectbox("Select Probe Type", ["pH", "EC", "Temperature", "DO"])

# Dynamic reading display
if ser:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"<h3>📊 {tab} Probe Current Reading</h3>", unsafe_allow_html=True)
    current_reading = st.empty()

    # Continuously fetch readings
    for _ in range(10):  # Replace with `while True` for continuous updates
        command = "R"  # Read command for the selected probe
        response = send_command(ser, command)
        if response:
            reading = response[0]
            st.markdown(f'<div class="current-reading-box">{reading}</div>', unsafe_allow_html=True)
        time.sleep(1)

# Calibration sections
if tab == "pH":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>🧪 pH Probe Calibration</h3>", unsafe_allow_html=True)

    # Temperature measurement
    temp_col1, temp_col2 = st.columns(2)
    with temp_col1:
        temp = st.number_input("🌡️ Enter Calibration Temperature (°C)", value=25.0)
    with temp_col2:
        if st.button("Measure Temperature"):
            temp_response = send_command(ser, "RT")
            if temp_response:
                temp = temp_response[0]
                st.success(f"Measured Temperature: {temp} °C")

    if st.button("Calibrate pH 7 (Mid)", key="ph_mid"):
        response = send_command(ser, "ph:cal,mid,7")
        st.success(" ".join(response))
    if st.button("Calibrate pH 4 (Low)", key="ph_low"):
        response = send_command(ser, "ph:cal,low,4")
        st.success(" ".join(response))
    if st.button("Calibrate pH 10 (High)", key="ph_high"):
        response = send_command(ser, "ph:cal,high,10")
        st.success(" ".join(response))

    if st.button("Retrieve Slope Data"):
        slope_response = send_command(ser, "Slope,?")
        st.info(" ".join(slope_response))

    if st.button("❌ Clear Calibration", key="ph_clear"):
        response = send_command(ser, "ph:cal,clear")
        st.warning(" ".join(response))
    st.markdown("</div>", unsafe_allow_html=True)

elif tab == "EC":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>🌊 EC Probe Calibration</h3>", unsafe_allow_html=True)

    k_value = st.selectbox("Select K Value", ["0.1", "1.0", "10.0"])
    if st.button(f"Set K Value to {k_value}"):
        response = send_command(ser, f"ec:k,{k_value}")
        st.success(" ".join(response))

    if st.button("Dry Calibration"):
        response = send_command(ser, "ec:cal,dry")
        st.success(" ".join(response))

    if k_value == "0.1":
        if st.button("Calibrate 84µS"):
            response = send_command(ser, "ec:cal,low,84")
            st.success(" ".join(response))
        if st.button("Calibrate 1413µS"):
            response = send_command(ser, "ec:cal,high,1413")
            st.success(" ".join(response))
    if st.button("❌ Clear Calibration"):
        response = send_command(ser, "ec:cal,clear")
        st.warning(" ".join(response))
    st.markdown("</div>", unsafe_allow_html=True)

elif tab == "Temperature":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>🌡️ Temperature Calibration</h3>", unsafe_allow_html=True)
    temp_value = st.number_input("🌡️ Enter Calibration Temperature (°C)", value=25.0)
    if st.button("Calibrate Temperature"):
        response = send_command(ser, f"RTD:cal,{temp_value}")
        st.success(" ".join(response))
    if st.button("❌ Clear Calibration"):
        response = send_command(ser, "RTD:cal,clear")
        st.warning(" ".join(response))
    st.markdown("</div>", unsafe_allow_html=True)

elif tab == "DO":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>🌬️ DO Probe Calibration</h3>", unsafe_allow_html=True)
    if st.button("Calibrate to Air"):
        response = send_command(ser, "do:cal")
        st.success(" ".join(response))
    if st.button("Calibrate Zero DO"):
        response = send_command(ser, "do:cal,0")
        st.success(" ".join(response))
    if st.button("❌ Clear Calibration"):
        response = send_command(ser, "do:cal,clear")
        st.warning(" ".join(response))
    st.markdown("</div>", unsafe_allow_html=True)
