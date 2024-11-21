import streamlit as st
import time

# CSS for Tailwind-like styling
st.markdown("""
    <style>
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .card {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .card h3 {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .btn {
            background-color: #1d4ed8;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        .btn:hover {
            background-color: #1e40af;
        }
        .btn-destructive {
            background-color: #dc2626;
            color: white;
        }
        .btn-destructive:hover {
            background-color: #b91c1c;
        }
        .input {
            width: 100%;
            padding: 8px;
            margin: 10px 0;
            border: 1px solid #d1d5db;
            border-radius: 4px;
        }
        .select {
            width: 100%;
            padding: 8px;
            margin: 10px 0;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            background-color: white;
        }
        .status {
            color: #6b7280;
            font-size: 0.875rem;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tabs button {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            background-color: #e5e7eb;
        }
        .tabs button.active {
            background-color: #1d4ed8;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# State management for device connection and calibration status
if "connected" not in st.session_state:
    st.session_state.connected = False
if "status" not in st.session_state:
    st.session_state.status = ""

# Connect to device
def connect_device():
    st.session_state.connected = True
    st.session_state.status = "Connected to device"

# Send command simulation
def send_command(command):
    time.sleep(0.5)  # Simulate a delay
    st.session_state.status = f"Command sent: {command}"

# Tabs for selecting probes
st.markdown("<div class='container'>", unsafe_allow_html=True)
st.markdown("<h1>Atlas Scientific Probe Calibration</h1>", unsafe_allow_html=True)

tabs = st.tabs(["pH", "EC", "Temperature", "DO"])

# pH Calibration Tab
with tabs[0]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>pH Probe Calibration</h3>", unsafe_allow_html=True)
    st.markdown(f"<p class='status'>Current Reading: {'7.00' if st.session_state.connected else 'No reading'}</p>", unsafe_allow_html=True)

    if st.button("Calibrate pH 7 (Mid)"):
        send_command("ph:cal,mid,7")
    if st.button("Calibrate pH 4 (Low)"):
        send_command("ph:cal,low,4")
    if st.button("Calibrate pH 10 (High)"):
        send_command("ph:cal,high,10")
    if st.button("Clear pH Calibration", key="clear_ph"):
        send_command("ph:cal,clear")
    st.markdown("</div>", unsafe_allow_html=True)

# EC Calibration Tab
with tabs[1]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>EC Probe Calibration</h3>", unsafe_allow_html=True)
    st.markdown(f"<p class='status'>Current Reading: {'1.413mS' if st.session_state.connected else 'No reading'}</p>", unsafe_allow_html=True)

    selected_k_value = st.selectbox("Select K Value", ["0.1", "1.0", "10.0"])
    if st.button("Set K Value"):
        send_command(f"ec:k,{selected_k_value}")

    if st.button("Dry Calibration"):
        send_command("ec:cal,dry")

    if selected_k_value == "0.1":
        if st.button("Calibrate 84µS"):
            send_command("ec:cal,low,84")
        if st.button("Calibrate 1413µS"):
            send_command("ec:cal,high,1413")
    elif selected_k_value == "1.0":
        if st.button("Calibrate 12880µS"):
            send_command("ec:cal,low,12880")
        if st.button("Calibrate 80000µS"):
            send_command("ec:cal,high,80000")
    elif selected_k_value == "10.0":
        if st.button("Calibrate 12880µS"):
            send_command("ec:cal,low,12880")
        if st.button("Calibrate 150000µS"):
            send_command("ec:cal,high,150000")

    if st.button("Clear EC Calibration"):
        send_command("ec:cal,clear")
    st.markdown("</div>", unsafe_allow_html=True)

# Temperature Calibration Tab
with tabs[2]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Temperature Probe Calibration</h3>", unsafe_allow_html=True)
    st.markdown(f"<p class='status'>Current Reading: {'25.0°C' if st.session_state.connected else 'No reading'}</p>", unsafe_allow_html=True)

    custom_temp = st.number_input("Enter Calibration Temperature", value=25.0)
    if st.button("Calibrate Temperature"):
        send_command(f"rtd:cal,{custom_temp}")
    if st.button("Clear Temperature Calibration"):
        send_command("rtd:cal,clear")
    st.markdown("</div>", unsafe_allow_html=True)

# DO Calibration Tab
with tabs[3]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>DO Probe Calibration</h3>", unsafe_allow_html=True)
    st.markdown(f"<p class='status'>Current Reading: {'8.00mg/L' if st.session_state.connected else 'No reading'}</p>", unsafe_allow_html=True)

    if st.button("Calibrate to Air"):
        send_command("do:cal")
    if st.button("Calibrate Zero DO"):
        send_command("do:cal,0")
    if st.button("Clear DO Calibration"):
        send_command("do:cal,clear")
    st.markdown("</div>", unsafe_allow_html=True)

# Device Connection Button
st.sidebar.button("Connect Device", on_click=connect_device)
st.sidebar.write(f"Status: {st.session_state.status}")

st.markdown("</div>", unsafe_allow_html=True)
