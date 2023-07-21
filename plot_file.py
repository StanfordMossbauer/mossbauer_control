import sys
import matplotlib.pyplot as plt
import numpy as np


for fname in sys.argv[1:]:
    with open(fname) as f:
        _ = np.array([int(float(l.strip())) for l in f.readlines()])
    print(np.sum(_))
    plt.plot(_)
plt.show()
