import serial
import serial.tools.list_ports
import time
import yaml
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging

class SerialManager:
    def __init__(self, config_path="config.yaml"):
        self.config = self.load_config(config_path)
        self.connection = None
        self.setup_logging()
        
    def load_config(self, config_path):
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/serial.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('SerialManager')
    
    def list_ports(self):
        """List available serial ports"""
        return [port.device for port in serial.tools.list_ports.comports()]
    
    def connect(self, port):
        """Connect to specified serial port"""
        try:
            self.connection = serial.Serial(
                port=port,
                baudrate=self.config['serial']['baudrate'],
                timeout=self.config['serial']['timeout']
            )
            self.logger.info(f"Connected to {port}")
            return True
        except Exception as e:
            self.logger.error(f"Connection error: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from serial port"""
        if self.connection and self.connection.is_open:
            self.connection.close()
            self.logger.info("Disconnected from serial port")
    
    def send_command(self, command):
        """Send command and get response"""
        if not self.connection or not self.connection.is_open:
            self.logger.error("Not connected to device")
            return None
        
        try:
            self.connection.write(f"{command}\r".encode())
            time.sleep(0.3)  # Wait for processing
            
            if self.connection.in_waiting:
                response = self.connection.readline().decode().strip()
                self.logger.debug(f"Command: {command}, Response: {response}")
                return response
            return None
        except Exception as e:
            self.logger.error(f"Command error: {str(e)}")
            return None

class DataLogger:
    def __init__(self, config_path="config.yaml"):
        self.config = self.load_config(config_path)
        self.setup_data_directory()
        
    def load_config(self, config_path):
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def setup_data_directory(self):
        """Create data directory if it doesn't exist"""
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
    
    def log_reading(self, device_type, reading, temperature=None):
        """Log a sensor reading"""
        log_file = Path(self.config['logging']['readings_file'])
        
        data = {
            'timestamp': datetime.now(),
            'device_type': device_type,
            'reading': reading,
            'temperature': temperature
        }
        
        df = pd.DataFrame([data])
        df.to_csv(log_file, mode='a', header=not log_file.exists(), index=False)
    
    def log_calibration(self, device_type, point, command, response):
        """Log a calibration event"""
        log_file = Path(self.config['logging']['calibration_file'])
        
        data = {
            'timestamp': datetime.now(),
            'device_type': device_type,
            'calibration_point': point,
            'command': command,
            'response': response
        }
        
        df = pd.DataFrame([data])
        df.to_csv(log_file, mode='a', header=not log_file.exists(), index=False)
    
    def get_readings_history(self, device_type=None, start_date=None, end_date=None):
        """Get historical readings with optional filtering"""
        try:
            df = pd.read_csv(self.config['logging']['readings_file'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            if device_type:
                df = df[df['device_type'] == device_type]
            if start_date:
                df = df[df['timestamp'] >= start_date]
            if end_date:
                df = df[df['timestamp'] <= end_date]
                
            return df.sort_values('timestamp', ascending=False)
        except FileNotFoundError:
            return pd.DataFrame()
    
    def get_calibration_history(self, device_type=None, start_date=None, end_date=None):
        """Get calibration history with optional filtering"""
        try:
            df = pd.read_csv(self.config['logging']['calibration_file'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            if device_type:
                df = df[df['device_type'] == device_type]
            if start_date:
                df = df[df['timestamp'] >= start_date]
            if end_date:
                df = df[df['timestamp'] <= end_date]
                
            return df.sort_values('timestamp', ascending=False)
        except FileNotFoundError:
            return pd.DataFrame()

class DeviceManager:
    def __init__(self, serial_manager, config_path="config.yaml"):
        self.serial = serial_manager
        self.config = self.load_config(config_path)
        self.current_device = None
        
    def load_config(self, config_path):
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def scan_devices(self):
        """Scan for connected EZO devices"""
        response = self.serial.send_command("!scan")
        devices = []
        if response:
            lines = response.split('\n')
            for line in lines:
                if ':' in line:
                    addr, device_info = line.split(':', 1)
                    addr = int(addr.strip())
                    device_type = device_info.strip().split()[1]
                    devices.append({
                        'address': addr,
                        'type': device_type,
                        'info': device_info.strip()
                    })
        return devices
    
    def select_device(self, address):
        """Select device by address"""
        return self.serial.send_command(str(address))
    
    def get_device_config(self, device_type):
        """Get device configuration"""
        return self.config['devices'].get(device_type.lower())
    
    def get_command(self, device_type, command_name, **kwargs):
        """Get formatted command for device"""
        device_config = self.get_device_config(device_type)
        if device_config and command_name in device_config['commands']:
            command = device_config['commands'][command_name]
            return command.format(**kwargs) if kwargs else command
        return None
