import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
temp_file_path = os.path.join(script_dir, "temperatures.txt")

# === CONSTANTS ===
num_thcoup = 10
delt_t = 0.5 * num_thcoup
sample_rate = 1000 * delt_t  # milliseconds
sample_length = 30 * 60  # seconds
num_samples = round(sample_length / delt_t)

save_length = 10
time = np.linspace(0, sample_length - delt_t, num_samples)

# === LABELS AND COLORS ===
labels = [
    "T (V: 1-2)", "Manipulator (V: 1-2)", "Top Sphere (V: 3-4)", "Window L (V: 3-4)",
    "Window M (V: 5-6)", "Bottom Sphere (V: 5-6)", "Back Sphere (V: 5-6)",
    "Window S (V: 3-4)", "Reducer (V: 7)", "Window LL (V: 7)"
]

# Define consistent colors for each sensor
colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
]

fig, ax = plt.subplots(2)

# === UTILITY TO ENSURE SAME LENGTH ===
def fixed_length_rows(array2d):
    """Convert each row in 2D array to a fixed-length list (num_samples),
    padding with zeros or trimming to match time axis."""
    fixed = []
    for row in array2d:
        row = list(row)
        if len(row) < num_samples:
            row = [0.0] * (num_samples - len(row)) + row
        elif len(row) > num_samples:
            row = row[-num_samples:]
        fixed.append(row)
    return fixed

# === INITIAL LOAD ===
try:
    with open(temp_file_path, "r") as file:
        lines = file.readlines()
except FileNotFoundError:
    # Create empty file with proper header if it doesn't exist
    print(f"Creating new temperatures.txt file at: {temp_file_path}")
    with open(temp_file_path, "w") as file:
        file.write("")
    lines = []

# Parse temperature values (skip corrupted lines)
parsed_lines = []

if lines:
    print(f"Processing {len(lines)} lines from temperature log...")
    
    # Only accept lines with exactly 11 columns (timestamp + 10 temps)
    for i, ln in enumerate(lines):
        line = ln.strip()
        if not line:  # Skip empty lines
            continue
            
        parts = [p.strip() for p in line.split(',') if p.strip()]
        
        # Only accept lines with exactly the expected format
        if len(parts) == 11:
            try:
                # Validate that first column is a timestamp and rest are numbers
                timestamp = float(parts[0])
                if timestamp > 1000000000:  # Valid unix timestamp
                    # Validate temperature values
                    valid_line = True
                    for j in range(1, 11):
                        try:
                            temp_val = float(parts[j])
                            if not (-100 <= temp_val <= 1000):  # Reasonable temperature range
                                valid_line = False
                                break
                        except ValueError:
                            valid_line = False
                            break
                    
                    if valid_line:
                        parsed_lines.append(parts)
            except ValueError:
                # Skip lines with invalid timestamps
                continue
    
    print(f"Found {len(parsed_lines)} valid temperature readings (skipped {len(lines) - len(parsed_lines)} corrupted lines)")

# If no valid data, create dummy data for initialization
if not parsed_lines:
    current_time = time.time()
    dummy_line = [str(current_time)] + ['20.0'] * num_thcoup
    parsed_lines = [dummy_line]

if len(parsed_lines) < 2:
    raise RuntimeError("Need at least two data points for rate calculation. File may be empty or corrupted.")

# Convert to numpy array
data_array = np.array(parsed_lines, dtype=np.float64).T
timestamps = data_array[0]
temp_array = data_array[1:]

if temp_array.shape[1] > num_samples:
    temp_array = temp_array[:, -num_samples:]
    timestamps = timestamps[-num_samples:]

# Compute change (°C/min)
temps = temp_array
d_ts = np.diff(timestamps)
d_temps = np.diff(temps, axis=1)
change_array = (d_temps / d_ts) * 60
if change_array.shape[1] > num_samples:
    change_array = change_array[:, -num_samples:]

# Moving average of changes
change_mean = np.zeros((num_thcoup, num_samples))
for i in range(num_samples):
    start = max(0, i - save_length + 1)
    window = change_array[:, start:i + 1] if i < change_array.shape[1] else change_array
    change_mean[:, i] = window.mean(axis=1)

# Fixed-length versions for animation
temp_data_list = fixed_length_rows(temp_array)
change_data_list = fixed_length_rows(change_array)
change_mean_list = fixed_length_rows(change_mean)
past_values = [[] for _ in range(num_thcoup)]

# === SETUP LINES WITH CONSISTENT COLORS ===
temp_lines = [ax[0].plot([], [], '.-', markersize=0.5, color=colors[i], label=f"{i+1} {labels[i]}")[0] for i in range(num_thcoup)]
change_lines = [ax[1].plot([], [], '.-', markersize=0.5, color=colors[i], label=f"{i+1} {labels[i]}")[0] for i in range(num_thcoup)]

# === ANIMATION FUNCTIONS ===
def animate_all(frame):
    """Single animation function that updates all lines consistently"""
    try:
        # Check if file exists, create if not
        try:
            with open(temp_file_path, "r") as file:
                lines = file.readlines()
        except FileNotFoundError:
            # File doesn't exist - just return without updating
            return temp_lines + change_lines
            
        if len(lines) < 1:
            return temp_lines + change_lines
        
        # Find the last complete line (skip partial writes and corrupted lines)
        last_line = None
        for line in reversed(lines):
            line = line.strip()
            if line:
                parts = [p.strip() for p in line.split(',') if p.strip()]
                # Only accept lines with exactly 11 columns and valid timestamp
                if len(parts) == 11:
                    try:
                        timestamp = float(parts[0])
                        if timestamp > 1000000000:  # Valid unix timestamp
                            last_line = line
                            break
                    except ValueError:
                        continue
        
        if not last_line:
            return temp_lines + change_lines
        
        # Parse current temperature values (only from valid lines)
        parts = [p.strip() for p in last_line.split(',') if p.strip()]
        
        # Extract temperature values (we know it's valid format)
        temp_values = []
        for idx in range(num_thcoup):
            try:
                val = float(parts[idx + 1])
                # Sanity check for reasonable temperature values
                if -100 <= val <= 1000:
                    temp_values.append(val)
                else:
                    temp_values.append(0.0)
            except (ValueError, IndexError):
                temp_values.append(0.0)
        
        # Update temperature data for all sensors consistently
        for idx in range(num_thcoup):
            lst = temp_data_list[idx]
            lst.append(temp_values[idx])
            if len(lst) > num_samples:
                lst.pop(0)
        
        # Update rate of change data if we have enough history
        if len(lines) >= 2:
            try:
                # Find the last two valid lines for rate calculation
                valid_lines = []
                for line in reversed(lines):
                    line = line.strip()
                    if line:
                        parts = [p.strip() for p in line.split(',') if p.strip()]
                        # Only accept lines with exactly 11 columns and valid timestamp
                        if len(parts) == 11:
                            try:
                                timestamp = float(parts[0])
                                if timestamp > 1000000000:  # Valid unix timestamp
                                    valid_lines.append(parts)
                                    if len(valid_lines) >= 2:
                                        break
                            except ValueError:
                                continue
                
                if len(valid_lines) >= 2:
                    # Reverse to get chronological order (oldest first)
                    valid_lines.reverse()
                    t0, t1 = float(valid_lines[0][0]), float(valid_lines[1][0])
                    dt = t1 - t0
                    
                    for idx in range(num_thcoup):
                        try:
                            v0 = float(valid_lines[0][1 + idx])
                            v1 = float(valid_lines[1][1 + idx])
                            rate_val = (v1 - v0) / dt * 60 if dt != 0 else 0.0
                        except (ValueError, IndexError):
                            rate_val = 0.0
                        
                        past = past_values[idx]
                        past.append(rate_val)
                        if len(past) > save_length:
                            past.pop(0)
                        mean_val = np.mean(past) if past else 0.0
                        
                        cd = change_data_list[idx]
                        md = change_mean_list[idx]
                        cd.append(rate_val)
                        md.append(mean_val)
                        if len(cd) > num_samples:
                            cd.pop(0)
                        if len(md) > num_samples:
                            md.pop(0)
            except Exception:
                pass  # Skip rate calculation if parsing fails
        
        # Update all plot lines with consistent time axis
        current_length = len(temp_data_list[0])  # All should have same length
        current_time = time[:current_length]
        
        for idx in range(num_thcoup):
            temp_lines[idx].set_data(current_time, temp_data_list[idx])
            if len(change_mean_list[idx]) > 0:
                change_length = len(change_mean_list[idx])
                change_time = time[:change_length]
                change_lines[idx].set_data(change_time, change_mean_list[idx])
        
    except Exception as e:
        print(f"Animation error: {e}")
        pass
    
    return temp_lines + change_lines

# === CREATE SINGLE ANIMATION ===
ani = FuncAnimation(fig, animate_all, interval=sample_rate, blit=True, cache_frame_data=False)

# === FINAL LAYOUT ===
ax[0].set_xlim(0, sample_length - delt_t)
ax[0].set_ylim(0, 300)
ax[0].set_title("Temperature in Time")
ax[0].set_xlabel("Time (s)")
ax[0].set_ylabel("Temperature (°C)")
ax[0].legend(loc="upper left")

ax[1].set_xlim(0, sample_length - delt_t)
ax[1].set_ylim(-10, 10)
ax[1].set_title("Mean Change in Temperature Over Time")
ax[1].set_xlabel("Time (s)")
ax[1].set_ylabel("Rate of Change (°C/min)")
ax[1].axhline(3, color='black', linestyle='--')
ax[1].axhline(-3, color='black', linestyle='--')
ax[1].legend(loc="upper left")

plt.tight_layout()
plt.show()
