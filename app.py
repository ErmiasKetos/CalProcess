import streamlit as st
import serial
import serial.tools.list_ports
import time
import random  # For simulating real-time updates

# Helper function to get available serial ports
def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

# Function to send a command to the device
def send_command(command):
    # Simulate sending a command (replace with actual serial communication if needed)
    time.sleep(0.5)  # Simulate delay
    if command == "Slope,?":
        # Simulated slope data
        return "Slope,99.7,100.3,-0.89"
    return f"Command sent: {command}"

# Function to interpret slope data
def interpret_slope_data(slope_data):
    try:
        values = slope_data.split(",")
        mid_slope = float(values[1])  # Midpoint slope
        high_slope = float(values[2])  # High point slope
        zero_offset = float(values[3])  # Zero point offset
        interpretation = (
            f"Midpoint Slope: {mid_slope}% (ideal: ~100%)\n"
            f"High Point Slope: {high_slope}% (ideal: ~100%)\n"
            f"Zero Point Offset: {zero_offset} mV (ideal: ~0 mV)\n"
        )
        if abs(mid_slope - 100) > 5 or abs(high_slope - 100) > 5:
            interpretation += "⚠️ Calibration slopes deviate significantly from ideal values. Consider recalibrating or replacing the probe."
        else:
            interpretation += "✅ Calibration slopes are within acceptable range."
        return interpretation
    except Exception:
        return "Error interpreting slope data. Please ensure the data format is correct."

# Function to simulate current readings
def get_current_reading(probe_type):
    if probe_type == "pH":
        return round(random.uniform(6.5, 7.5), 2)  # Simulated pH reading
    elif probe_type == "EC":
        return round(random.uniform(1.0, 1.5), 3)  # Simulated EC reading in mS
    elif probe_type == "Temperature":
        return round(random.uniform(24.0, 26.0), 1)  # Simulated Temp in °C
    elif probe_type == "DO":
        return round(random.uniform(7.5, 9.0), 2)  # Simulated DO in mg/L
    return "No reading"

# CSS for Tailwind-Inspired Styling
st.markdown(
    """
    <style>
    .card {
        background-color: #ffffff;
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 10px;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
    }
    .btn-primary {
        background-color: #2563eb;
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    .btn-primary:hover {
        background-color: #1d4ed8;
    }
    .btn-danger {
        background-color: #dc2626;
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    .btn-danger:hover {
        background-color: #b91c1c;
    }
    .metric {
        display: flex;
        flex-direction: column;
        align-items: center;
        font-weight: bold;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Main Streamlit App
st.title("🌡️ Atlas Scientific Probe Calibration")

# Sidebar Connection Status
st.sidebar.title("Device Connection")
connection_status = st.sidebar.empty()
connected = st.sidebar.button("🔗 Connect Device")

if connected:
    connection_status.success("✅ Device Connected!")
else:
    connection_status.info("❌ Device Not Connected")

# Tabs for probe calibration
tab = st.selectbox("Select Probe Type", ["pH", "EC", "Temperature", "DO"])

# Dynamic current reading (updates every second)
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(f"<h3>📊 {tab} Probe Current Reading</h3>", unsafe_allow_html=True)
current_reading = st.empty()

# Simulate current reading updates
for _ in range(5):  # Simulate 5 updates; replace with `while True` if needed
    with current_reading:
        reading = get_current_reading(tab)
        if tab == "EC":
            st.metric(label=f"Current {tab} Reading", value=f"{reading} mS")
        elif tab == "Temperature":
            st.metric(label=f"Current {tab} Reading", value=f"{reading} °C")
        elif tab == "DO":
            st.metric(label=f"Current {tab} Reading", value=f"{reading} mg/L")
        else:
            st.metric(label=f"Current {tab} Reading", value=f"{reading}")
    time.sleep(1)

# Calibration Panels
if tab == "pH":
    st.markdown("<h3>🧪 pH Probe Calibration</h3>", unsafe_allow_html=True)

    # Temperature Measurement for Calibration
    if st.button("Measure Temperature for Calibration"):
        temperature = get_current_reading("Temperature")
        st.success(f"Measured Temperature: {temperature} °C")

    if st.button("Calibrate pH 7 (Mid)", key="ph_mid"):
        response = send_command("ph:cal,mid,7")
        st.success(response)
    if st.button("Calibrate pH 4 (Low)", key="ph_low"):
        response = send_command("ph:cal,low,4")
        st.success(response)
    if st.button("Calibrate pH 10 (High)", key="ph_high"):
        response = send_command("ph:cal,high,10")
        st.success(response)

    # Slope Data and Interpretation
    if st.button("Retrieve Slope Data"):
        slope_data = send_command("Slope,?")
        st.info(f"Slope Data: {slope_data}")
        st.write(interpret_slope_data(slope_data))

    if st.button("❌ Clear pH Calibration", key="clear_ph"):
        response = send_command("ph:cal,clear")
        st.warning(response)

elif tab == "EC":
    st.markdown("<h3>🌊 EC Probe Calibration</h3>", unsafe_allow_html=True)
    selected_k_value = st.selectbox("Select K Value", ["0.1", "1.0", "10.0"])
    if st.button("Set K Value"):
        response = send_command(f"ec:k,{selected_k_value}")
        st.success(response)
    if st.button("Dry Calibration"):
        response = send_command("ec:cal,dry")
        st.success(response)

    if selected_k_value == "0.1":
        if st.button("Calibrate 84µS"):
            response = send_command("ec:cal,low,84")
            st.success(response)
        if st.button("Calibrate 1413µS"):
            response = send_command("ec:cal,high,1413")
            st.success(response)
    elif selected_k_value == "1.0":
        if st.button("Calibrate 12880µS"):
            response = send_command("ec:cal,low,12880")
            st.success(response)
        if st.button("Calibrate 80000µS"):
            response = send_command("ec:cal,high,80000")
            st.success(response)
    elif selected_k_value == "10.0":
        if st.button("Calibrate 12880µS"):
            response = send_command("ec:cal,low,12880")
            st.success(response)
        if st.button("Calibrate 150000µS"):
            response = send_command("ec:cal,high,150000")
            st.success(response)

    if st.button("Clear EC Calibration"):
        response = send_command("ec:cal,clear")
        st.warning(response)

elif tab == "Temperature":
    st.markdown("<h3>🌡️ Temperature Probe Calibration</h3>", unsafe_allow_html=True)
    temp_value = st.number_input("Enter Calibration Temperature (°C)", value=25.0)
    if st.button("Calibrate Temperature"):
        response = send_command(f"rtd:cal,{temp_value}")
        st.success(response)
    if st.button("❌ Clear Temperature Calibration"):
        response = send_command("rtd:cal,clear")
        st.warning(response)

elif tab == "DO":
    st.markdown("<h3>🌬️ DO Probe Calibration</h3>", unsafe_allow_html=True)
    if st.button("Calibrate to Air"):
        response = send_command("do:cal")
        st.success(response)
    if st.button("Calibrate Zero DO"):
        response = send_command("do:cal,0")
        st.success(response)
    if st.button("❌ Clear DO Calibration"):
        response = send_command("do:cal,clear")
        st.warning(response)

st.markdown("</div>", unsafe_allow_html=True)
