# Plot the four (two analog, two digital) traces
# output by the c-demo code. For configuring DPP settings.

import numpy as np
import matplotlib.pyplot as plt

fn_map = {
    'Input': 'Waveform_0_0_1.txt',
    'TrapezoidReduced': 'Waveform_0_0_2.txt',
    'Peaking': 'DWaveform_0_0_1.txt',
    'Trigger': 'DWaveform_0_0_2.txt',
}

arr_map = {}
fig = plt.figure()
for key, val in fn_map.items():
    with open(val) as f:
        arr_map[key] = np.array([int(v) for v in f.readlines()])
    plt.plot(arr_map[key], label=key)
plt.legend(loc='best')
plt.show()
