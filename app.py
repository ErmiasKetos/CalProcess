import streamlit as st
import time
import threading
from datetime import datetime
from collections import deque
import pandas as pd
from ezo_components import EZOHandler, EZOUI
import streamlit as st
import serial
import serial.tools.list_ports

# List available COM ports
ports = [port.device for port in serial.tools.list_ports.comports()]

# Let the user select the COM port
selected_port = st.selectbox("Select COM Port", ports)

try:
    # Open the selected COM port
    ser = serial.Serial(selected_port, 9600, timeout=1)
    st.success(f"Successfully connected to {selected_port}")
    
    # Your code to interact with the device goes here
    
except serial.SerialException as e:
    st.error(f"Error: {e}")
    st.info("Please make sure the device is connected and the correct port is selected.")

def initialize_session_state():
    """Initialize all session state variables"""
    if 'serial_connection' not in st.session_state:
        st.session_state['serial_connection'] = None
    if 'readings' not in st.session_state:
        st.session_state['readings'] = {
            'pH': deque(maxlen=1000),
            'EC': deque(maxlen=1000),
            'DO': deque(maxlen=1000),
            'RTD': deque(maxlen=1000),
            'timestamps': deque(maxlen=1000)
        }
    if 'monitoring_active' not in st.session_state:
        st.session_state['monitoring_active'] = False
    if 'last_calibration' not in st.session_state:
        st.session_state['last_calibration'] = {
            'pH': None,
            'EC': None,
            'DO': None,
            'RTD': None
        }
    if 'handler' not in st.session_state:
        st.session_state['handler'] = EZOHandler()
    if 'ui' not in st.session_state:
        st.session_state['ui'] = EZOUI(st.session_state['handler'])

def monitor_readings(ser, probe_type):
    """Background thread for continuous probe monitoring"""
    while st.session_state['monitoring_active']:
        try:
            if ser and ser.is_open:
                value = st.session_state['handler'].get_reading(ser)
                
                if value != 0.000:  # Only record non-zero readings
                    st.session_state['readings'][probe_type].append(value)
                    st.session_state['readings']['timestamps'].append(datetime.now())
                
                time.sleep(1)  # Read every second
            else:
                st.session_state['monitoring_active'] = False
                break
        except Exception as e:
            st.error(f"Monitoring error: {str(e)}")
            st.session_state['monitoring_active'] = False
            break

def create_data_plot(readings, probe_type, handler):
    """Create interactive plot of probe readings"""
    if not readings[probe_type]:
        return
        
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Add main reading trace
    fig.add_trace(go.Scatter(
        x=list(readings['timestamps']),
        y=list(readings[probe_type]),
        mode='lines+markers',
        name=handler.probe_configs[probe_type]['name'],
        line=dict(color=handler.probe_configs[probe_type]['colors']['good'])
    ))
    
    # Update layout
    fig.update_layout(
        title=f"{handler.probe_configs[probe_type]['name']} Readings Over Time",
        xaxis_title="Time",
        yaxis_title=f"{handler.probe_configs[probe_type]['name']} ({handler.probe_configs[probe_type]['unit']})",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def export_readings(readings, probe_type, handler):
    """Export readings to CSV file"""
    if not readings[probe_type]:
        return None
        
    df = pd.DataFrame({
        'Timestamp': list(readings['timestamps']),
        f'{handler.probe_configs[probe_type]["name"]} ({handler.probe_configs[probe_type]["unit"]})': 
            list(readings[probe_type])
    })
    return df

def main():
    st.set_page_config(
        page_title="EZO Probe Monitor",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    initialize_session_state()
    
    st.title("🧪 EZO Probe Monitor")

    # Sidebar - Connection
    st.sidebar.title("Device Connection")
    
    # Port detection and selection
    available_ports = st.session_state['handler'].get_available_ports()
    
    if available_ports:
        port_options = [f"{p['port']} - {p['description']}" for p in available_ports]
        selected_port = st.sidebar.selectbox(
            "Select Port",
            port_options
        ).split(' - ')[0]
    else:
        selected_port = st.sidebar.text_input(
            "Enter Port Manually",
            value="COM6",
            help="Example: COM6 or /dev/ttyUSB0"
        )
    
    # Connection controls
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button('🔗 Connect', key='connect'):
            ser, response = st.session_state['handler'].connect_to_port(selected_port)
            if ser:
                st.session_state['serial_connection'] = ser
                st.sidebar.success(f"Connected! Response: {response}")
            else:
                st.sidebar.error(f"Connection failed: {response}")
    
    with col2:
        if st.button('❌ Disconnect', key='disconnect'):
            if st.session_state['serial_connection']:
                st.session_state['monitoring_active'] = False
                time.sleep(0.5)
                st.session_state['serial_connection'].close()
                st.session_state['serial_connection'] = None
                st.sidebar.success("Disconnected")

    # Main content
    if st.session_state['serial_connection']:
        tab_monitor, tab_cal, tab_data = st.tabs([
            "📊 Monitor",
            "🔧 Calibration",
            "📈 Data Analysis"
        ])
        
        # Monitoring Tab
        with tab_monitor:
            st.subheader("Live Readings")
            
            probe_type = st.selectbox(
                "Select Probe",
                ["pH", "EC", "DO", "RTD"]
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button('▶️ Start Monitoring'):
                    st.session_state['monitoring_active'] = True
                    thread = threading.Thread(
                        target=monitor_readings,
                        args=(st.session_state['serial_connection'], probe_type)
                    )
                    thread.daemon = True
                    thread.start()
            
            with col2:
                if st.button('⏹️ Stop Monitoring'):
                    st.session_state['monitoring_active'] = False
            
            # Display current reading
            if st.session_state['monitoring_active'] or st.session_state['readings'][probe_type]:
                current_value = (
                    st.session_state['handler'].get_reading(st.session_state['serial_connection'])
                    if st.session_state['monitoring_active']
                    else list(st.session_state['readings'][probe_type])[-1]
                )
                st.session_state['ui'].create_probe_card(probe_type, current_value)
            
            # Show graph if we have readings
            if st.session_state['readings'][probe_type]:
                create_data_plot(
                    st.session_state['readings'],
                    probe_type,
                    st.session_state['handler']
                )
        
        # Calibration Tab
        with tab_cal:
            probe_type = st.selectbox(
                "Select Probe for Calibration",
                ["pH", "EC", "DO", "RTD"],
                key='cal_select'
            )
            
            st.session_state['ui'].create_calibration_ui(
                probe_type,
                st.session_state['serial_connection']
            )
        
        # Data Analysis Tab
        with tab_data:
            st.subheader("Data Analysis")
            
            probe_type = st.selectbox(
                "Select Probe Data",
                ["pH", "EC", "DO", "RTD"],
                key='data_select'
            )
            
            if st.session_state['readings'][probe_type]:
                # Show statistics
                values = list(st.session_state['readings'][probe_type])
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Minimum", f"{min(values):.3f}")
                with col2:
                    st.metric("Maximum", f"{max(values):.3f}")
                with col3:
                    st.metric("Average", f"{sum(values)/len(values):.3f}")
                with col4:
                    st.metric("Readings", len(values))
                
                # Export options
                df = export_readings(
                    st.session_state['readings'],
                    probe_type,
                    st.session_state['handler']
                )
                
                if df is not None:
                    st.dataframe(df)
                    
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV",
                        csv,
                        f"ezo_{probe_type}_readings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
                    
                    if st.button("🗑️ Clear Data"):
                        st.session_state['readings'][probe_type].clear()
                        st.session_state['readings']['timestamps'].clear()
                        st.success("Data cleared")
            else:
                st.info("No data recorded yet")
    else:
        st.warning("Please connect to a device to start monitoring")

if __name__ == "__main__":
    main()
