import numpy as np
import pyvisa as pyvisa
import time as time
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
temp_file_path = os.path.join(script_dir, "temperatures.txt")

rm = pyvisa.ResourceManager()
instr = rm.open_resource("GPIB0::19::INSTR")

# Define the number of temperature channels we want to log consistently
num_channels = 10

# Define which instrument channels to read for each temperature sensor
# Based on your testing: Channel 1=167°C, Channel 2=161°C, Channel 3=250°C
# Display order: 167, 161, 248, 168, 227, 128, 113, 199, 203, 37
# So we need: [1, 2, 3, ?, ?, ?, ?, ?, ?, ?] - test more channels to complete mapping
CHANNEL_MAP = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # Start with 1-10, adjust based on testing

while True:
	try:
		# Build complete line before writing (atomic operation)
		line_data = [str(time.time())]
		
		# Always collect exactly num_channels values
		for i in range(num_channels):
			try:
				channel_num = CHANNEL_MAP[i]
				meas = instr.query(f"MEAS? {channel_num}").strip()
				temp_val = float(meas)
				# Use value if reasonable, otherwise use 0.0
				if temp_val < 10000 and temp_val > -100:
					line_data.append(str(temp_val))
				else:
					line_data.append("0.0")
			except (ValueError, Exception):
				# If measurement fails, use 0.0 to maintain consistency
				line_data.append("0.0")
		
		# Write complete line atomically
		complete_line = ",".join(line_data) + "\n"
		print(complete_line.strip())  # Print to console for monitoring
		with open(temp_file_path, "a") as f:
			f.write(complete_line)
			f.flush()  # Ensure data is written immediately
		
		# Add a small delay to prevent overwhelming the instrument
		time.sleep(0.1)
		
	except Exception as e:
		print(f"Error in logging: {e}")
		time.sleep(1)  # Wait before retrying




