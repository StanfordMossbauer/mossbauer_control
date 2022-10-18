import sys
import matplotlib.pyplot as plt
import numpy as np

with open(sys.argv[1]) as f:
    _ = np.array([int(l) for l in f.readlines()])
print(np.sum(_))
plt.plot(_)
plt.show()
