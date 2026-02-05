"""
Amptek PX5/DP5 Digital Pulse Processor Interface

This module provides a simplified interface for controlling Amptek PX5/DP5 devices
for basic spectrum acquisition and auxiliary output control.

Author: Generated for mossbauer_control
"""

import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from .base import MossbauerInstrument

try:
    import sys
    import os
    # Add the amptek module to the path
    amptek_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'amptek', 'python')
    if amptek_path not in sys.path:
        sys.path.append(amptek_path)
    
    import amptek_hardware_interface as ahi
    AMPTEK_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Amptek hardware interface not available: {e}")
    AMPTEK_AVAILABLE = False


class Amptek(MossbauerInstrument):
    """
    Simplified interface for Amptek PX5/DP5 Digital Pulse Processors
    
    Provides basic control functions:
    - Connection management (USB/Ethernet/Simulator)
    - Measurement control (start/stop/clear)
    - Auxiliary output configuration
    - Data acquisition
    """
    
    def __init__(self, connection_type='usb', **kwargs):
        """
        Initialize Amptek interface
        
        Args:
            connection_type (str): 'usb', 'ethernet', or 'simulator'
            **kwargs: Connection-specific parameters
                For USB: serial_number (int, optional, -1 for first device)
                For Ethernet: hostname (str), port (int), timeout (float)
        """
        super().__init__()
        
        if not AMPTEK_AVAILABLE:
            raise ImportError("Amptek hardware interface not available. Please install the amptek module.")
        
        self.amptek = ahi.AmptekHardwareInterface()
        self.connection_type = connection_type
        self.connection_params = kwargs
        self.connected = False
        self.measuring = False
        
        # Default configuration
        self.default_config = {
            'RESC': '1',      # Reset
            'CLCK': '20',     # Clock frequency (MHz)
            'TPEA': '6.4',    # Peaking time (μs)
            'GAIF': '1',      # Gain fine adjustment
            'GAIN': '5',      # Coarse gain
            'RESL': '0',      # Resolution enhancement
            'TFLA': '0.8',    # Flat top (μs)
            'TPFA': '1.0',    # Fast channel peaking time (μs)
            'PURE': '1',      # Pileup rejection enable
            'RTDE': '1',      # RTD enable
            'MCAS': '8192',   # MCA size
            'MCAC': '1024',   # MCA channels
            'SOFF': '0',      # Spectrum offset
            'AINP': '1',      # Analog input positive
            'INOF': '0',      # Input offset
            'GAIA': '1',      # Gain adjustment
        }
        
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """
        Connect to the Amptek device
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.connection_type.lower() == 'usb':
                serial_number = self.connection_params.get('serial_number', -1)
                self.amptek.connectUSB(serial_number)
                self.logger.info(f"Connected to Amptek via USB (serial: {serial_number})")
                
            elif self.connection_type.lower() == 'ethernet':
                hostname = self.connection_params.get('hostname', 'localhost')
                port = self.connection_params.get('port', 4001)
                timeout = self.connection_params.get('timeout', 1.0)
                self.amptek.connectUDP(hostname, port, timeout)
                self.logger.info(f"Connected to Amptek via Ethernet ({hostname}:{port})")
                
            elif self.connection_type.lower() == 'simulator':
                self.amptek.connectSimulator()
                self.logger.info("Connected to Amptek simulator")
                
            else:
                raise ValueError(f"Unknown connection type: {self.connection_type}")
            
            # Test connection with ping
            if self.amptek.Ping():
                self.connected = True
                self.logger.info("Amptek connection verified with ping")
                return True
            else:
                self.logger.error("Amptek ping failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Amptek: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the device"""
        if self.measuring:
            self.stop_measurement()
        self.connected = False
        self.logger.info("Disconnected from Amptek")
    
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self.connected and self.amptek.Ping()
    
    def configure_device(self, config: Optional[Dict[str, str]] = None):
        """
        Configure device parameters
        
        Args:
            config (dict, optional): Configuration parameters. Uses defaults if None.
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        
        config_to_use = self.default_config.copy()
        if config:
            config_to_use.update(config)
        
        # Convert config dict to list of "PARAM=VALUE" strings
        config_commands = [f"{param}={value}" for param, value in config_to_use.items()]
        
        success = self.amptek.SetTextConfiguration(config_commands)
        if success:
            self.logger.info("Device configuration updated")
        else:
            self.logger.error("Failed to update device configuration")
        
        return success
    
    def start_measurement(self, preset_time: Optional[float] = None, 
                         preset_counts: Optional[int] = None) -> bool:
        """
        Start spectrum acquisition
        
        Args:
            preset_time (float, optional): Acquisition time in seconds
            preset_counts (int, optional): Target count number
            
        Returns:
            bool: True if started successfully
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        
        if self.measuring:
            self.logger.warning("Measurement already in progress")
            return True
        
        # Clear previous spectrum
        self.amptek.ClearSpectrum()
        
        # Set preset parameters
        if preset_time is not None:
            self.amptek.SetPresetAccumulationTime(preset_time)
            self.logger.info(f"Set preset time: {preset_time} seconds")
        
        if preset_counts is not None:
            self.amptek.SetPresetCounts(preset_counts)
            self.logger.info(f"Set preset counts: {preset_counts}")
        
        # Start acquisition
        success = self.amptek.Enable()
        if success:
            self.measuring = True
            self.logger.info("Measurement started")
        else:
            self.logger.error("Failed to start measurement")
        
        return success
    
    def stop_measurement(self) -> bool:
        """
        Stop current measurement
        
        Returns:
            bool: True if stopped successfully
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        
        success = self.amptek.Disable()
        if success:
            self.measuring = False
            self.logger.info("Measurement stopped")
        else:
            self.logger.error("Failed to stop measurement")
        
        return success
    
    def is_measuring(self) -> bool:
        """Check if device is currently measuring"""
        if not self.connected:
            return False
        
        try:
            status = self.amptek.updateStatus()
            return status.IsEnabled()
        except:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current device status
        
        Returns:
            dict: Status information including counts, timing, temperatures, etc.
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        
        status = self.amptek.updateStatus()
        
        return {
            'enabled': status.IsEnabled(),
            'fast_count': status.FastCount(),
            'slow_count': status.SlowCount(),
            'gp_count': status.GpCount(),
            'dead_time': status.DeadTime(),
            'accumulation_time': status.AccTime(),
            'real_time': status.RealTime(),
            'high_voltage': status.HighVoltage(),
            'detector_temp': status.DetectorTemp(),
            'board_temp': status.BoardTemp(),
            'preset_time_reached': status.IsPresetTimeReached(),
            'preset_count_reached': status.IsPresetCountReached(),
            'gated': status.IsGated(),
            'firmware_version': f"{status.FirmwareMajor()}.{status.FirmwareMinor()}.{status.FirmwareBuild()}",
            'fpga_version': f"{status.FpgaMajor()}.{status.FpgaMinor()}",
            'serial_number': status.SerialNb(),
            'device_type': status.DeviceType(),
        }
    
    def get_data(self) -> List[int]:
        """
        Get current spectrum data
        
        Returns:
            list: Spectrum data as list of counts per channel
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        
        spectrum = self.amptek.GetSpectrum()
        return spectrum
    
    def clear_spectrum(self) -> bool:
        """
        Clear current spectrum data
        
        Returns:
            bool: True if cleared successfully
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        
        success = self.amptek.ClearSpectrum()
        if success:
            self.logger.info("Spectrum cleared")
        else:
            self.logger.error("Failed to clear spectrum")
        
        return success
    
    def set_aux_output(self, n_aux: int, ch_start: int, ch_stop: int, 
                      pulse_width: float = 1.0, output_type: str = 'SCA') -> bool:
        """
        Configure auxiliary output for Single Channel Analyzer (SCA)
        
        Args:
            n_aux (int): Auxiliary output number (1 or 2)
            ch_start (int): Start channel for SCA window
            ch_stop (int): Stop channel for SCA window  
            pulse_width (float): Pulse width in microseconds (default: 1.0)
            output_type (str): Output type ('SCA', 'ICR', 'OCR', etc.)
            
        Returns:
            bool: True if configured successfully
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        
        if n_aux not in [1, 2]:
            raise ValueError("n_aux must be 1 or 2")
        
        # Configuration commands for auxiliary output
        config_commands = []
        
        # Set SCA window
        if n_aux == 1:
            config_commands.extend([
                f"SCAH={ch_stop}",    # SCA upper level for AUX1
                f"SCAL={ch_start}",   # SCA lower level for AUX1  
                f"AUO1={output_type}", # AUX1 output type
                f"PULS=1",            # Enable pulse output
            ])
        else:  # n_aux == 2
            config_commands.extend([
                f"SCAH={ch_stop}",    # SCA upper level for AUX2
                f"SCAL={ch_start}",   # SCA lower level for AUX2
                f"AUO2={output_type}", # AUX2 output type  
                f"PULS=1",            # Enable pulse output
            ])
        
        # Set pulse width if supported
        config_commands.append(f"TPUL={pulse_width}")
        
        success = self.amptek.SetTextConfiguration(config_commands)
        
        if success:
            self.logger.info(f"AUX{n_aux} configured: channels {ch_start}-{ch_stop}, "
                           f"pulse_width={pulse_width}μs, type={output_type}")
        else:
            self.logger.error(f"Failed to configure AUX{n_aux}")
        
        return success
    
    def get_configuration(self, params: List[str]) -> Dict[str, str]:
        """
        Get current configuration parameters
        
        Args:
            params (list): List of parameter names to retrieve
            
        Returns:
            dict: Parameter names and their current values
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        
        config_list = self.amptek.GetTextConfiguration(params)
        
        # Parse "PARAM=VALUE" format into dictionary
        config_dict = {}
        for config_str in config_list:
            if '=' in config_str:
                param, value = config_str.split('=', 1)
                config_dict[param] = value
        
        return config_dict
    
    def wait_for_completion(self, check_interval: float = 1.0) -> Dict[str, Any]:
        """
        Wait for current measurement to complete
        
        Args:
            check_interval (float): Time between status checks in seconds
            
        Returns:
            dict: Final status when measurement completes
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        
        self.logger.info("Waiting for measurement completion...")
        
        while True:
            status = self.get_status()
            
            if not status['enabled']:
                self.measuring = False
                self.logger.info("Measurement completed")
                break
            
            # Log progress
            acc_time = status['accumulation_time']
            fast_counts = status['fast_count']
            slow_counts = status['slow_count']
            
            self.logger.debug(f"Progress: {acc_time:.1f}s, "
                            f"Fast: {fast_counts}, Slow: {slow_counts}")
            
            time.sleep(check_interval)
        
        return status
    
    def setup_mossbauer_scan(self):
        """Setup device for Mössbauer spectroscopy measurements"""
        mossbauer_config = {
            'CLCK': '20',     # 20 MHz clock
            'TPEA': '6.4',    # 6.4 μs peaking time
            'GAIN': '5',      # Medium gain
            'PURE': '1',      # Enable pileup rejection
            'MCAS': '8192',   # 8k channels
            'RTDE': '1',      # Enable RTD
        }
        
        return self.configure_device(mossbauer_config)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def __repr__(self):
        """String representation"""
        status = "connected" if self.connected else "disconnected"
        measuring = "measuring" if self.measuring else "idle"
        return f"Amptek({self.connection_type}, {status}, {measuring})"


# Example usage and testing
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    # Example: Connect and acquire a 10-second spectrum
    with Amptek('simulator') as amptek:
        if amptek.connect():
            # Configure for Mössbauer spectroscopy
            amptek.setup_mossbauer_scan()
            
            # Set up auxiliary output for channel 100-200
            amptek.set_aux_output(n_aux=1, ch_start=100, ch_stop=200, pulse_width=2.0)
            
            # Start 10-second measurement
            amptek.start_measurement(preset_time=10.0)
            
            # Wait for completion with progress updates
            final_status = amptek.wait_for_completion(check_interval=1.0)
            
            # Get the spectrum data
            spectrum = amptek.get_data()
            
            print(f"Measurement completed:")
            print(f"Total counts (fast): {final_status['fast_count']}")
            print(f"Total counts (slow): {final_status['slow_count']}")
            print(f"Accumulation time: {final_status['accumulation_time']:.2f} s")
            print(f"Dead time: {final_status['dead_time']:.2f} %")
            
            # Plot spectrum
            plt.figure(figsize=(10, 6))
            plt.plot(spectrum)
            plt.xlabel('Channel')
            plt.ylabel('Counts')
            plt.title('Amptek Spectrum')
            plt.grid(True)
            plt.show()