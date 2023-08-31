import sys
import matplotlib.pyplot as plt
import numpy as np

for arg in sys.argv[1:]:
    with open(arg) as f:
        _ = np.array([float(l.strip()) for l in f.readlines()])
    print(np.sum(_))
    plt.plot(_)
plt.show()
