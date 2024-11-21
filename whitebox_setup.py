import serial
import serial.tools.list_ports
import time
import streamlit as st
from pathlib import Path
import yaml

class WhiteboxT1Setup:
    def __init__(self):
        self.serial_conn = None
        self.detected_devices = {}
        self.default_addresses = {
            'DO': 97,    # 0x61
            'ORP': 98,   # 0x62
            'pH': 99,    # 0x63
            'EC': 100,   # 0x64
            'RTD': 102,  # 0x66
            'PMP': 103,  # 0x67
            'CO2': 105,  # 0x69
            'PRS': 106,  # 0x6A
            'O2': 108,   # 0x6c
            'HUM': 111,  # 0x6F
            'RGB': 112   # 0x70
        }

    def detect_arduino(self):
        """Automatically detect Arduino with Whitebox T1"""
        ports = list(serial.tools.list_ports.comports())
        arduino_ports = [
            p.device for p in ports
            if 'Arduino' in p.description or 'USB Serial' in p.description
        ]
        return arduino_ports

    def connect(self, port, baudrate=9600):
        """Connect to Whitebox T1"""
        try:
            self.serial_conn = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino initialization
            return True
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
            return False

    def send_command(self, command, wait_time=0.3):
        """Send command to device"""
        if not self.serial_conn:
            return None
        try:
            self.serial_conn.write(f"{command}\r".encode())
            time.sleep(wait_time)
            if self.serial_conn.in_waiting:
                return self.serial_conn.readline().decode().strip()
            return None
        except Exception as e:
            st.error(f"Command error: {str(e)}")
            return None

    def scan_devices(self):
        """Scan for connected EZO devices"""
        response = self.send_command("!scan", wait_time=1)
        if not response:
            return []

        devices = []
        lines = response.split('\n')
        for line in lines:
            if ':' in line:
                addr, info = line.split(':', 1)
                addr = int(addr.strip())
                for device_type, default_addr in self.default_addresses.items():
                    if default_addr == addr:
                        devices.append({
                            'type': device_type,
                            'address': addr,
                            'info': info.strip()
                        })
        return devices

    def verify_i2c_mode(self, device):
        """Verify device is in I2C mode"""
        self.send_command(str(device['address']))
        response = self.send_command("Protocol,?")
        return response and 'I2C' in response

    def setup_device(self, device):
        """Initialize and verify device setup"""
        # Select device
        self.send_command(str(device['address']))
        
        # Check protocol
        if not self.verify_i2c_mode(device):
            st.warning(f"{device['type']} not in I2C mode")
            return False
        
        # Device-specific initialization
        if device['type'] == 'pH':
            self.init_ph_device()
        elif device['type'] == 'EC':
            self.init_ec_device()
        elif device['type'] == 'DO':
            self.init_do_device()
        elif device['type'] == 'RTD':
            self.init_rtd_device()
            
        return True

    def init_ph_device(self):
        """Initialize pH probe"""
        # Check calibration status
        response = self.send_command("Cal,?")
        if response:
            st.info(f"pH Calibration Status: {response}")
        
        # Check temperature compensation
        response = self.send_command("T,?")
        if response:
            st.info(f"Temperature Compensation: {response}°C")
        
        # Check slope
        response = self.send_command("Slope,?")
        if response:
            st.info(f"pH Slope Status: {response}")

    def init_ec_device(self):
        """Initialize EC probe"""
        # Check K value
        response = self.send_command("K,?")
        if response:
            st.info(f"EC K-value: {response}")
        
        # Check calibration status
        response = self.send_command("Cal,?")
        if response:
            st.info(f"EC Calibration Status: {response}")

    def init_do_device(self):
        """Initialize DO probe"""
        # Check atmospheric pressure
        response = self.send_command("P,?")
        if response:
            st.info(f"Atmospheric Pressure: {response}")
        
        # Check calibration status
        response = self.send_command("Cal,?")
        if response:
            st.info(f"DO Calibration Status: {response}")

    def init_rtd_device(self):
        """Initialize RTD probe"""
        # Check calibration status
        response = self.send_command("Cal,?")
        if response:
            st.info(f"Temperature Calibration Status: {response}")

    def save_configuration(self, devices):
        """Save detected devices configuration"""
        config = {
            'devices': {
                device['type']: {
                    'address': device['address'],
                    'info': device['info']
                } for device in devices
            },
            'setup_date': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        Path('config').mkdir(exist_ok=True)
        with open('config/devices.yaml', 'w') as f:
            yaml.dump(config, f)

def setup_page():
    st.title("🔌 Whitebox T1 Setup Assistant")
    
    setup = WhiteboxT1Setup()
    
    # Auto-detect Arduino
    arduino_ports = setup.detect_arduino()
    
    if not arduino_ports:
        st.error("No Arduino detected! Please check connection.")
        st.write("Troubleshooting steps:")
        st.write("1. Ensure Arduino is connected")
        st.write("2. Check if power switch is set to 'ARDUINO'")
        st.write("3. Verify proper driver installation")
        return

    # Connection section
    st.header("1. Device Connection")
    port = st.selectbox("Select Arduino Port", arduino_ports)
    
    if st.button("Connect & Initialize"):
        progress = st.progress(0)
        
        # Connect to device
        progress.progress(20)
        if setup.connect(port):
            st.success("Connected to Whitebox T1")
            
            # Scan for devices
            progress.progress(40)
            st.write("Scanning for EZO devices...")
            devices = setup.scan_devices()
            
            if devices:
                st.success(f"Found {len(devices)} EZO devices")
                progress.progress(60)
                
                # Initialize each device
                for i, device in enumerate(devices):
                    st.write(f"Initializing {device['type']} device...")
                    if setup.setup_device(device):
                        st.success(f"{device['type']} initialized successfully")
                    progress.progress(60 + (i+1)*40/len(devices))
                
                # Save configuration
                setup.save_configuration(devices)
                st.success("Setup complete! Configuration saved.")
            else:
                st.warning("No EZO devices found. Please check connections.")
        else:
            st.error("Failed to connect to Whitebox T1")

if __name__ == "__main__":
    setup_page()
