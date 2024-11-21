import streamlit as st
from probes import setup_port_testing, pH_calibration, EC_calibration, DO_calibration, temperature_calibration

# Page setup
st.set_page_config(page_title="Atlas Scientific Calibration", layout="wide")

# Custom CSS for styling
st.markdown(
    """
    <style>
    body {
        background-color: #f7f9fc;
        font-family: Arial, sans-serif;
    }
    .card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    .card h3 {
        margin-top: 0;
    }
    .btn-primary {
        background-color: #007BFF;
        border: none;
        color: white;
        padding: 10px 20px;
        text-align: center;
        font-size: 14px;
        border-radius: 5px;
        cursor: pointer;
    }
    .btn-primary:hover {
        background-color: #0056b3;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title
st.markdown("<h1 style='text-align: center;'>Atlas Scientific Probe Calibration</h1>", unsafe_allow_html=True)

# Sidebar Port Testing
st.sidebar.title("Port Testing")
setup_port_testing(key_prefix="sidebar")

# Main App Tabs
st.markdown("<div class='card'><h3>Probes</h3></div>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["pH", "EC", "DO", "Temperature"])

with tab1:
    st.markdown("<div class='card'><h3>pH Probe Calibration</h3></div>", unsafe_allow_html=True)
    pH_calibration(key_prefix="ph")

with tab2:
    st.markdown("<div class='card'><h3>Electrical Conductivity Calibration</h3></div>", unsafe_allow_html=True)
    EC_calibration(key_prefix="ec")

with tab3:
    st.markdown("<div class='card'><h3>Dissolved Oxygen Calibration</h3></div>", unsafe_allow_html=True)
    DO_calibration(key_prefix="do")

with tab4:
    st.markdown("<div class='card'><h3>Temperature Probe Calibration</h3></div>", unsafe_allow_html=True)
    temperature_calibration(key_prefix="temp")
