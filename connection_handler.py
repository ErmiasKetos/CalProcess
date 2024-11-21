import streamlit as st
import serial
import platform
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionHandler:
    def __init__(self):
        self.active_probes = {
            'pH': False,
            'EC': False,
            'DO': False,
            'RTD': False
        }

    def check_port(self, port):
        """Test if a port is available and responsive"""
        try:
            ser = serial.Serial(port, 9600, timeout=1)
            time.sleep(0.2)
            
            # Try to get device info
            ser.write(b"i\r")
            time.sleep(0.2)
            
            if ser.in_waiting:
                response = ser.readline().decode().strip()
                description = f"Active device (Response: {response})"
            else:
                description = "Port available (No response)"
                
            ser.close()
            return {
                "port": port,
                "description": description,
                "status": "active" if 'response' in locals() else "available"
            }
        except Exception as e:
            logger.debug(f"Port {port} check failed: {str(e)}")
            return None

    def scan_ports(self):
    """Scan all potential ports in parallel"""
    potential_ports = self.get_potential_ports()
    available_ports = []
    
    if not potential_ports:
        return []
        
    progress_text = "Scanning ports..."
    progress_bar = st.sidebar.progress(0)
    
    # Ensure at least 1 worker, maximum 4 workers
    max_workers = min(max(1, len(potential_ports)), 4)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(self.check_port, port): port 
                  for port in potential_ports}
        
        for i, future in enumerate(as_completed(futures)):
            progress = (i + 1) / len(potential_ports)
            progress_bar.progress(progress)
            
            result = future.result()
            if result:
                available_ports.append(result)
    
    progress_bar.empty()
    return available_ports

    def scan_ports(self):
        """Scan all potential ports in parallel"""
        potential_ports = self.get_potential_ports()
        available_ports = []
        
        progress_text = "Scanning ports..."
        progress_bar = st.sidebar.progress(0)
        
        with ThreadPoolExecutor(max_workers=min(len(potential_ports), 10)) as executor:
            futures = {executor.submit(self.check_port, port): port 
                      for port in potential_ports}
            
            for i, future in enumerate(as_completed(futures)):
                progress = (i + 1) / len(potential_ports)
                progress_bar.progress(progress)
                
                result = future.result()
                if result:
                    available_ports.append(result)
        
        progress_bar.empty()
        return available_ports

    def connect_to_port(self, port):
        """Establish connection to selected port"""
        try:
            ser = serial.Serial(
                port=port,
                baudrate=9600,
                timeout=1,
                write_timeout=1
            )
            
            # Wait for Arduino to reset
            time.sleep(2)
            
            # Test communication
            ser.write(b"i\r")
            time.sleep(0.5)
            
            if ser.in_waiting:
                response = ser.readline().decode().strip()
                logger.info(f"Connected to {port}: {response}")
                return ser
            else:
                ser.close()
                return None
                
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            return None

    def send_command(self, ser, command):
        """Send command to device and get response"""
        if not ser or not ser.is_open:
            return None
            
        try:
            ser.reset_input_buffer()
            ser.write(f"{command}\r".encode())
            time.sleep(0.5)
            
            response = []
            while ser.in_waiting:
                line = ser.readline().decode().strip()
                response.append(line)
                
            return response[0] if response else None
            
        except Exception as e:
            logger.error(f"Command failed: {str(e)}")
            return None

    def probe_reading(self, ser, probe_type):
        """Get current reading from specified probe"""
        try:
            response = self.send_command(ser, "R")
            if response and response.replace('.','').isdigit():
                return float(response)
        except:
            pass
        return 0.000

    def calibrate_probe(self, ser, probe_type, point, value):
        """Calibrate specified probe"""
        command = f"cal,{point},{value}"
        response = self.send_command(ser, command)
        return response if response else "Calibration failed"

    def detect_probes(self, ser):
        """Detect which probes are connected"""
        for probe in self.active_probes:
            response = self.send_command(ser, f"PROBE,{probe}")
            self.active_probes[probe] = bool(response and "OK" in response)
