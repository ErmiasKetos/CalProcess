import streamlit as st
import time
import random  # Simulated dynamic updates

# Simulated Functions for Commands and Data
def send_command(command):
    if command == "I2C,scan":
        return "98: EZO ORP Circuit\n99: EZO pH Circuit\n100: EZO EC Circuit"
    elif command == "Slope,?":
        return "Slope,99.7,100.3,-0.89"
    return f"Command sent: {command}"

def get_current_reading(probe_type):
    if probe_type == "pH":
        return round(random.uniform(6.5, 7.5), 2)
    elif probe_type == "EC":
        return round(random.uniform(1.0, 1.5), 3)
    elif probe_type == "Temperature":
        return round(random.uniform(24.0, 26.0), 1)
    elif probe_type == "DO":
        return round(random.uniform(7.5, 9.0), 2)

def interpret_slope_data(slope_data):
    try:
        values = slope_data.split(",")
        mid_slope = float(values[1])
        high_slope = float(values[2])
        zero_offset = float(values[3])
        interpretation = f"""
        Midpoint Slope: {mid_slope}% (ideal ~100%)
        Highpoint Slope: {high_slope}% (ideal ~100%)
        Zero Point Offset: {zero_offset} mV (ideal ~0 mV)
        """
        if abs(mid_slope - 100) > 5 or abs(high_slope - 100) > 5:
            interpretation += "\n⚠️ Slopes deviate significantly. Recalibration recommended."
        else:
            interpretation += "\n✅ Slopes are within acceptable range."
        return interpretation
    except:
        return "Error interpreting slope data."

# CSS for Styling
st.markdown(
    """
    <style>
    .card {
        background-color: #f9fafb;
        padding: 20px;
        margin: 10px 0;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .card h3 {
        margin: 0 0 10px 0;
    }
    .current-reading-box {
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
        padding: 20px;
        border-radius: 10px;
        background-color: #e0f7fa;
        color: #00695c;
        border: 2px solid #004d40;
        margin: 10px 0;
    }
    .btn {
        padding: 10px 15px;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        font-weight: bold;
        margin: 5px;
    }
    .btn-primary {
        background-color: #007bff;
        color: white;
    }
    .btn-primary:hover {
        background-color: #0056b3;
    }
    .btn-danger {
        background-color: #dc3545;
        color: white;
    }
    .btn-danger:hover {
        background-color: #b21f2d;
    }
    .row {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
    }
    .col {
        flex: 1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# App Header
st.title("🌡️ Atlas Scientific Probe Calibration")

# Sidebar Status
st.sidebar.title("Device Connection")
connected = st.sidebar.button("🔗 Connect Device")
if connected:
    st.sidebar.success("✅ Device Connected!")
    st.sidebar.markdown(
        "Ensure Arduino IDE Serial Monitor is set to 9600 baud.\nYou can now use the EZO Console."
    )
    if st.sidebar.button("🔍 Scan for EZO Devices"):
        devices = send_command("I2C,scan")
        st.sidebar.info(f"Connected Devices:\n{devices}")
else:
    st.sidebar.warning("❌ Device Not Connected")

# Tabs for Probe Calibration
tab = st.selectbox("Select Probe", ["pH", "EC", "Temperature", "DO"])

# Layout for Current Reading and Calibration Controls
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(f"<h3>📊 {tab} Probe Current Reading</h3>", unsafe_allow_html=True)
current_reading = st.empty()

# Simulate Dynamic Current Reading
for _ in range(5):  # Simulated updates (use while True for real-time updates)
    reading = get_current_reading(tab)
    with current_reading:
        st.markdown(f'<div class="current-reading-box">{reading}</div>', unsafe_allow_html=True)
    time.sleep(1)

# Calibration Panels
if tab == "pH":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>🧪 pH Calibration</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        temp = st.number_input("🌡️ Enter Temperature (°C)", value=25.0)
    with col2:
        if st.button("Measure Temperature"):
            temp = get_current_reading("Temperature")
            st.success(f"Measured Temperature: {temp} °C")

    st.button("Calibrate pH 7 (Mid)", key="ph_mid", help="Send command for pH 7 calibration")
    st.button("Calibrate pH 4 (Low)", key="ph_low", help="Send command for pH 4 calibration")
    st.button("Calibrate pH 10 (High)", key="ph_high", help="Send command for pH 10 calibration")

    if st.button("Retrieve Slope Data"):
        slope_data = send_command("Slope,?")
        st.info(slope_data)
        st.write(interpret_slope_data(slope_data))

    st.button("❌ Clear Calibration", key="ph_clear", help="Clear all pH calibrations")
    st.markdown("</div>", unsafe_allow_html=True)

elif tab == "EC":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>🌊 EC Calibration</h3>", unsafe_allow_html=True)
    selected_k = st.selectbox("Select K Value", ["0.1", "1.0", "10.0"])
    st.button(f"Set K Value to {selected_k}")
    st.button("Dry Calibration")
    if selected_k == "0.1":
        st.button("Calibrate 84µS")
        st.button("Calibrate 1413µS")
    if selected_k == "1.0":
        st.button("Calibrate 12880µS")
        st.button("Calibrate 80000µS")
    if selected_k == "10.0":
        st.button("Calibrate 12880µS")
        st.button("Calibrate 150000µS")
    st.button("❌ Clear Calibration")
    st.markdown("</div>", unsafe_allow_html=True)

elif tab == "Temperature":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>🌡️ Temperature Calibration</h3>", unsafe_allow_html=True)
    temp = st.number_input("🌡️ Enter Temperature (°C)", value=25.0)
    st.button(f"Calibrate to {temp}°C")
    st.button("❌ Clear Calibration")
    st.markdown("</div>", unsafe_allow_html=True)

elif tab == "DO":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>🌬️ DO Calibration</h3>", unsafe_allow_html=True)
    st.button("Calibrate to Air")
    st.button("Calibrate Zero DO")
    st.button("❌ Clear Calibration")
    st.markdown("</div>", unsafe_allow_html=True)
