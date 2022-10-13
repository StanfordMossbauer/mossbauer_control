import sys
import matplotlib.pyplot as plt

with open(sys.argv[1]) as f:
    _ = [int(l) for l in f.readlines()]
plt.plot(_)
plt.show()
