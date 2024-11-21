import streamlit as st
import serial
import platform
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from glob import glob
import sys

logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG for more info
logger = logging.getLogger(__name__)

class ConnectionHandler:
    def __init__(self):
        self.active_probes = {
            'pH': False,
            'EC': False,
            'DO': False,
            'RTD': False
        }

    def get_potential_ports(self):
        """Get list of potential ports based on operating system"""
        system = platform.system()
        st.sidebar.write(f"Detected Operating System: {system}")
        
        ports = []
        if system == "Windows":
            # Check both COM ports and USB devices
            for i in range(1, 21):
                ports.append(f"COM{i}")
            
            # Add additional Windows-specific USB device patterns
            try:
                from serial.tools import list_ports
                for port in list_ports.comports():
                    if port.device not in ports:
                        ports.append(port.device)
                        st.sidebar.write(f"Found port: {port.device} - {port.description}")
            except Exception as e:
                st.sidebar.warning(f"Error scanning Windows ports: {str(e)}")
                
        elif system == "Linux":
            try:
                # Common Linux port patterns
                patterns = [
                    "/dev/ttyUSB*",
                    "/dev/ttyACM*",
                    "/dev/ttyS*",
                    "/dev/ttyXRUSB*",
                    "/dev/serial/by-id/*"
                ]
                for pattern in patterns:
                    matching_ports = glob(pattern)
                    ports.extend(matching_ports)
                    if matching_ports:
                        st.sidebar.write(f"Found ports matching {pattern}: {matching_ports}")
            except Exception as e:
                st.sidebar.warning(f"Error scanning Linux ports: {str(e)}")
                
        elif system == "Darwin":  # macOS
            try:
                patterns = [
                    "/dev/tty.usbserial*",
                    "/dev/tty.usbmodem*",
                    "/dev/cu.usbserial*",
                    "/dev/cu.usbmodem*",
                    "/dev/tty.SLAB_USBtoUART*"
                ]
                for pattern in patterns:
                    matching_ports = glob(pattern)
                    ports.extend(matching_ports)
                    if matching_ports:
                        st.sidebar.write(f"Found ports matching {pattern}: {matching_ports}")
            except Exception as e:
                st.sidebar.warning(f"Error scanning macOS ports: {str(e)}")
        
        # Debug output
        if ports:
            st.sidebar.write("Available ports:", ports)
        else:
            st.sidebar.warning("No ports found automatically")
            
        return list(set(ports))  # Remove duplicates

    def verify_port_exists(self, port):
        """Verify if a port exists in the system"""
        try:
            if platform.system() == "Windows":
                # For Windows, try to open the port directly
                try:
                    ser = serial.Serial(port, 9600, timeout=1)
                    ser.close()
                    return True
                except:
                    return False
            else:
                # For Unix-like systems, check if the device file exists
                import os
                return os.path.exists(port)
        except Exception as e:
            st.sidebar.error(f"Error verifying port {port}: {str(e)}")
            return False

    def connect_to_port(self, port):
        """Establish connection to selected port with enhanced error handling"""
        try:
            # First verify port exists
            if not self.verify_port_exists(port):
                st.sidebar.error(f"Port {port} does not exist in the system")
                return None

            st.sidebar.info(f"Attempting to connect to {port}...")
            
            # Try to connect
            ser = serial.Serial(
                port=port,
                baudrate=9600,
                timeout=1,
                write_timeout=1
            )
            
            # Wait for Arduino to reset
            time.sleep(2)
            st.sidebar.info("Port opened, testing communication...")
            
            # Clear any pending data
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            # Test communication
            ser.write(b"i\r")
            time.sleep(0.5)
            
            if ser.in_waiting:
                response = ser.readline().decode().strip()
                st.sidebar.success(f"Device responded: {response}")
                return ser
            else:
                ser.close()
                st.sidebar.error("No response from device")
                return None
                
        except serial.SerialException as e:
            st.sidebar.error(f"Serial connection error: {str(e)}")
            if "Permission denied" in str(e):
                st.sidebar.error("Permission denied. On Linux/Mac, try: sudo chmod 666 " + port)
            elif "already in use" in str(e):
                st.sidebar.error("Port is already in use by another program")
            return None
        except Exception as e:
            st.sidebar.error(f"Unexpected error: {str(e)}")
            return None

    def scan_ports(self):
        """Scan all potential ports in parallel with better feedback"""
        potential_ports = self.get_potential_ports()
        available_ports = []
        
        if not potential_ports:
            st.sidebar.warning("No potential ports found to scan")
            return []
            
        st.sidebar.info(f"Scanning {len(potential_ports)} potential ports...")
        progress_bar = st.sidebar.progress(0)
        
        # Ensure at least 1 worker, maximum 4 workers
        max_workers = min(max(1, len(potential_ports)), 4)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.check_port, port): port 
                      for port in potential_ports}
            
            for i, future in enumerate(as_completed(futures)):
                progress = (i + 1) / len(potential_ports)
                progress_bar.progress(progress)
                
                port = futures[future]
                try:
                    result = future.result()
                    if result:
                        available_ports.append(result)
                        st.sidebar.success(f"Found active port: {port}")
                except Exception as e:
                    st.sidebar.error(f"Error scanning {port}: {str(e)}")
        
        progress_bar.empty()
        return available_ports

    # ... rest of the ConnectionHandler class methods remain the same ...

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
