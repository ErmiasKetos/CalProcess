import serial
import time
import streamlit as st

class ProtocolManager:
    def __init__(self, serial_conn=None):
        self.serial_conn = serial_conn
        self.default_addresses = {
            'DO': 97,
            'ORP': 98,
            'pH': 99,
            'EC': 100,
            'RTD': 102,
            'PMP': 103,
            'CO2': 105,
            'PRS': 106,
            'O2': 108,
            'HUM': 111,
            'RGB': 112
        }
        self.baud_rates = [300, 1200, 2400, 9600, 19200, 38400, 57600, 115200]

    def check_protocol(self, device_address):
        """Check current protocol mode of device"""
        if not self.serial_conn:
            return None
            
        try:
            # Select device
            self.send_command(str(device_address))
            time.sleep(0.3)
            
            # Query protocol
            response = self.send_command("Protocol,?")
            return response.strip() if response else None
        except Exception as e:
            st.error(f"Error checking protocol: {str(e)}")
            return None

    def switch_to_i2c(self, device_address, new_i2c_address):
        """
        Switch device to I2C mode
        Command: i2c,<new address>
        Example: i2c,100
        """
        if not self.serial_conn:
            return False
            
        try:
            # Validate I2C address
            if not 1 <= new_i2c_address <= 127:
                st.error("I2C address must be between 1 and 127")
                return False
                
            # Check if address is already in use
            if self.is_address_in_use(new_i2c_address):
                st.error("This I2C address is already in use")
                return False
                
            # Send command to switch to I2C
            command = f"i2c,{new_i2c_address}"
            response = self.send_command(command)
            
            if response and "SUCCESS" in response:
                st.success(f"Successfully switched to I2C (Address: {new_i2c_address})")
                return True
            else:
                st.error("Failed to switch to I2C mode")
                return False
                
        except Exception as e:
            st.error(f"Error switching to I2C: {str(e)}")
            return False

    def switch_to_uart(self, device_address, baud_rate=9600):
        """
        Switch device to UART mode
        Command: baud,<baud rate>
        Example: baud,9600
        """
        if not self.serial_conn:
            return False
            
        try:
            # Validate baud rate
            if baud_rate not in self.baud_rates:
                st.error("Invalid baud rate")
                return False
                
            # Send command to switch to UART
            command = f"baud,{baud_rate}"
            response = self.send_command(command)
            
            if response and "SUCCESS" in response:
                st.success(f"Successfully switched to UART (Baud: {baud_rate})")
                st.warning("""
                    Warning: Device will no longer be accessible via I2C!
                    You will need to use another method to switch back to I2C.
                """)
                return True
            else:
                st.error("Failed to switch to UART mode")
                return False
                
        except Exception as e:
            st.error(f"Error switching to UART: {str(e)}")
            return False

    def send_command(self, command):
        """Send command to device"""
        if not self.serial_conn:
            return None
            
        try:
            # Add carriage return to command
            command = f"{command}\r"
            self.serial_conn.write(command.encode())
            time.sleep(0.3)  # Wait for processing
            
            # Read response
            if self.serial_conn.in_waiting:
                response = self.serial_conn.readline().decode().strip()
                return response
            return None
        except Exception as e:
            st.error(f"Command error: {str(e)}")
            return None

    def is_address_in_use(self, address):
        """Check if I2C address is already in use"""
        try:
            # Send scan command
            self.send_command("!scan")
            time.sleep(0.3)
            
            # Read response
            response = self.serial_conn.read(self.serial_conn.in_waiting).decode()
            
            # Check if address appears in response
            return str(address) in response
        except Exception:
            return False

    def verify_protocol_switch(self, device_address, expected_protocol):
        """Verify protocol switch was successful"""
        try:
            current_protocol = self.check_protocol(device_address)
            return current_protocol == expected_protocol
        except Exception:
            return False

    def get_available_addresses(self):
        """Get list of available I2C addresses"""
        used_addresses = []
        try:
            # Send scan command
            self.send_command("!scan")
            time.sleep(0.3)
            
            # Read response
            response = self.serial_conn.read(self.serial_conn.in_waiting).decode()
            
            # Parse response for addresses
            for line in response.split('\n'):
                if ':' in line:
                    addr = int(line.split(':')[0].strip())
                    used_addresses.append(addr)
                    
            # Return list of unused addresses
            return [addr for addr in range(1, 128) 
                   if addr not in used_addresses]
        except Exception:
            return list(range(1, 128))

    def suggest_address(self, device_type):
        """Suggest an available I2C address for a device type"""
        try:
            available = self.get_available_addresses()
            default = self.default_addresses.get(device_type)
            
            # Try default address first
            if default in available:
                return default
                
            # Otherwise return first available address
            return available[0] if available else None
        except Exception:
            return None
