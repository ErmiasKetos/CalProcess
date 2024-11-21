import streamlit as st
import serial
import serial.tools.list_ports
import time

# Helper function to get available serial ports
def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

# Function to send a command to the device
def send_command(command):
    # Simulate sending a command (replace with actual serial communication if needed)
    time.sleep(0.5)  # Simulate delay
    return f"Command sent: {command}"

# CSS for styling
st.markdown(
    """
    <style>
    body {
        font-family: Arial, sans-serif;
        background-color: #f9f9f9;
    }
    .card {
        background-color: white;
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 10px;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
    }
    .card h3 {
        margin-top: 0;
    }
    .btn {
        background-color: #007bff;
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    .btn:hover {
        background-color: #0056b3;
    }
    .btn-destructive {
        background-color: #dc3545;
        color: white;
    }
    .btn-destructive:hover {
        background-color: #b52b37;
    }
    .tabs {
        display: flex;
        gap: 10px;
    }
    .tabs button {
        flex: 1;
        padding: 10px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        background-color: #f1f1f1;
    }
    .tabs button.active {
        background-color: #007bff;
        color: white;
    }
    .tab-content {
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Main Streamlit App
st.title("Atlas Scientific Probe Calibration")

# Connection Status
connection_status = st.sidebar.empty()
connected = st.sidebar.button("Connect Device")

if connected:
    connection_status.success("Device Connected!")
else:
    connection_status.info("Device Not Connected")

# Tabs for probe calibration
tab = st.selectbox("Select Probe Type", ["pH", "EC", "Temperature", "DO"])

# pH Calibration
if tab == "pH":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>pH Probe Calibration</h3>", unsafe_allow_html=True)
    st.write(f"Current Reading: {'No reading' if not connected else '7.00'}")

    if st.button("Calibrate pH 7 (Mid)"):
        response = send_command("ph:cal,mid,7")
        st.write(response)
    if st.button("Calibrate pH 4 (Low)"):
        response = send_command("ph:cal,low,4")
        st.write(response)
    if st.button("Calibrate pH 10 (High)"):
        response = send_command("ph:cal,high,10")
        st.write(response)
    if st.button("Clear pH Calibration", key="clear_ph"):
        response = send_command("ph:cal,clear")
        st.write(response)
    st.markdown("</div>", unsafe_allow_html=True)

# EC Calibration
elif tab == "EC":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>EC Probe Calibration</h3>", unsafe_allow_html=True)
    st.write(f"Current Reading: {'No reading' if not connected else '1.413mS'}")

    selected_k_value = st.selectbox("Select K Value", ["0.1", "1.0", "10.0"])
    if st.button("Set K Value"):
        response = send_command(f"ec:k,{selected_k_value}")
        st.write(response)

    if st.button("Dry Calibration"):
        response = send_command("ec:cal,dry")
        st.write(response)

    if selected_k_value == "0.1":
        if st.button("Calibrate 84µS"):
            response = send_command("ec:cal,low,84")
            st.write(response)
        if st.button("Calibrate 1413µS"):
            response = send_command("ec:cal,high,1413")
            st.write(response)
    elif selected_k_value == "1.0":
        if st.button("Calibrate 12880µS"):
            response = send_command("ec:cal,low,12880")
            st.write(response)
        if st.button("Calibrate 80000µS"):
            response = send_command("ec:cal,high,80000")
            st.write(response)
    elif selected_k_value == "10.0":
        if st.button("Calibrate 12880µS"):
            response = send_command("ec:cal,low,12880")
            st.write(response)
        if st.button("Calibrate 150000µS"):
            response = send_command("ec:cal,high,150000")
            st.write(response)

    if st.button("Clear EC Calibration"):
        response = send_command("ec:cal,clear")
        st.write(response)
    st.markdown("</div>", unsafe_allow_html=True)

# Temperature Calibration
elif tab == "Temperature":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Temperature Probe Calibration</h3>", unsafe_allow_html=True)
    st.write(f"Current Reading: {'No reading' if not connected else '25.0°C'}")

    custom_temp = st.number_input("Enter Calibration Temperature", value=25.0)
    if st.button("Calibrate Temperature"):
        response = send_command(f"rtd:cal,{custom_temp}")
        st.write(response)
    if st.button("Clear Temperature Calibration"):
        response = send_command("rtd:cal,clear")
        st.write(response)
    st.markdown("</div>", unsafe_allow_html=True)

# DO Calibration
elif tab == "DO":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>DO Probe Calibration</h3>", unsafe_allow_html=True)
    st.write(f"Current Reading: {'No reading' if not connected else '8.00mg/L'}")

    if st.button("Calibrate to Air"):
        response = send_command("do:cal")
        st.write(response)
    if st.button("Calibrate Zero DO"):
        response = send_command("do:cal,0")
        st.write(response)
    if st.button("Clear DO Calibration"):
        response = send_command("do:cal,clear")
        st.write(response)
    st.markdown("</div>", unsafe_allow_html=True)
