import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# === CONSTANTS ===
num_thcoup = 10
delt_t = 0.5 * num_thcoup
sample_rate = 1000 * delt_t  # milliseconds
sample_length = 30 * 60  # seconds
num_samples = round(sample_length / delt_t)

save_length = 10
time = np.linspace(0, sample_length - delt_t, num_samples)

# === LABELS ===
labels = [
    "T (V: 1-2)", "Manipulator (V: 1-2)", "Top Sphere (V: 3-4)", "Window L (V: 3-4)",
    "Window M (V: 5-6)", "Bottom Sphere (V: 5-6)", "Back Sphere (V: 5-6)",
    "Window S (V: 3-4)", "Reducer (V: 7)", "Window LL (V: 7)"
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
    with open("temperatures.txt", "r") as file:
        lines = file.readlines()
except FileNotFoundError:
    raise RuntimeError("temperatures.txt not found.")

if len(lines) < 2:
    raise RuntimeError("File must contain at least two data lines for rate-of-change calculation.")

# Parse temperature values
temp_array = np.array([ln.strip().split(',')[1:-1] for ln in lines], dtype=np.float64).T
if temp_array.shape[1] > num_samples:
    temp_array = temp_array[:, -num_samples:]

# Parse timestamp and temp to compute change (°C/min)
ts_temp = np.array([ln.strip().split(',')[:-1] for ln in lines], dtype=np.float64).T
timestamps = ts_temp[0]
temps = ts_temp[1:]
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

# === SETUP LINES ===
temp_lines = [ax[0].plot([], [], '.-', markersize=0.5, label=f"{i+1} {labels[i]}")[0] for i in range(num_thcoup)]
change_lines = [ax[1].plot([], [], '.-', markersize=0.5, label=f"{i+1} {labels[i]}")[0] for i in range(num_thcoup)]

# === ANIMATION FUNCTIONS ===
def animate_temp(frame, idx):
    try:
        with open("temperatures.txt", "r") as file:
            last_line = file.readlines()[-1]
        val = float(last_line.strip().split(',')[1 + idx])
    except Exception:
        val = 0.0

    lst = temp_data_list[idx]
    lst.append(val)
    if len(lst) > num_samples:
        lst.pop(0)

    temp_lines[idx].set_data(time, lst)
    return [temp_lines[idx]]

def animate_change(frame, idx):
    try:
        with open("temperatures.txt", "r") as file:
            lns = file.readlines()
        if len(lns) < 2:
            raise ValueError
        recent = [np.array(ln.strip().split(','), dtype=np.float64) for ln in lns[-2:]]
        t0, v0 = recent[0][0], recent[0][1 + idx]
        t1, v1 = recent[1][0], recent[1][1 + idx]
        dt = t1 - t0
        val = (v1 - v0) / dt * 60 if dt != 0 else 0.0
    except Exception:
        val = 0.0

    past = past_values[idx]
    past.append(val)
    if len(past) > save_length:
        past.pop(0)
    mean_val = np.mean(past)

    cd = change_data_list[idx]
    md = change_mean_list[idx]
    cd.append(val); md.append(mean_val)
    if len(cd) > num_samples:
        cd.pop(0)
    if len(md) > num_samples:
        md.pop(0)

    change_lines[idx].set_data(time, md)
    return [change_lines[idx]]

# === CREATE ANIMATIONS ===
temp_ani = [
    FuncAnimation(fig, animate_temp, fargs=(i,), interval=sample_rate, blit=True, cache_frame_data=False)
    for i in range(num_thcoup)
]
change_ani = [
    FuncAnimation(fig, animate_change, fargs=(i,), interval=sample_rate, blit=True, cache_frame_data=False)
    for i in range(num_thcoup)
]

# === FINAL LAYOUT ===
ax[0].set_xlim(0, sample_length - delt_t)
ax[0].set_ylim(20, 200)
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
