import pyvisa as pyvisa
import time

# Quick diagnostic to see what's on each channel
rm = pyvisa.ResourceManager()
instr = rm.open_resource("GPIB0::19::INSTR")

print("Checking channels 1-16 to see what data is available:")
print("Channel | Value")
print("--------|--------")

try:
    for i in range(1, 17):  # Check channels 1-16
        try:
            meas = instr.query(f"MEAS? {i}").strip()
            value = float(meas)
            print(f"{i:7} | {value:8.2f}")
        except Exception as e:
            print(f"{i:7} | ERROR: {e}")
        
        time.sleep(0.1)  # Small delay between readings

except Exception as e:
    print(f"Connection error: {e}")

print("\nBased on the values above, identify which channels have your 10 temperature sensors.")
print("Then update the CHANNEL_MAP in log_temperatures.py accordingly.")