import serial
import serial.tools.list_ports
import time
import streamlit as st
from pathlib import Path
import yaml
from protocol_utils import ProtocolManager

class WhiteboxSetup:
    def __init__(self, serial_conn=None):
        self.serial_conn = serial_conn
        self.protocol_manager = ProtocolManager(serial_conn)
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

    def initialize_device(self, device):
        """Initialize and verify device setup"""
        if not self.serial_conn:
            return False

        # Check protocol
        current_protocol = self.protocol_manager.check_protocol(device['address'])
        
        if current_protocol != "I2C":
            st.warning(f"{device['type']} is not in I2C mode. Would you like to switch it?")
            if st.button("Switch to I2C"):
                success = self.protocol_manager.switch_to_i2c(
                    device['address'],
                    device['address']  # Keep same address
                )
                if not success:
                    return False
        
        # Device-specific initialization
        init_functions = {
            'pH': self.init_ph_device,
            'EC': self.init_ec_device,
            'DO': self.init_do_device,
            'RTD': self.init_rtd_device
        }
        
        if device['type'] in init_functions:
            return init_functions[device['type']](device['address'])
            
        return True

    def init_ph_device(self, address):
        """Initialize pH probe"""
        self.send_command(str(address))
        status = {}
        
        # Check calibration
        response = self.send_command("Cal,?")
        status['calibration'] = response if response else "Unknown"
        
        # Check temperature compensation
        response = self.send_command("T,?")
        status['temperature'] = response if response else "25.0"
        
        # Check slope
        response = self.send_command("Slope,?")
        status['slope'] = response if response else "Unknown"
        
        return status

    def init_ec_device(self, address):
        """Initialize EC probe"""
        self.send_command(str(address))
        status = {}
        
        # Check K value
        response = self.send_command("K,?")
        status['k_value'] = response if response else "Unknown"
        
        # Check calibration
        response = self.send_command("Cal,?")
        status['calibration'] = response if response else "Unknown"
        
        return status

    def init_do_device(self, address):
        """Initialize DO probe"""
        self.send_command(str(address))
        status = {}
        
        # Check pressure
        response = self.send_command("P,?")
        status['pressure'] = response if response else "101.3"
        
        # Check calibration
        response = self.send_command("Cal,?")
        status['calibration'] = response if response else "Unknown"
        
        return status

    def init_rtd_device(self, address):
        """Initialize RTD probe"""
        self.send_command(str(address))
        status = {}
        
        # Check calibration
        response = self.send_command("Cal,?")
        status['calibration'] = response if response else "Unknown"
        
        return status

    def send_command(self, cmd, wait_time=0.3):
        """Send command to device"""
        if not self.serial_conn:
            return None
        try:
            self.serial_conn.write(f"{cmd}\r".encode())
            time.sleep(wait_time)
            if self.serial_conn.in_waiting:
                return self.serial_conn.readline().decode().strip()
            return None
        except Exception as e:
            st.error(f"Command error: {str(e)}")
            return None

    def save_device_status(self, devices):
        """Save device status to config"""
        config = {
            'devices': {},
            'setup_date': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        for device in devices:
            status = self.initialize_device(device)
            config['devices'][device['type']] = {
                'address': device['address'],
                'info': device['info'],
                'status': status
            }
        
        Path('config').mkdir(exist_ok=True)
        with open('config/devices.yaml', 'w') as f:
            yaml.dump(config, f)
        
        return config
